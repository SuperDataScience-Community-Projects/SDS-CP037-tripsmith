import pytest
from api_wrappers import FlightSearch, HotelSearch, POISearch
from mock_client import MockTavilyClient

@pytest.fixture
def client():
    return MockTavilyClient()

def test_flight_nl_query_and_search(client):
    fs = FlightSearch(client)
    q = fs.build_nl_query(origin="London", destination="Paris", depart_date="2025-10-15", passengers=1)
    assert "List flights" in q
    results = fs.search(origin="London", destination="Paris", depart_date="2025-10-15", passengers=1)
    assert isinstance(results, list) and results

def test_hotels_nl(client):
    hs = HotelSearch(client)
    q = hs.build_nl_query(location="Paris", checkin="2025-10-15", checkout="2025-10-17", min_rating=3.0)
    assert "Search hotels" in q
    res = hs.search(location="Paris", checkin="2025-10-15", checkout="2025-10-17")
    assert isinstance(res, list) and res

def test_pois_nl(client):
    ps = POISearch(client)
    q = ps.build_nl_query(location="Paris", interests=["museum", "park"], radius_km=2.5)
    assert "Find points of interest" in q
    res = ps.search(location="Paris", interests=["museum", "park"])
    assert isinstance(res, list) and res
