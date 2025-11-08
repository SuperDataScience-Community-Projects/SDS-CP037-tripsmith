from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from datetime import date

class FlightOption(BaseModel):
    """Normalized flight option.

    Args:
        origin: IATA code of origin.
        destination: IATA code of destination.
        depart_date: Departure date (YYYY-MM-DD).
        return_date: Optional return date.
        airline: Marketing airline code.
        price_usd: Total price in USD.
        duration_minutes: Total flight duration in minutes.
        link: Deep link to book.
    """

    origin: str = Field(..., min_length=3, max_length=3)
    destination: str = Field(..., min_length=3, max_length=3)
    depart_date: date
    return_date: Optional[date] = None
    airline: str
    price_usd: float
    duration_minutes: int
    link: Optional[str] = None

    @field_validator("return_date")
    @classmethod
    def validate_dates(cls, v, info):
        depart_date = info.data.get("depart_date")
        if v and depart_date and v < depart_date:
            raise ValueError("return_date cannot be before depart_date")
        return v


class HotelOption(BaseModel):
    """Normalized hotel option.

    Args:
        name: Hotel name.
        check_in: Check-in date.
        check_out: Check-out date.
        nightly_rate_usd: Average nightly rate.
        rating: Average rating (0-5).
        link: Booking link.
    """

    name: str
    check_in: date
    check_out: date
    nightly_rate_usd: float
    rating: float = Field(..., ge=0, le=5)
    link: Optional[str] = None

    @field_validator("check_out")
    @classmethod
    def validate_range(cls, v, info):
        if v <= info.data.get("check_in"):
            raise ValueError("check_out must be after check_in")
        return v


class POI(BaseModel):
    """Point of Interest / activity.

    Args:
        title: Name of the activity or place.
        category: Type (e.g., museum, food, nature).
        duration_minutes: Estimated time needed.
        price_estimate_usd: Estimated cost.
        link: Reference URL.
    """

    title: str
    category: str
    duration_minutes: int
    price_estimate_usd: float = 0.0
    link: Optional[str] = None


class DayPlan(BaseModel):
    date: date
    activities: List[POI] = []
    free_time_minutes: int = 0


class Itinerary(BaseModel):
    """Complete itinerary bundle returned by the planner."""

    origin: str
    destination: str
    start_date: date
    end_date: date
    flights: List[FlightOption] = []
    hotels: List[HotelOption] = []
    daily_plan: List[DayPlan] = []
    total_estimated_cost_usd: float = 0.0
    rationale: str = ""

    @field_validator("hotels")
    @classmethod
    def validate_coverage(cls, v, info):
        start = info.data.get("start_date")
        end = info.data.get("end_date")
        if not (start and end):
            return v
        total_nights = (end - start).days
        covered = sum((h.check_out - h.check_in).days for h in v)
        if covered < total_nights:
            raise ValueError("Hotel nights do not cover the full trip")
        return v
