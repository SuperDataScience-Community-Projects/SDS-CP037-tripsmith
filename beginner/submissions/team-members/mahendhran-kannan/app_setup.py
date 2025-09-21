from live_client import LiveClient
from api_wrappers import FlightSearch, HotelSearch, POISearch
from mock_client import MockTavilyClient
import os

BASE_URL = "https://api.tavily.com/search"
def create_search_services():
    # LiveClient will read TAVILY_API_KEY from env if not passed explicitly
    #client = MockTavilyClient() 
    client = LiveClient(BASE_URL)
    flight_search = FlightSearch(client)
    hotel_search = HotelSearch(client)
    poi_search = POISearch(client)
    return flight_search, hotel_search, poi_search

if __name__ == "__main__":
    flights, hotels, pois = create_search_services()   
    flights_result = flights.search(origin="London", destination="Paris", depart_date="2025-10-15", passengers=1)
    print("Flights:", flights_result)


