from __future__ import annotations
from datetime import date
from typing import Dict, Any
from .base import Agent
from models import HotelOption
from utils.search_providers import hotel_search

class HotelAgent(Agent):
    """Agent responsible for hotel discovery and filtering."""

    name = "hotel_agent"

    def run(self, city: str, check_in: date, check_out: date, max_rate: float) -> Dict[str, Any]:
        hotels = hotel_search(city, check_in, check_out, max_rate)
        return {"hotels": [h.model_dump() for h in hotels]}
