from datetime import date
from controller.planner import Planner
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"), override=True)

def run_centralized_demo() -> dict:
    """Run the centralized planner and return itinerary as dict.

    Args:
        None

    Returns:
        dict: Itinerary serialized to a dictionary.

    Raises:
        None

    Notes:
        Useful for CLI or testing.
    """
    p = Planner()
    it = p.plan_trip(
        origin="JFK",
        destination="LAX",
        start_date=date(2025, 10, 10),
        end_date=date(2025, 10, 14),
        budget_per_night=120.0,
        interests=["museum", "food"],
    )
    return it.model_dump()
