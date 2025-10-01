
import asyncio
import logging
from typing import Dict, Any, List, Tuple, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger("PlannerAgentCentralized")

# Dummy AgentResponse for demonstration
class AgentResponse:
    def __init__(self, data: Any, reasoning: str):
        self.data = data
        self.reasoning = reasoning

# Dummy FlightAgent, HotelAgent, POIAgent implementations
class FlightAgent:
    async def process_request(self, request: Dict[str, Any]) -> AgentResponse:
        # Simulate async work
        await asyncio.sleep(0.2)
        # Dummy flight data
        flights = [
            {
                "flight_number": "TS123",
                "departure_date": request.get("departure_date", "2024-07-01"),
                "arrival_date": request.get("departure_date", "2024-07-01"),
                "origin": request.get("origin", "JFK"),
                "destination": request.get("destination", "LAX"),
            },
            {
                "flight_number": "TS124",
                "departure_date": request.get("return_date", "2024-07-07"),
                "arrival_date": request.get("return_date", "2024-07-07"),
                "origin": request.get("destination", "LAX"),
                "destination": request.get("origin", "JFK"),
            }
        ]
        reasoning = "Selected flights based on earliest departure and latest return within requested dates."
        return AgentResponse(flights, reasoning)

class HotelAgent:
    async def process_request(self, request: Dict[str, Any]) -> AgentResponse:
        await asyncio.sleep(0.2)
        hotels = [
            {
                "name": "Hotel Sunshine",
                "check_in": request.get("departure_date", "2024-07-01"),
                "check_out": request.get("return_date", "2024-07-07"),
                "location": request.get("destination", "Los Angeles"),
            }
        ]
        reasoning = "Booked hotel covering entire stay with best ratings and proximity to points of interest."
        return AgentResponse(hotels, reasoning)

class POIAgent:
    async def process_request(self, request: Dict[str, Any]) -> AgentResponse:
        await asyncio.sleep(0.2)
        # Generate daily schedules between dates
        from datetime import datetime, timedelta
        dep = request.get("departure_date", "2024-07-01")
        ret = request.get("return_date", "2024-07-07")
        dep_date = datetime.strptime(dep, "%Y-%m-%d")
        ret_date = datetime.strptime(ret, "%Y-%m-%d")
        days = (ret_date - dep_date).days
        daily_schedules = []
        poi_list = [
            {"name": "Hollywood Walk of Fame", "category": "Sightseeing"},
            {"name": "Santa Monica Pier", "category": "Leisure"},
            {"name": "Griffith Observatory", "category": "Sightseeing"},
            {"name": "Venice Beach", "category": "Leisure"},
        ]
        for i in range(days):
            date = (dep_date + timedelta(days=i)).strftime("%Y-%m-%d")
            daily_schedules.append({
                "date": date,
                "points_of_interest": [poi_list[i % len(poi_list)]]
            })
        reasoning = "Chose diverse attractions to balance sightseeing and leisure activities daily."
        return AgentResponse(daily_schedules, reasoning)

class PlannerAgentCentralized:
    def __init__(self):
        self.flight_agent = FlightAgent()
        self.hotel_agent = HotelAgent()
        self.poi_agent = POIAgent()

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Received planning request: %s", request)
        # Query all agents concurrently
        logger.info("Querying FlightAgent, HotelAgent, and POIAgent concurrently.")
        flight_task = self.flight_agent.process_request(request)
        hotel_task = self.hotel_agent.process_request(request)
        poi_task = self.poi_agent.process_request(request)
        flight_resp, hotel_resp, poi_resp = await asyncio.gather(
            flight_task, hotel_task, poi_task
        )
        logger.info("Received responses from all sub-agents.")

        # Combine results
        itinerary = self.combine_results(flight_resp, hotel_resp, poi_resp)
        reasoning = {
            "flight_agent": flight_resp.reasoning,
            "hotel_agent": hotel_resp.reasoning,
            "poi_agent": poi_resp.reasoning
        }

        # Validate itinerary
        is_valid, validation_msg = self.validate_itinerary(itinerary, request)
        if not is_valid:
            logger.warning("Itinerary validation failed: %s", validation_msg)
            return {
                "success": False,
                "data": itinerary,
                "reasoning": reasoning,
                "error": validation_msg
            }
        logger.info("Itinerary validated successfully.")
        logger.info("Final itinerary: %s", itinerary)
        logger.info("Reasoning: %s", reasoning)
        return {
            "success": True,
            "data": itinerary,
            "reasoning": reasoning
        }

    def combine_results(
        self,
        flight_resp: AgentResponse,
        hotel_resp: AgentResponse,
        poi_resp: AgentResponse
    ) -> Dict[str, Any]:
        logger.info("Combining results from agents.")
        return {
            "flights": flight_resp.data,
            "hotels": hotel_resp.data,
            "daily_schedules": poi_resp.data
        }

    def validate_itinerary(
        self,
        itinerary: Dict[str, Any],
        request: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        # Validate hotel coverage
        flights = itinerary.get("flights", [])
        hotels = itinerary.get("hotels", [])
        daily_schedules = itinerary.get("daily_schedules", [])
        dep = request.get("departure_date")
        ret = request.get("return_date")
        if not flights or not hotels or not daily_schedules:
            return False, "Missing flights, hotels, or daily schedules."
        # Check hotel covers all nights
        hotel = hotels[0]
        if hotel["check_in"] != dep or hotel["check_out"] != ret:
            return False, "Hotel does not cover full trip dates."
        # Check flight dates align
        flight_dep = flights[0]["departure_date"]
        flight_ret = flights[-1]["departure_date"]
        if flight_dep != dep or flight_ret != ret:
            return False, "Flight dates do not match requested trip dates."
        # Check daily schedules cover all days
        from datetime import datetime, timedelta
        dep_date = datetime.strptime(dep, "%Y-%m-%d")
        ret_date = datetime.strptime(ret, "%Y-%m-%d")
        expected_days = (ret_date - dep_date).days
        if len(daily_schedules) != expected_days:
            return False, "Daily schedules do not cover all days of the trip."
        return True, None


# --- For demonstration/testing purposes only ---
if __name__ == "__main__":
    import sys
    import json
    async def main():
        agent = PlannerAgentCentralized()
        sample_request = {
            "origin": "JFK",
            "destination": "LAX",
            "departure_date": "2024-07-01",
            "return_date": "2024-07-07"
        }
        result = await agent.process_request(sample_request)
        print(json.dumps(result, indent=2))
    asyncio.run(main())