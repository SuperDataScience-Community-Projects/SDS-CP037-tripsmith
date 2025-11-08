from datetime import date, timedelta
from typing import List, Dict, Any
from controller.planner import Planner 
from models import Itinerary  

def plan_trip_core(origin: str, destination: str, start_date: date, end_date: date,
                   budget_per_night: float, interests: List[str]) -> Dict[str, Any]:
    planner = Planner()
    it: Itinerary = planner.plan_trip(
        origin=origin,
        destination=destination,
        start_date=start_date,
        end_date=end_date,
        budget_per_night=budget_per_night,
        interests=interests,
    )
    
    return it.model_dump()
