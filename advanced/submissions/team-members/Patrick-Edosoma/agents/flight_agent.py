from __future__ import annotations
from datetime import date
from typing import Dict, Any
from .base import Agent
from models import FlightOption
from utils.search_providers import flight_search


class FlightAgent(Agent):
    """Agent responsible for flight discovery and normalization."""

    name = "flight_agent"

    def run(self, origin: str, destination: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """Search and normalize flight options.

        Args:
            origin: Origin IATA code.
            destination: Destination IATA or city code.
            start_date: Outbound date.
            end_date: Return date.

        Returns:
            Dict with key "flights" -> list of FlightOption dicts.
        """
        flights = flight_search(origin, destination, start_date, end_date)
        return {"flights": [f.model_dump() for f in flights]}
