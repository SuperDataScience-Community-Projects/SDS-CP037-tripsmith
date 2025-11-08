# orchestration/decentralized.py

from __future__ import annotations
from datetime import date
from typing import Tuple
from models import HotelOption
from controller.planner import Planner


def negotiate_hotel_rate(hotel: HotelOption, budget_per_night: float) -> Tuple[bool, str]:
    """Simple rule-based negotiation: accept if within 10% of budget.

    Args:
        hotel (HotelOption): Proposed hotel option.
        budget_per_night (float): Nightly budget in USD.

    Returns:
        Tuple[bool, str]: (accepted, rationale).

    Notes:
        In a real system, this would be an agent-to-agent dialogue.
    """
    threshold = budget_per_night * 1.10
    if hotel.nightly_rate_usd <= budget_per_night:
        return True, "Within budget."
    if hotel.nightly_rate_usd <= threshold:
        return True, "Slightly above budget but acceptable (<=10%)."
    return False, "Rejected: exceeds 10% over budget."


def run_decentralized_demo() -> dict:
    """Demonstrate decentralized orchestration with hotel negotiation.

    Returns:
        dict: Final itinerary dict.

    Notes:
        Flights and POIs are taken as-is; hotels are negotiated.
    """
    p = Planner()
    it = p.plan_trip(
        origin="JFK",
        destination="LAX",
        start_date=date(2025, 10, 10),
        end_date=date(2025, 10, 14),
        budget_per_night=100.0,
        interests=["museum", "food"],
    )

    if it.hotels:
        accepted, why = negotiate_hotel_rate(it.hotels[0], 100.0)
        it.rationale += f" Hotel decision: {why}"
        if not accepted:
            it.hotels = []
            it.rationale += " (hotel removed; needs re-plan)."

    return it.model_dump()
