import os
import requests
from dotenv import load_dotenv
from api_wrappers import FlightSearch, HotelSearch, POISearch

load_dotenv()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not TAVILY_API_KEY:
    raise RuntimeError("Set TAVILY_API_KEY in your environment for live test")

BASE_URL = "https://api.tavily.com/search"   # adjust if needed
HEADERS = {"Authorization": f"Bearer {TAVILY_API_KEY}", "Content-Type": "application/json"}

class LiveClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def request(self, endpoint: str, payload: dict):
        url = self.base_url  # Tavily uses single POST /search typically
        r = requests.post(url, json=payload, headers=HEADERS)
        r.raise_for_status()
        return r.json()

