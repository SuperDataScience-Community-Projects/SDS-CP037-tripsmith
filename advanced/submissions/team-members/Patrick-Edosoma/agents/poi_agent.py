from __future__ import annotations
from typing import Dict, Any, List
from .base import Agent
from models import POI
from utils.search_providers import poi_search

class POIAgent(Agent):
    """Agent for activities / points of interest."""

    name = "poi_agent"

    def run(self, city: str, interests: List[str]) -> Dict[str, Any]:
        pois = poi_search(city, interests)
        return {"pois": [p.model_dump() for p in pois]}
