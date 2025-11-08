# app_streamlit.py
from __future__ import annotations

import os
import json
from datetime import date, datetime
from typing import List, Optional

import streamlit as st

from dotenv import load_dotenv
GEMINI_AVAILABLE = False
import google.generativeai as genai  
    GEMINI_AVAILABLE = True
except Exception:
    GEMINI_AVAILABLE = False

from controller.planner import Planner
from utils.logging_config import setup_logging
from utils.airports import normalize_to_iata 

try:
    from babel.dates import format_date as _babel_format  
except Exception:
    _babel_format = None

_COUNTRY_TO_LOCALE = {
    "United States": "en_US", "USA": "en_US", "US": "en_US",
    "Nigeria": "en_NG",
    "United Kingdom": "en_GB", "UK": "en_GB", "Britain": "en_GB",
    "France": "fr_FR",
    "Germany": "de_DE",
    "South Africa": "en_ZA",
    "Canada": "en_CA",
    "Australia": "en_AU",
}

INTEREST_CHOICES = [
    "museum", "nature", "food", "sea", "beach",
    "nightlife", "shopping", "history", "art",
    "outdoors", "family", "adventure", "music", "sports",
]

load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"), override=True)
setup_logging()


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GEMINI_AVAILABLE and GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)


def format_trip_date(d: date, *, style: str = "AUTO_COUNTRY", country_hint: str | None = None) -> str:
    """Format a date for display; API calls still use ISO."""
    if not isinstance(d, date):
        return str(d)
    if style == "MDY_LONG":   
        return d.strftime("%B %d, %Y")
    if style == "DMY_LONG":   
        return d.strftime("%d %B %Y")
    if style == "MDY_SLASH":  
        return d.strftime("%m/%d/%Y")
    if style == "DMY_SLASH":  
        return d.strftime("%d/%m/%Y")
    if style == "YMD_DASH":   
        return d.strftime("%Y-%m-%d")

    if _babel_format and country_hint:
        loc = _COUNTRY_TO_LOCALE.get(country_hint.strip())
        if loc:
            try:
                return _babel_format(d, format="long", locale=loc)
            except Exception:
                pass
    return d.isoformat()

def md_flights(it: dict) -> str:
    flights = it.get("flights") or []
    if not flights:
        return "_No flights found for those dates/route._"
    lines = ["### ✈️ Flight options"]
    for f in flights[:5]:
        airline = f.get("airline", "—")
        price = f.get("price_usd", "—")
        mins = int(f.get("duration_minutes") or 0)
        h, m = mins // 60, mins % 60
        od = f"{f.get('origin','—')} → {f.get('destination','—')}"
        base = f"- **{airline}** • {od} • **${price}** • {h}h {m}m"
        if f.get("link"):
            base += f" • [View]({f['link']})"
        lines.append(base)
    return "\n".join(lines)

def md_hotels(it: dict) -> str:
    hotels = it.get("hotels") or []
    if not hotels:
        return "_No hotels matched your budget/dates._"
    lines = ["### 🏨 Top hotels"]
    for h in hotels[:5]:
        name = h.get("name", "Hotel")
        rating = h.get("rating", "—")
        price = h.get("nightly_rate_usd", "—")
        base = f"- **{name}** • ⭐ {rating} • **${price}/night**"
        if h.get("link"):
            base += f" • [Open]({h['link']})"
        lines.append(base)
    return "\n".join(lines)

def md_daily_plan(it: dict, country_hint: Optional[str]) -> str:
    days = it.get("daily_plan") or []
    if not days:
        return "_No day-by-day plan generated._"
    lines = ["### 📅 Daily highlights"]
    for d in days:
        dt_raw = d.get("date")
        parsed = None
        try:
            if isinstance(dt_raw, str) and len(dt_raw) >= 10:
                parsed = datetime.strptime(dt_raw[:10], "%Y-%m-%d").date()
            elif isinstance(dt_raw, date):
                parsed = dt_raw
        except Exception:
            parsed = None
        date_txt = format_trip_date(parsed, country_hint=country_hint) if parsed else str(dt_raw)
        lines.append(f"- **{date_txt}**")
        for a in (d.get("activities") or [])[:2]:
            title = a.get("title", "Activity"); mins = a.get("duration_minutes", 0)
            bullet = f"  - {title} ({mins} min)"
            if a.get("link"):
                bullet += f" — [More]({a['link']})"
            lines.append(bullet)
    return "\n".join(lines)

def gemini_narrative(itinerary_obj: dict, country_hint: Optional[str]) -> str:
    """Generate a concise travel brief via Gemini; empty string if disabled or any error."""
    try:
        if not (GEMINI_AVAILABLE and GOOGLE_API_KEY):
            return ""
        model = genai.GenerativeModel("gemini-1.5-flash")
        start = itinerary_obj.get("start_date")
        end = itinerary_obj.get("end_date")
        origin = itinerary_obj.get("origin", "")
        dest = itinerary_obj.get("destination", "")
        prompt = (
            "You are a concise travel assistant. Given this structured itinerary JSON, write a short, upbeat brief.\n"
            "Keep it under ~250 words. Use simple markdown headings and bullets. Include:\n"
            "1) Trip overview with dates and route\n"
            "2) Flight options (price, airline, duration, and 'View' link if present)\n"
            "3) 3–5 hotel suggestions with price/night, rating, and a link if present\n"
            "4) A compact day-by-day highlight (1–2 bullets/day)\n"
            "5) A couple of tips.\n"
            "If fields are missing, gracefully skip them. Do NOT invent prices or links.\n\n"
            f"Country hint for date formatting: {country_hint or 'None'}\n"
            f"Trip window: {start} → {end}, {origin} → {dest}\n\n"
            f"ITINERARY_JSON:\n{json.dumps(itinerary_obj, ensure_ascii=False, default=str)}"
        )
        resp = model.generate_content(prompt)
        return (getattr(resp, "text", "") or "").strip()
    except Exception:
        return ""

st.set_page_config(page_title="TripSmith Planner", page_icon="✈️", layout="centered")
st.title("TripSmith — Multi-Agent Travel Planner")

with st.form("trip_form"):
    
    col1, col2 = st.columns(2)
    with col1:
        origin = st.text_input("Origin (IATA or city)", value="ABV")
    with col2:
        destination = st.text_input("Destination (IATA or city)", value="LOS")

    country_hint = st.text_input("(Optional) Destination country hint", value="Nigeria")

    col3, col4 = st.columns(2)
    with col3:
        start_date = st.date_input("Start date", value=date(2025, 10, 10))
    with col4:
        end_date = st.date_input("End date", value=date(2025, 10, 14))

    col5, col6 = st.columns(2)
    with col5:
        budget = st.number_input("Budget per night (USD)", value=120.0, step=5.0, min_value=0.0)
    with col6:
        interests = st.multiselect(
            "Interests",
            INTEREST_CHOICES,
            default=["museum", "food"],
            help="Pick a couple—agents will balance activities and free time.",
        )

    submitted = st.form_submit_button("Plan Trip")

if submitted:
    if end_date <= start_date:
        st.error("End date must be after start date.")
        st.stop()

    o = normalize_to_iata(origin)
    d = normalize_to_iata(destination, country_hint or None)
    if o != origin or d != destination:
        st.info(f"Converted inputs → origin: {o}, destination: {d}")

    with st.spinner("Planning your trip…"):
        it = Planner().plan_trip(
            origin=o,
            destination=d,
            start_date=start_date,
            end_date=end_date,
            budget_per_night=budget,
            interests=interests,
        )

    sd = format_trip_date(it.start_date, style="AUTO_COUNTRY", country_hint=country_hint)
    ed = format_trip_date(it.end_date,   style="AUTO_COUNTRY", country_hint=country_hint)
    st.markdown(
        f"**Summary:** ✈️ **{it.origin} → {it.destination}** • "
        f"📅 **{sd} → {ed}** • "
        f"💵 **est. ${it.total_estimated_cost_usd}**"
    )

    if GEMINI_AVAILABLE and GOOGLE_API_KEY:
        with st.spinner("Generating travel brief…"):
            narrative = gemini_narrative(it.model_dump(mode='json'), country_hint)
        if narrative:
            st.markdown("---")
            st.markdown(narrative)

    it_json = it.model_dump(mode="json")
    st.markdown("---")
    st.markdown(md_flights(it_json))
    st.markdown("---")
    st.markdown(md_hotels(it_json))
    st.markdown("---")
    st.markdown(md_daily_plan(it_json, country_hint))
