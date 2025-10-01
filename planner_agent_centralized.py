import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
from urllib.parse import urlencode

from tavily import TavilyClient


class PlannerAgentCentralized:
    """
    Centralized planner using only Tavily.
    - Hotels: names extracted from web search; single booking site URL provided
    - Itinerary: builds morning/afternoon/evening slots from POIs without URLs
    - Budgets: split into hotel and activities allocations
    """

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
        total_budget = float(request.get("budget", 0) or 0)
        hotel_budget = float(request.get("hotel_budget", 0) or 0)
        activity_budget = float(request.get("activity_budget", 0) or 0)

        if total_budget and not (hotel_budget or activity_budget):
            hotel_budget = round(total_budget * 0.6, 2)
            activity_budget = round(total_budget * 0.4, 2)

        hotel_names, hotel_reason = self._search_hotel_names(destination)
        poi_items, poi_reason = self._search_pois(destination, preferences)

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
            res = self.tavily.search(query=query, search_depth="basic", max_results=12)
            names: List[str] = []
            for r in res.get("results", []):
                title = (r.get("title") or "").strip()
                if not title:
                    continue
                # Filter out generic pages without clear hotel names
                if any(k in title.lower() for k in ["best", "top", "guide", "things", "visit", "attractions"]):
                    continue
                names.append(title[:140])
            names = list(dict.fromkeys(names))  # de-duplicate preserving order
            reason = f"Collected {len(names)} hotel name candidates via Tavily."
            return names, reason
        except Exception as e:
            return [], f"Hotel search failed: {e}"

    def _search_pois(self, destination: str, preferences: List[str]) -> tuple[List[Dict[str, Any]], str]:
        pref_part = (", ".join(preferences)) if preferences else "top attractions"
        query = f"{pref_part} in {destination} with short descriptions"
        try:
            res = self.tavily.search(query=query, search_depth="basic", max_results=24)
            items: List[Dict[str, Any]] = []
            for r in res.get("results", []):
                title = (r.get("title") or "").strip()
                snippet = (r.get("content") or "").strip()
                if not title:
                    continue
                items.append({
                    "name": title[:140],
                    "note": snippet[:200] if snippet else ""
                })
            # Deduplicate by name
            seen = set()
            unique_items: List[Dict[str, Any]] = []
            for it in items:
                if it["name"] in seen:
                    continue
                seen.add(it["name"])
                unique_items.append(it)
            reason = f"Collected {len(unique_items)} itinerary items via Tavily for {pref_part}."
            return unique_items, reason
        except Exception as e:
            return [], f"POI search failed: {e}"

    def _build_daily_schedule(self, start_date: datetime, num_days: int, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        schedule: List[Dict[str, Any]] = []
        idx = 0
        for i in range(num_days):
            day = start_date + timedelta(days=i)
            day_plan: List[Dict[str, Any]] = []
            # Morning, Afternoon, Evening slots
            for slot in ["09:00 • Morning", "13:30 • Afternoon", "18:30 • Evening"]:
                if idx < len(items):
                    entry = items[idx]
                    idx += 1
                    day_plan.append({
                        "time": slot,
                        "name": entry.get("name", "Activity"),
                        "note": entry.get("note", "")
                    })
            schedule.append({
                "date": day.strftime("%Y-%m-%d"),
                "items": day_plan
            })
        return schedule

    def _booking_site_for_destination(self, destination: str) -> str:
        # Prefer Booking.com city search link
        params = urlencode({"ss": destination})
        return f"https://www.booking.com/searchresults.html?{params}"
