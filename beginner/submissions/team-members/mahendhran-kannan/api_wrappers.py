# api_wrappers.py
from typing import Any, Dict, List, Optional, Protocol
from datetime import date, datetime

class HTTPClientProtocol(Protocol):
    def request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        ...

def _ensure_date_iso(d: Optional[Any]) -> Optional[str]:
    if d is None:
        return None
    if isinstance(d, str):
        try:
            datetime.fromisoformat(d)
            return d
        except Exception:
            raise ValueError(f"Invalid date string: {d}")
    if isinstance(d, (date, datetime)):
        return d.isoformat()
    raise ValueError("date must be a date/datetime or ISO string")

# helper to build payload for Tavily (natural-language)
def _tavily_payload_from_query(query: str, max_results: int = 10) -> Dict[str, Any]:
    return {"query": query, "max_results": max_results}

class FlightSearch:
    ENDPOINT = "/search"   # generic search endpoint for Tavily

    def __init__(self, client: HTTPClientProtocol):
        self.client = client

    def build_nl_query(
        self,
        origin: str,
        destination: str,
        depart_date: Any,
        return_date: Optional[Any] = None,
        passengers: int = 1,
        cabin_class: str = "economy",
        sort: str = "best price"
    ) -> str:
        depart_iso = _ensure_date_iso(depart_date)
        return_iso = _ensure_date_iso(return_date) if return_date else None
        q = f"List flights from {origin} to {destination} on {depart_iso}"
        if return_iso:
            q += f" returning on {return_iso}"
        q += f", {passengers} passenger{'s' if passengers>1 else ''}, {cabin_class} cabin, sort by {sort}."
        return q

    def search(self, **kwargs) -> List[Dict[str, Any]]:
        nl = self.build_nl_query(**kwargs)
        payload = _tavily_payload_from_query(nl, max_results=10)
        resp = self.client.request(self.ENDPOINT, payload)
        return self._parse_response(resp)

    def _parse_response(self, resp: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = resp.get("results", resp.get("flights", []))
        parsed = []
        for r in results:
            parsed.append({
                "airline": r.get("airline"),
                "price": r.get("price"),
                "currency": r.get("currency", "USD"),
                "segments": r.get("segments", []),
                "raw": r
            })
        return parsed


class HotelSearch:
    ENDPOINT = "/search"

    def __init__(self, client: HTTPClientProtocol):
        self.client = client

    def build_nl_query(
        self,
        location: str,
        checkin: Any,
        checkout: Any,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_rating: Optional[float] = None,
    ) -> str:
        ci = _ensure_date_iso(checkin)
        co = _ensure_date_iso(checkout)
        parts = [f"Search hotels in {location} from {ci} to {co}"]
        if min_price is not None or max_price is not None:
            parts.append(f"price between {min_price or 'any'} and {max_price or 'any'} per night")
        if min_rating is not None:
            parts.append(f"minimum rating {min_rating}")
        parts.append("return best matches")
        return ", ".join(parts) + "."

    def search(self, **kwargs) -> List[Dict[str, Any]]:
        nl = self.build_nl_query(**kwargs)
        payload = _tavily_payload_from_query(nl, max_results=10)
        resp = self.client.request(self.ENDPOINT, payload)
        return self._parse_response(resp)

    def _parse_response(self, resp: Dict[str, Any]) -> List[Dict[str, Any]]:
        hotels = resp.get("hotels", resp.get("results", []))
        parsed = []
        for h in hotels:
            parsed.append({
                "name": h.get("name"),
                "price_per_night": h.get("price_per_night"),
                "rating": h.get("rating"),
                "address": h.get("address"),
                "raw": h
            })
        return parsed


class POISearch:
    ENDPOINT = "/search"

    def __init__(self, client: HTTPClientProtocol):
        self.client = client

    def build_nl_query(self, location: str, interests: List[str], radius_km: float = 5.0) -> str:
        if not interests:
            raise ValueError("interests must be a non-empty list")
        interest_text = ", ".join(interests)
        q = f"Find points of interest in {location} within {radius_km} km for: {interest_text}. Include opening hours and ratings if available."
        return q

    def search(self, **kwargs) -> List[Dict[str, Any]]:
        nl = self.build_nl_query(**kwargs)
        payload = _tavily_payload_from_query(nl, max_results=20)
        resp = self.client.request(self.ENDPOINT, payload)
        return self._parse_response(resp)

    def _parse_response(self, resp: Dict[str, Any]) -> List[Dict[str, Any]]:
        pois = resp.get("pois", resp.get("results", []))
        parsed = []
        for p in pois:
            parsed.append({
                "name": p.get("name"),
                "category": p.get("category"),
                "rating": p.get("rating"),
                "open_hours": p.get("open_hours"),
                "raw": p
            })
        return parsed
