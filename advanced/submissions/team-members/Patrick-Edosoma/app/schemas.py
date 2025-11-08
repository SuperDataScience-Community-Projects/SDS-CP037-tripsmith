from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field

class FlightOption(BaseModel):
    origin: str
    destination: str
    depart_date: date
    return_date: date
    airline: str
    price_usd: float
    duration_minutes: int
    link: Optional[str] = None

class HotelOption(BaseModel):
    name: str
    check_in: date
    check_out: date
    nightly_rate_usd: float
    rating: float
    link: Optional[str] = None

class POI(BaseModel):
    title: str
    category: str
    duration_minutes: int
    price_estimate_usd: float
    link: Optional[str] = None

class DayPlan(BaseModel):
    date: date
    activities: List[POI]
    free_time_minutes: int

class PlanRequest(BaseModel):
    origin: str = Field(..., min_length=3, max_length=3, description="IATA code")
    destination: str = Field(..., min_length=3, max_length=3, description="IATA code")
    start_date: date
    end_date: date
    budget_per_night: float = 120.0
    interests: List[str] = ["museum", "food"]

class PlanResponse(BaseModel):
    origin: str
    destination: str
    start_date: date
    end_date: date
    flights: List[FlightOption]
    hotels: List[HotelOption]
    daily_plan: List[DayPlan]
    total_estimated_cost_usd: float
    rationale: str
