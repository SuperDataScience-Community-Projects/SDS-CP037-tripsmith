# TripSmith — Multi-Agent Travel Planner

End-to-end travel planning with multi-agent orchestration, FastAPI, Streamlit, and Gradio. TripSmith finds flights, surfaces hotels, suggests POIs, builds a daily plan, and estimates total cost — all wrapped in typed models and clean APIs.

## 🚀 Live:

API (FastAPI on Render): https://tripsmith.onrender.com

Streamlit UI: https://tripsmith-okjv4n7ij6aappdtq7gqwzw.streamlit.app

# 💼 Business Statement

TripSmith is a proof-of-concept for how multi-agent systems can transform the travel industry by:

1. Reducing friction: Centralizing the process of finding flights, hotels, and activities in one tool.

2. Personalization at scale: Matching itineraries to user preferences (e.g., museum, food, adventure) with reasoning from LLMs like Gemini.

3. Cost transparency: Providing estimated budgets upfront to aid decision-making.

4. Developer extensibility: Built modularly, allowing future integrations (multi-city trips, loyalty program tie-ins, group planning).

While TripSmith currently runs on free-tier APIs and has limitations, it demonstrates a scalable foundation for a SaaS-style product where paid APIs and premium tiers could deliver 

real-time availability, booking integrations, and deeper personalization.


#  Objectivive

The objective of TripSmith is to simplify end-to-end travel planning by combining multiple intelligent agents into one cohesive system. Instead of searching flights, hotels, and activities separately across different platforms, users can input their trip details and receive a complete personalized itinerary — including flights, hotels, daily activities, and cost estimates — in just one request.

The project also serves as a practical milestone in applied AI/ML engineering, showcasing how APIs, LLMs, and orchestration can be combined with modern deployment tools like Docker, FastAPI, and Streamlit.

# Features

✈️ Flight search (Amadeus Flights)

🏨 Hotel search (Amadeus Hotels and/or SerpAPI Google Hotels; Bluepillow/SerpAPI fallback)

🗺️ POIs (Tavily/SerpAPI; city/country disambiguation)

🧭 Daily plan (balanced activities + free time)

💵 Cost estimate (flight + hotel + POI costs)

🌍 IATA normalization and city/country resolution from data/airports.csv

📅 International date formatting with country-aware display


# Architecture

```bash
├─ app/                 # FastAPI app (main API)
│  └─ main.py
├─ controller/
│  └─ planner.py        # Orchestrates agents → itinerary
├─ agents/
│  ├─ flight_agent.py
│  ├─ hotel_agent.py
│  └─ poi_agent.py
├─ utils/
│  ├─ airports.py       # IATA <-> City, Country mapping (airports.csv)
│  └─ search_providers.py
├─ data/
│  └─ airports.csv      # Global airport dataset (IATA, city, country)
├─ models.py            # Pydantic models (FlightOption, HotelOption...)
├─ app_streamlit.py     # Streamlit UI
├─ app_gradio.py        # Gradio UI
├─ requirements.txt
└─ Dockerfile
```

# Tech Stack

• Backend: FastAPI, Uvicorn

• Front-end UIs: Streamlit, Gradio

• Agents: Lightweight, goal-directed Python classes

• LLM: Google Gemini API for reasoning/planning

• Validation: Pydantic v2

• Infra: Docker, Docker Hub

• Hosting: Render (API), Streamlit Cloud (UI)

# Data Sources & APIs

• Amadeus (Flights + Hotels) — real inventories (free tier; limited)

• SerpAPI (Google Hotels + web results) — hotel/POI parsing

• Tavily — POI discovery

• Airports CSV — IATA ↔ City,Country disambiguation

• Gemini API — chain-of-thought/reasoning support for planning

# Quickstart
1) Local (Python)
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Copy and fill your environment variables
cp .env.example .env   # or create .env (see below)

# Run API
uvicorn app.main:app --reload --port 8080
# Open: http://localhost:8080  |  Swagger: http://localhost:8080/docs

# Streamlit UI
streamlit run app_streamlit.py

# Gradio UI
python app_gradio.py
```

2. Docker (amd64 for Render)
   
   Render requires linux/amd64 images:
```bash
   # Build multi-arch (or amd64 on Apple Silicon)
docker buildx create --use --name tripsmithx || true
docker buildx build --platform linux/amd64 -t YOUR_DOCKERHUBname/tripsmith:latest --push .
```

# Configuration (.env)
```bash
AMADEUS_API_KEY=...
AMADEUS_API_SECRET=...

SERPAPI_API_KEY=...
TAVILY_API_KEY=...

GEMINI_API_KEY=...

```

# Limitations

• Free tier APIs: Amadeus, SerpAPI, Tavily, etc., may rate limit or return partial results.
The app gracefully falls back to mocks to keep demos stable.

• Hotel prices/links: parsers rely on provider payloads; some fields (e.g., price per night) may be missing and are filtered/sanitized.

• Flights: if Amadeus rejects parameters (e.g., inverted dates), the planner will fall back to mock flight options.

# 📬 Contact
Patrick Edosoma

Machine Learning Engineer

[Linkedlin](https://www.linkedin.com/in/patrickedosoma/)

# ⭐️ Star This Repo
If you found this project helpful, please star ⭐️ it to show support!



