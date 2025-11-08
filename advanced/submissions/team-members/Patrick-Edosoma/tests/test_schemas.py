from datetime import date
from models import FlightOption, HotelOption, POI, Itinerary, DayPlan
import pytest




def test_hotel_validation():
with pytest.raises(ValueError):
HotelOption(
name="X", check_in=date(2025, 1, 10), check_out=date(2025, 1, 10), nightly_rate_usd=100, rating=4.0
)


def test_itinerary_hotel_coverage():
with pytest.raises(ValueError):
Itinerary(
origin="JFK",
destination="LAX",
start_date=date(2025, 1, 1),
end_date=date(2025, 1, 5),
hotels=[],
)