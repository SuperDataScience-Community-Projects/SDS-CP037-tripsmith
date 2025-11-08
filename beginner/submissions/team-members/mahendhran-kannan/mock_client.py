from typing import Dict, Any
import random
import datetime

class MockTavilyClient:
    def request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Expect payload to include "query"
        q = payload.get("query", "").lower()
        # crude routing by keywords in query
        if "flight" in q or "flights" in q:
            return self._mock_flights(payload)
        if "hotel" in q or "hotels" in q:
            return self._mock_hotels(payload)
        if "point of interest" in q or "points of interest" in q or "find points" in q or "poi" in q:
            return self._mock_pois(payload)
        # fallback: attempt to detect 'poi' by interests phrase
        if "find points of interest" in q or "within" in q and ":" in q:
            return self._mock_pois(payload)
        return {"results": []}

    def _mock_flights(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        results = []
        for i in range(2):
            results.append({
                "airline": f"AirMock {i+1}",
                "price": round(random.uniform(80, 500), 2),
                "currency": "USD",
                "segments": [{"from": "XXX", "to": "YYY", "duration_mins": 90}]
            })
        return {"results": results}

    def _mock_hotels(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        hotels = []
        for i in range(3):
            hotels.append({
                "name": f"Hotel Mock {i+1}",
                "price_per_night": round(70 + i*30, 2),
                "rating": round(3.5 + i*0.5, 1),
                "address": f"{i+1} Mock St"
            })
        return {"hotels": hotels}

    def _mock_pois(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        pois = []
        # try extract interests after ":" if present
        q = payload.get("query", "")
        if ":" in q:
            parts = q.split(":")
            interests = parts[-1].split(",")
        else:
            interests = ["attraction", "museum"]
        for i, interest in enumerate([x.strip() for x in interests][:5]):
            pois.append({
                "name": f"{interest.title()} Place {i+1}",
                "category": interest.strip().lower(),
                "rating": round(4.0 - i*0.2, 1),
                "open_hours": "10:00-18:00"
            })
        return {"pois": pois}
