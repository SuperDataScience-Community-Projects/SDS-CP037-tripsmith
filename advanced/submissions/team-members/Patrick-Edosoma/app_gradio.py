# app_gradio.py
from __future__ import annotations

import os, json
from datetime import date, datetime
from typing import List, Optional

import gradio as gr
from dotenv import load_dotenv

# Optional: Gemini
GEMINI_AVAILABLE = False
import google.generativeai as genai
    GEMINI_AVAILABLE = True
except Exception:
    GEMINI_AVAILABLE = False

from controller.planner import Planner
from utils.airports import normalize_to_iata
from utils.logging_config import setup_logging

load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"), override=True)
setup_logging()

if GEMINI_AVAILABLE and os.getenv("GOOGLE_API_KEY"):
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

INTEREST_CHOICES = [
    "museum","nature","food","sea","beach","nightlife","shopping","history",
    "art","outdoors","family","adventure","music","sports",
]

def _country_default_fmt(country_hint: Optional[str]) -> str:
    if not country_hint: return "DD/MM/YYYY"
    ch = country_hint.strip().lower()
    if ch in {"united states","usa","us","u.s.","u.s.a.","philippines","belize","micronesia","palau"}:
        return "MM/DD/YYYY"
    return "DD/MM/YYYY"

def _try_parse_dt(s: str, fmts: List[str]) -> Optional[date]:
    for f in fmts:
        try:
            return datetime.strptime(s.strip(), f).date()
        except Exception:
            pass
    return None

def parse_date_flexible(text: str, country_hint: Optional[str]) -> Optional[date]:
    text = (text or "").strip()
    d = _try_parse_dt(text, ["%Y-%m-%d"])
    if d: return d
    d_df = _try_parse_dt(text, ["%d/%m/%Y","%d-%m-%Y"])
    d_mf = _try_parse_dt(text, ["%m/%d/%Y","%m-%d-%Y"])
    if d_df and d_mf:
        return d_mf if _country_default_fmt(country_hint) == "MM/DD/YYYY" else d_df
    return d_df or d_mf

def format_date_auto(d: date, country_hint: Optional[str]) -> str:
    return (f"{d.month:02d}/{d.day:02d}/{d.year}"
            if _country_default_fmt(country_hint) == "MM/DD/YYYY"
            else f"{d.day:02d}/{d.month:02d}/{d.year}")

def md_flights(it: dict) -> str:
    flights = it.get("flights") or []
    if not flights: return "_No flights found for those dates/route._"
    lines = ["### ✈️ Flight options"]
    for f in flights[:5]:
        airline = f.get("airline","—"); price = f.get("price_usd","—")
        mins = int(f.get("duration_minutes") or 0); h,m = mins//60, mins%60
        od = f"{f.get('origin','—')} → {f.get('destination','—')}"
        base = f"- **{airline}** • {od} • **${price}** • {h}h {m}m"
        if f.get("link"): base += f" • [View]({f['link']})"
        lines.append(base)
    return "\n".join(lines)

def md_hotels(it: dict) -> str:
    hotels = it.get("hotels") or []
    if not hotels: return "_No hotels matched your budget/dates._"
    lines = ["### 🏨 Top hotels"]
    for h in hotels[:5]:
        name = h.get("name","Hotel"); rating = h.get("rating","—"); price = h.get("nightly_rate_usd","—")
        base = f"- **{name}** • ⭐ {rating} • **${price}/night**"
        if h.get("link"): base += f" • [Open]({h['link']})"
        lines.append(base)
    return "\n".join(lines)

def md_daily_plan(it: dict, country_hint: Optional[str]) -> str:
    days = it.get("daily_plan") or []
    if not days: return "_No day-by-day plan generated._"
    lines = ["### 📅 Daily highlights"]
    for d in days:
        dt_raw = d.get("date")
        try:
            if isinstance(dt_raw, str) and len(dt_raw) >= 10:
                dt_parsed = datetime.strptime(dt_raw[:10], "%Y-%m-%d").date()
            elif isinstance(dt_raw, date):
                dt_parsed = dt_raw
            else:
                dt_parsed = None
        except Exception:
            dt_parsed = None
        date_txt = format_date_auto(dt_parsed, country_hint) if dt_parsed else str(dt_raw)
        lines.append(f"- **{date_txt}**")
        for a in (d.get("activities") or [])[:2]:
            title = a.get("title","Activity"); mins = a.get("duration_minutes",0)
            bullet = f"  - {title} ({mins} min)"
            if a.get("link"): bullet += f" — [More]({a['link']})"
            lines.append(bullet)
    return "\n".join(lines)

def md_overview(it: dict, start_date: date, end_date: date, budget_per_night: float,
                interests: List[str], country_hint: Optional[str]) -> str:
    start_h = format_date_auto(start_date, country_hint)
    end_h   = format_date_auto(end_date, country_hint)
    days = (end_date - start_date).days
    nights = max(days, 0)
    origin = it.get("origin","—")
    dest   = it.get("destination","—")
    total_cost = it.get("total_estimated_cost_usd","—")
    flights_n = len(it.get("flights") or [])
    hotels_n  = len(it.get("hotels") or [])
    interests_str = ", ".join(interests) if interests else "—"

    lines = [
        "### 🧭 Trip overview",
        f"- Route: **{origin} → {dest}**",
        f"- Dates: **{start_h} → {end_h}** • Duration: **{days} days / {nights} nights**",
        f"- Budget/night: **${budget_per_night:.2f}** • Est. total: **${total_cost}**",
        f"- Interests: **{interests_str}**",
        f"- Options found: **{flights_n} flights**, **{hotels_n} hotels**",
    ]
    return "\n".join(lines)

def _gemini_enabled() -> bool:
    return GEMINI_AVAILABLE and bool(os.getenv("GOOGLE_API_KEY"))

def _gemini_narrative(itinerary_obj: dict, country_hint: Optional[str]) -> str:
    try:
        if not _gemini_enabled(): return ""
        model = genai.GenerativeModel("gemini-1.5-flash")
        start = itinerary_obj.get("start_date"); end = itinerary_obj.get("end_date")
        origin = itinerary_obj.get("origin",""); dest = itinerary_obj.get("destination","")
        prompt = (
            "You are a concise travel assistant. Given this structured itinerary JSON, write a brief trip narrative.\n"
            "Requirements:\n"
            "- Use simple markdown (short headings + bullets or short paragraphs).\n"
            "- **At least 3 sentences/lines**, ideally 3–6, friendly but succinct.\n"
            "- Include: route & dates, vibe of the destination, what the days focus on, and 1–2 practical tips.\n"
            "- If fields are missing, gracefully skip them. **Do NOT invent prices or links.**\n\n"
            f"Country hint for date formatting: {country_hint or 'None'}\n"
            f"Trip window: {start} → {end}, {origin} → {dest}\n\n"
            f"ITINERARY_JSON:\n{json.dumps(itinerary_obj, ensure_ascii=False, default=str)}"
        )
        resp = model.generate_content(prompt)
        return (getattr(resp, "text", "") or "").strip()
    except Exception:
        return ""


def plan(origin: str, destination: str, country_hint: str,
         start_text: str, end_text: str, budget: float, interests_list: List[str]):
    """
    Plan a trip and return UI sections.

    Args:
        origin: User-entered origin (IATA or city).
        destination: User-entered destination (IATA or city).
        country_hint: Country to disambiguate date formats and destinations.
        start_text: Start date as string.
        end_text: End date as string.
        budget: Budget per night (USD).
        interests_list: Selected interests.

    Returns:
        Tuple[str, str, str, str, str, str, str, str]: Error, summary, overview,
        narrative, origin->location mapping, flights, hotels, daily plan.
    """
    
    start_date = parse_date_flexible(start_text, country_hint or None)
    end_date = parse_date_flexible(end_text, country_hint or None)
    if not start_date or not end_date:
        return ("❌ Please enter valid dates. Examples: 2025-10-10, 10/10/2025, or 10-10-2025.",
                "", "", "", "", "", "", "")
    try:
        budget_val = float(budget)
    except Exception:
        return ("❌ Budget per night must be a number.", "", "", "", "", "", "", "")
    if budget_val < 0:
        return ("❌ Budget per night must be a non-negative number.", "", "", "", "", "", "", "")
    if end_date <= start_date:
        return ("❌ End date must be after start date.", "", "", "", "", "", "", "")
    o = normalize_to_iata(origin)
    d = normalize_to_iata(destination, country_hint or None)
    interests = interests_list or []

    it = Planner().plan_trip(
        origin=o, destination=d, start_date=start_date, end_date=end_date,
        budget_per_night=budget_val, interests=interests,
    )
    it_json = it.model_dump(mode="json")

    start_h = format_date_auto(start_date, country_hint)
    end_h   = format_date_auto(end_date, country_hint)
    days = (end_date - start_date).days
    nights = max(days, 0)
    summary = (
        f"**Summary**\n\n"
        f"- ✈️ **{it.origin} → {it.destination}**\n"
        f"- 📅 **{start_h} → {end_h}** • **{days} days / {nights} nights**\n"
        f"- 💵 Nightly budget: **${budget_val:.2f}** • Est. total: **${it_json.get('total_estimated_cost_usd','—')}**"
    )
    overview = md_overview(it_json, start_date, end_date, budget_val, interests, country_hint)

    narrative = _gemini_narrative(it_json, country_hint) if _gemini_enabled() else ""
    flights_md = md_flights(it_json)
    hotels_md  = md_hotels(it_json)
    days_md    = md_daily_plan(it_json, country_hint)

  
    origin_mapping_text = f"{o} to {d}"

    return ("", summary, overview, narrative, origin_mapping_text, flights_md, hotels_md, days_md)

with gr.Blocks(title="TripSmith — Multi-Agent Travel Planner") as demo:
    gr.Markdown("# TripSmith — Multi-Agent Travel Planner")

    with gr.Row():
        origin = gr.Textbox(value="ABV", label="Origin (IATA or city)")
        destination = gr.Textbox(value="LOS", label="Destination (IATA or city)")

    country_hint = gr.Textbox(value="Nigeria", label="(Optional) Destination country hint")

    start_text = gr.Textbox(value="2025-10-10", label="Start date (Year • Month • Day)")
    end_text   = gr.Textbox(value="2025-10-14", label="End date (Year • Month • Day)")

    with gr.Row():
        budget = gr.Number(value=120, label="Budget/night (USD)", precision=2)
        interests = gr.Dropdown(choices=INTEREST_CHOICES, value=["museum","food"],
                                multiselect=True, label="Interests")

    run_btn = gr.Button("Plan Trip ✈️", variant="primary")

    error_md     = gr.Markdown()
    summary_md   = gr.Markdown()
    overview_md  = gr.Markdown()  
    narrative_md = gr.Markdown()
    origin_map_tb = gr.Textbox(label="Origin → Location", interactive=False)  
    hotels_md    = gr.Markdown()
    days_md      = gr.Markdown()

    run_btn.click(
        plan,
        inputs=[origin, destination, country_hint, start_text, end_text, budget, interests],
        outputs=[error_md, summary_md, overview_md, narrative_md, origin_map_tb, flights_md, hotels_md, days_md],
        show_progress=True,  
    )

    demo.queue()

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
