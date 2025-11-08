from __future__ import annotations
from datetime import date, timedelta
from typing import List, Tuple, Set
import logging

from models import FlightOption, HotelOption, Itinerary, DayPlan, POI
from agents.flight_agent import FlightAgent
from agents.hotel_agent import HotelAgent
from agents.poi_agent import POIAgent

logger = logging.getLogger(__name__)


class Planner:
    """Central controller that queries agents and assembles an itinerary."""

    def __init__(self) -> None:
        self.flight_agent = FlightAgent()
        self.hotel_agent = HotelAgent()
        self.poi_agent = POIAgent()

    def _dedupe_flights(self, flights: List[FlightOption]) -> List[FlightOption]:
        """Drop near-duplicates by (airline, rounded price, duration)."""
        seen: Set[Tuple[str, float, int]] = set()
        out: List[FlightOption] = []
        for f in flights:
            key = (f.airline or "XX", round(float(f.price_usd or 0.0), 2), int(f.duration_minutes or 0))
            if key in seen:
                continue
            seen.add(key)
            out.append(f)
        return out

    def _rotate_pois(self, pois: List[POI], days: int, per_day: int = 2) -> List[List[POI]]:
        """Distribute POIs across days, rotating so we don’t show the same 2 each day."""
        if not pois:
            return [[] for _ in range(days)]
        result: List[List[POI]] = []
        n = len(pois)
        for d in range(days):
            start = (d * per_day) % n
            picks = [pois[(start + i) % n] for i in range(min(per_day, n))]
            result.append(picks)
        return result

    def plan_trip(
        self,
        origin: str,
        destination: str,
        start_date: date,
        end_date: date,
        budget_per_night: float,
        interests: List[str],
    ) -> Itinerary:
        """Produce a complete itinerary using centralized orchestration."""

        flights_payload = self.flight_agent.run(origin, destination, start_date, end_date)
        flights = [FlightOption(**f) for f in flights_payload.get("flights", [])]
        logger.info("Found %d flight options (raw)", len(flights))

        flights = self._dedupe_flights(flights)
        flights_sorted = sorted(flights, key=lambda x: (x.price_usd or 9e9, x.duration_minutes or 9e9))
        flights_kept = flights_sorted[:5]
        logger.info("Keeping %d flight options (sorted)", len(flights_kept))

        hotels_payload = self.hotel_agent.run(destination, start_date, end_date, budget_per_night)
        hotels = [HotelOption(**h) for h in hotels_payload.get("hotels", [])]
        logger.info("Found %d hotel options (raw)", len(hotels))

        hotels_sorted = sorted(
            hotels,
            key=lambda h: ((h.nightly_rate_usd or 9e9), -(h.rating or 0.0)),
        )
        hotels_kept = hotels_sorted[:5]
        logger.info("Keeping %d hotel options (sorted)", len(hotels_kept))
        poi_payload = self.poi_agent.run(destination, interests)
        pois = [POI(**p) for p in poi_payload.get("pois", [])]
        logger.info("Found %d POIs", len(pois))

        days = max((end_date - start_date).days, 0)
        daily: List[DayPlan] = []
        rotated = self._rotate_pois(pois, days=days, per_day=2)
        cur = start_date
        for idx in range(days):
            daily.append(DayPlan(date=cur, activities=rotated[idx], free_time_minutes=240))
            cur += timedelta(days=1)

        est_cost = 0.0
        if flights_kept:
            est_cost += float(flights_kept[0].price_usd or 0.0)
        nights = max((end_date - start_date).days, 0)
        if hotels_kept:
            est_cost += nights * float(hotels_kept[0].nightly_rate_usd or 0.0)
        est_cost += sum(float(p.price_estimate_usd or 0.0) for p in pois)
        est_cost = round(est_cost, 2)

        it = Itinerary(
            origin=origin,
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            flights=flights_kept,
            hotels=hotels_kept,
            daily_plan=daily,
            total_estimated_cost_usd=est_cost,
            rationale=(
                "Kept the top 5 cheapest flight options (deduped) and top 5 hotels "
                "within budget tolerance; rotated POIs per day to avoid repetition."
            ),
        )
        return it
