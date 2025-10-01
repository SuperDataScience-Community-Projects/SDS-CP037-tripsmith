import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
from urllib.parse import urlencode
import re

from tavily import TavilyClient


GENERIC_KEYWORDS = [
    "best", "top", "guide", "things", "visit", "attractions",
    "all you must know", "the 10 best", "the best", "how to", "tips"
]
BLOCKED_SOURCES = [
    "reddit", "quora", "tripadvisor", "yelp", "forum", "forums", "community",
    "wikipedia.org", "wikivoyage.org", "blog", "list of"
]
ARTICLE_PATTERNS = [r"^list of ", r"^how to ", r"^why ", r"^what "]

PROPER_NOUN_RE = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b")


def is_generic_title(title: str) -> bool:
    t = title.lower()
    if any(k in t for k in GENERIC_KEYWORDS):
        return True
    if any(s in t for s in BLOCKED_SOURCES):
        return True
    if any(re.match(p, t) for p in ARTICLE_PATTERNS):
        return True
    return t.startswith("r/")


def normalize_title(title: str) -> str:
    cleaned = title.split("|")[0].split(" – ")[0].split(" - ")[0].strip()
    for ph in ["the 10 best", "best", "top", "guide:"]:
        if cleaned.lower().startswith(ph):
            cleaned = cleaned[len(ph):].strip(" :-—|•")
    return cleaned if cleaned else title


def actionize(name: str, fallback_category: str | None = None) -> str:
    # Convert generic/statement titles into imperative activity suggestions
    n = name.strip().rstrip(".,! ")
    # If contains a proper noun (probable place), keep it as is
    if PROPER_NOUN_RE.search(n):
        return n
    # If looks like a topic, make it actionable
    if fallback_category:
        return f"Explore {fallback_category.lower()} – {n}" if len(n) < 40 else f"Explore {fallback_category.lower()} in the area"
    return f"Explore: {n}" if len(n) < 40 else "Explore local highlights"


class PlannerAgentCentralized:
    def __init__(self, tavily_api_key: str | None = None):
        api_key = tavily_api_key or os.environ.get("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("Missing TAVILY_API_KEY. Please set it in your environment.")
        self.tavily = TavilyClient(api_key=api_key)

    def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        destination = request.get("destination", "")
        departure_date = request.get("departure_date", "")
        return_date = request.get("return_date", "")
        preferences = request.get("preferences", [])
        pref_hint = preferences[0] if preferences else None
        total_budget = float(request.get("budget", 0) or 0)
        hotel_budget = float(request.get("hotel_budget", 0) or 0)
        activity_budget = float(request.get("activity_budget", 0) or 0)

        if total_budget and not (hotel_budget or activity_budget):
            hotel_budget = round(total_budget * 0.6, 2)
            activity_budget = round(total_budget * 0.4, 2)

        hotel_names, hotel_reason = self._search_hotel_names(destination)
        poi_items, poi_reason = self._search_pois(destination, preferences, pref_hint)

        if not poi_items:
            poi_items = self._default_activities(destination)
            poi_reason += " | Used default activities due to low search signal."

        dep = datetime.strptime(departure_date, "%Y-%m-%d")
        ret = datetime.strptime(return_date, "%Y-%m-%d")
        num_days = max(1, (ret - dep).days + 1)

        daily_itinerary = self._build_daily_schedule(dep, num_days, poi_items)
        booking_site = self._booking_site_for_destination(destination)

        itinerary = {
            "hotels": hotel_names[:5],
            "booking_site": booking_site,
            "daily_itinerary": daily_itinerary,
            "budgets": {
                "total_budget": total_budget or None,
                "hotel_budget": hotel_budget or None,
                "activity_budget": activity_budget or None,
            }
        }
        reasoning = {
            "hotel_agent": hotel_reason,
            "poi_agent": poi_reason
        }
        return {"success": True, "data": itinerary, "reasoning": reasoning}

    def _search_hotel_names(self, destination: str) -> tuple[List[str], str]:
        query = f"best hotels in {destination} city center"
        try:
            res = self.tavily.search(query=query, search_depth="basic", max_results=30)
            names: List[str] = []
            for r in res.get("results", []):
                raw = (r.get("title") or "").strip()
                if not raw:
                    continue
                if is_generic_title(raw):
                    continue
                name = normalize_title(raw)
                if name and name not in names:
                    names.append(name)
            reason = f"Collected {len(names)} hotel name candidates via Tavily."
            return names, reason
        except Exception as e:
            return [], f"Hotel search failed: {e}"

    def _search_pois(self, destination: str, preferences: List[str], pref_hint: str | None) -> tuple[List[Dict[str, Any]], str]:
        pref_part = (", ".join(preferences)) if preferences else "attractions"
        query = f"{pref_part} in {destination}"
        try:
            res = self.tavily.search(query=query, search_depth="basic", max_results=40)
            items: List[Dict[str, Any]] = []
            for r in res.get("results", []):
                raw = (r.get("title") or "").strip()
                url = r.get("url")
                if not raw:
                    continue
                if is_generic_title(raw):
                    continue
                name = normalize_title(raw)
                # Make action-friendly
                name = actionize(name, pref_hint)
                if name and not any(x.get("name") == name for x in items):
                    items.append({"name": name, "url": url})
            reason = f"Collected {len(items)} itinerary items via Tavily for {pref_part}."
            return items, reason
        except Exception as e:
            return [], f"POI search failed: {e}"

    def _default_activities(self, destination: str) -> List[Dict[str, Any]]:
        return [
            {"name": f"Morning walking tour of {destination}"},
            {"name": f"Lunch at a local market in {destination}"},
            {"name": f"Afternoon museum visit in {destination}"},
            {"name": f"Sunset viewpoint in {destination}"},
            {"name": f"Dinner in {destination} city center"}
        ]

    def _build_daily_schedule(self, start_date: datetime, num_days: int, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        schedule: List[Dict[str, Any]] = []
        idx = 0
        for i in range(num_days):
            day = start_date + timedelta(days=i)
            day_plan: List[Dict[str, Any]] = []
            for slot in ["09:00 • Morning", "13:30 • Afternoon", "18:30 • Evening"]:
                entry = items[idx] if idx < len(items) else {"name": "Free time / explore locally"}
                idx = min(idx + 1, len(items))
                day_plan.append({
                    "time": slot,
                    "name": entry.get("name", "Activity"),
                    "url": entry.get("url")
                })
            schedule.append({
                "date": day.strftime("%Y-%m-%d"),
                "items": day_plan
            })
        return schedule

    def _booking_site_for_destination(self, destination: str) -> str:
        params = urlencode({"ss": destination})
        return f"https://www.booking.com/searchresults.html?{params}"