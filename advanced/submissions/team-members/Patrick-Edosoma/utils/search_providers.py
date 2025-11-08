from __future__ import annotations
from typing import List, Optional
from datetime import date
import os
import re
import logging
from urllib.parse import quote_plus
import requests
from dotenv import load_dotenv

from models import FlightOption, HotelOption, POI
from utils.airports import get_city_for_iata  

load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"), override=True)

logger = logging.getLogger(__name__)


def _iso8601_to_minutes(s: str) -> int:
    """Convert ISO 8601 durations like 'PT5H30M' to total minutes."""
    m = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?", s or "")
    if not m:
        return 0
    h = int(m.group(1) or 0)
    mm = int(m.group(2) or 0)
    return h * 60 + mm

def _google_flights_link(origin: str, dest: str, depart: date, ret: date,
                         currency: str = "USD", airline: Optional[str] = None) -> str:
    """
    Generate a stable text-query deep link to Google Flights for this route/dates.
    (Hash-format links are volatile; this query form is robust.)
    """
    q = f"flights from {origin} to {dest} on {depart.isoformat()} return {ret.isoformat()} currency {currency}"
    if airline:
        q += f" airline {airline}"
    return f"https://www.google.com/travel/flights?q={quote_plus(q)}"



def mock_flight_search(origin: str, destination: str, start: date, end: date) -> List[FlightOption]:
    """Return fake flight options for demo and testing."""
    return [
        FlightOption(
            origin=origin,
            destination=destination,
            depart_date=start,
            return_date=end,
            airline="TS",
            price_usd=350.0,
            duration_minutes=420,
        
        ),
        FlightOption(
            origin=origin,
            destination=destination,
            depart_date=start,
            return_date=end,
            airline="TS",
            price_usd=430.0,
            duration_minutes=360,
            
        ),
    ]


def mock_hotel_search(city: str, check_in: date, check_out: date, max_rate: float) -> List[HotelOption]:
    """Return fake hotel options within a max nightly rate."""
    return [
        HotelOption(
            name="Central Inn",
            check_in=check_in,
            check_out=check_out,
            nightly_rate_usd=min(max_rate, 120.0),
            rating=4.3,
        ),
        HotelOption(
            name="Budget Stay",
            check_in=check_in,
            check_out=check_out,
            nightly_rate_usd=min(max_rate, 85.0),
            rating=3.9,
        ),
    ]


def mock_poi_search(city: str, interests: list[str]) -> List[POI]:
    """Return fake points of interest filtered by category."""
    base = [
        POI(title="City Museum", category="museum", duration_minutes=120, price_estimate_usd=20.0),
        POI(title="Riverside Walk", category="nature", duration_minutes=90, price_estimate_usd=0.0),
        POI(title="Street Food Tour", category="food", duration_minutes=150, price_estimate_usd=35.0),
    ]
    if interests:
        filtered = [p for p in base if p.category in interests]
        return filtered or base
    return base



_TAVILY_URL = "https://api.tavily.com/search"

def poi_search(city: str, interests: list[str]) -> List[POI]:
    """
    Use Tavily if TAVILY_API_KEY set; otherwise, fall back to mocks.
    IMPORTANT: expands IATA (e.g., 'LOS') to 'Lagos, Nigeria' so Tavily doesn't think it's Los Angeles.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        logger.info("poi_search: no TAVILY_API_KEY; falling back to mocks.")
        return mock_poi_search(city, interests)

    human_city = get_city_for_iata(city)

    query = f"Top things to do in {human_city}: " + ", ".join(interests or ["sightseeing"])
    try:
        resp = requests.post(
            _TAVILY_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"query": query, "max_results": 5},
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results") or []
        pois: List[POI] = []
        cat = (interests[0] if interests else "activity")
        for r in results[:5]:
            title = r.get("title") or "Activity"
            url = r.get("url")
            pois.append(POI(title=title, category=cat, duration_minutes=120, price_estimate_usd=0.0, link=url))
        if not pois:
            logger.info("poi_search: Tavily returned no results; falling back to mocks.")
            return mock_poi_search(city, interests)
        return pois
    except Exception as e:
        logger.warning("poi_search error (%s); falling back to mocks.", e)
        return mock_poi_search(city, interests)

_AMADEUS_AUTH = "https://test.api.amadeus.com/v1/security/oauth2/token"
_AMADEUS_FLIGHTS = "https://test.api.amadeus.com/v2/shopping/flight-offers"

def _amadeus_token() -> Optional[str]:
    key = os.getenv("AMADEUS_API_KEY")
    sec = os.getenv("AMADEUS_API_SECRET")
    if not key or not sec:
        return None
    r = requests.post(
        _AMADEUS_AUTH,
        data={"grant_type": "client_credentials", "client_id": key, "client_secret": sec},
        timeout=20,
    )
    r.raise_for_status()
    return r.json().get("access_token")

def _price_band(p: float, width: float = 10.0) -> float:
    return round(float(p or 0.0) / width) * width

def _dedupe_flights_list(items: List[FlightOption]) -> List[FlightOption]:
    seen = set()
    out = []
    for f in items:
        key = (f.airline or "XX", _price_band(f.price_usd or 0.0), int(f.duration_minutes or 0))
        if key in seen:
            continue
        seen.add(key)
        out.append(f)
    return out

def flight_search(origin: str, destination: str, start: date, end: date) -> List[FlightOption]:
    """Use Amadeus if keys are set; otherwise, fall back to mocks. If real results < 5, pad with deduped mocks."""
    token = _amadeus_token()
    options: List[FlightOption] = []

    if token:
        try:
            params = {
                "originLocationCode": origin,
                "destinationLocationCode": destination,
                "departureDate": start.isoformat(),
                "returnDate": end.isoformat(),
                "adults": 1,
                "currencyCode": "USD",
                "max": 20,
            }
            r = requests.get(_AMADEUS_FLIGHTS, headers={"Authorization": f"Bearer {token}"}, params=params, timeout=25)
            r.raise_for_status()
            payload = r.json().get("data", [])

            for fo in payload[:10]:
                price = float(fo["price"]["grandTotal"])
                itins = fo.get("itineraries") or []
                dur_iso = (itins[0].get("duration") if itins else None) or "PT0M"
                duration_minutes = _iso8601_to_minutes(dur_iso)
                airline = (fo.get("validatingAirlineCodes") or ["XX"])[0]

                options.append(
                    FlightOption(
                        origin=origin,
                        destination=destination,
                        depart_date=start,
                        return_date=end,
                        airline=airline,
                        price_usd=price,
                        duration_minutes=duration_minutes,
                        link=_google_flights_link(origin, destination, start, end, currency="USD", airline=airline),
                    )
                )
        except Exception as e:
            logger.warning("flight_search Amadeus error (%s); will fall back to mocks.", e)

    if len(options) < 5:
        mocks = mock_flight_search(origin, destination, start, end)

        padded = []
        bump = 0
        for m in mocks:
            bumped = FlightOption(
                origin=m.origin,
                destination=m.destination,
                depart_date=m.depart_date,
                return_date=m.return_date,
                airline=m.airline,
                price_usd=float(m.price_usd) + bump,          
                duration_minutes=int(m.duration_minutes) + bump % 30,  
                link=_google_flights_link(origin, destination, start, end, currency="USD", airline=m.airline),
            )
            padded.append(bumped)
            bump += 10

        options = _dedupe_flights_list(options + padded)

    
    options = sorted(options, key=lambda x: (x.price_usd or 9e9, x.duration_minutes or 9e9))[:5]
    return options




_SERPAPI_ENDPOINT = "https://serpapi.com/search.json"
_price_re = re.compile(r"(\d+[.,]?\d*)")

def _parse_price(text: str, default: float) -> float:
    if not text:
        return default
    m = _price_re.search(str(text).replace(",", ""))
    if not m:
        return default
    try:
        return float(m.group(1))
    except ValueError:
        return default

def hotel_search(city: str, check_in: date, check_out: date, max_rate: float) -> List[HotelOption]:
    """
    Use SerpApi Google Hotels if SERPAPI_API_KEY is set; else fall back to mocks.
    Queries proper check-in/out dates and normalizes property results.
    """
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        logger.info("hotel_search: no SERPAPI_API_KEY; falling back to mocks.")
        return mock_hotel_search(city, check_in, check_out, max_rate)

    human_city = get_city_for_iata(city)  
    try:
        params = {
            "engine": "google_hotels",
            "q": human_city,
            "check_in_date": check_in.isoformat(),
            "check_out_date": check_out.isoformat(),
            "currency": "USD",
            "api_key": api_key,
            "hl": "en",
        }
        r = requests.get(_SERPAPI_ENDPOINT, params=params, timeout=25)
        r.raise_for_status()
        data = r.json()

        props = data.get("properties") or []
        hotels: List[HotelOption] = []

        for p in props[:15]:
            name = p.get("name")
            if not name:
                continue

            rating = p.get("overall_rating") or p.get("reviews_rating") or 4.0
            try:
                rating = float(rating)
            except Exception:
                rating = 4.0

            pn = None
            price_block = p.get("price_per_night") or {}
            if isinstance(price_block, dict):
                pn = price_block.get("lowest") or price_block.get("extracted")

            if pn is None:
                total_rate = p.get("total_rate") or {}
                if isinstance(total_rate, dict):
                    pn = total_rate.get("extracted")

            if pn is None:
            
                text_fields = [p.get("rate_per_night"), p.get("price"), p.get("description")]
                val = next((t for t in text_fields if t), "")
                if val:
                    pn = _parse_price(val, default=max_rate or 120.0)

            if pn is None or float(pn) < 20.0 or float(pn) > 2000.0:
                continue

            if max_rate and float(pn) > max_rate * 1.25:
                continue

            link = (
                p.get("link")
                or p.get("booking_link")
                or p.get("google_maps_url")
                or ((p.get("links") or {}).get("booking"))
                or ((p.get("links") or {}).get("maps"))
            )
            if not link:
                query = f"{name} {human_city}"
                link = f"https://www.google.com/maps/search/?api=1&query={quote_plus(query)}"

            hotels.append(
                HotelOption(
                    name=name,
                    check_in=check_in,
                    check_out=check_out,
                    nightly_rate_usd=float(pn),
                    rating=float(min(max(rating, 0.0), 5.0)),
                    link=link,
                )
            )

        if not hotels:
            logger.info("hotel_search: no properties parsed; falling back to mocks.")
            return mock_hotel_search(human_city, check_in, check_out, max_rate)
            
        hotels.sort(key=lambda h: ((h.nightly_rate_usd or 9e9), -(h.rating or 0.0)))
        return hotels

    except Exception as e:
        logger.warning("hotel_search error (%s); falling back to mocks.", e)
        return mock_hotel_search(human_city, check_in, check_out, max_rate)
