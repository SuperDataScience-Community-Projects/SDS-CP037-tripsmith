import os
import streamlit as st
from datetime import date

from planner_agent_centralized import PlannerAgentCentralized

st.set_page_config(page_title="Travel Planner", page_icon="🗺️", layout="wide")

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
if not TAVILY_API_KEY:
    st.error("Missing TAVILY_API_KEY. Please set it in your Space Secrets.")
    st.stop()

planner = PlannerAgentCentralized(tavily_api_key=TAVILY_API_KEY)

st.title("Travel Planner")
st.caption("Powered by Streamlit on Hugging Face Spaces")

cities = [
    "New York", "Paris", "London", "Tokyo", "Sydney",
    "Rome", "Barcelona", "Dubai", "Singapore", "Cape Town",
    "Los Angeles", "Toronto", "Berlin", "Amsterdam", "Bangkok"
]

# Curated, smaller preference set
preference_options = [
    "Museums", "Food & Drink", "Outdoors", "Shopping", "Historic Sites"
]

currencies = ["USD", "EUR", "GBP", "CAD", "AUD", "ZAR"]

# Sidebar inputs
with st.sidebar:
    st.header("Plan your trip")
    destination = st.selectbox("Destination City", options=cities, index=1)
    c1, c2 = st.columns(2)
    with c1:
        start_date = st.date_input("Start Date", value=date.today())
    with c2:
        end_date = st.date_input("End Date", value=date.today())

    currency = st.selectbox("Currency", options=currencies, index=0)
    hotel_budget = st.number_input("Hotel Budget per Night", min_value=1, value=150, step=10)
    activity_budget = st.number_input("Activities Budget", min_value=0, value=300, step=25)

    prefs = st.multiselect("Preferences", options=preference_options, default=["Museums", "Food & Drink"]) 
    submitted = st.button("Plan Trip")

if submitted:
    if end_date < start_date:
        st.warning("End Date must be on or after Start Date.")
        st.stop()

    request = {
        "destination": destination,
        "departure_date": start_date.strftime("%Y-%m-%d"),
        "return_date": end_date.strftime("%Y-%m-%d"),
        "hotel_budget": hotel_budget,
        "activity_budget": activity_budget,
        "preferences": prefs,
    }

    with st.spinner("Planning your trip with Tavily..."):
        result = planner.process_request(request)

    if not result.get("success"):
        st.error(result.get("error", "Failed to create itinerary."))
        st.stop()

    itinerary = result["data"]
    reasoning = result.get("reasoning", {})

    # Right-side output
    col_main, _ = st.columns([3, 1])
    with col_main:
        # Budgets
        st.subheader("Budgets")
        b = itinerary.get("budgets", {})
        cA, cB = st.columns(2)
        with cA:
            st.metric("Hotel (per night)", f"{currency} {(hotel_budget):,.0f}")
        with cB:
            st.metric("Activities", f"{currency} {(b.get('activity_budget') or 0):,.0f}")

        # Hotels
        st.markdown("### 🏨 Hotels")
        hotels = itinerary.get("hotels", [])
        booking_site = itinerary.get("booking_site")
        if hotels:
            st.markdown("\n".join([f"- **{name}**" for name in hotels[:5]]))
            if booking_site:
                st.markdown(f"Book or compare at: [{booking_site}]({booking_site})")
        else:
            st.write("No hotels found.")

        # Daily Itinerary
        st.markdown("### 📅 Daily Itinerary")
        for day in itinerary.get("daily_itinerary", []):
            with st.expander(day.get("date", "Day")):
                for item in day.get("items", []):
                    time = item.get("time", "")
                    name = item.get("name", "Activity")
                    url = item.get("url")
                    st.markdown(f"- {time} — **{name}**")
                    if url:
                        st.caption(f"More info: {url}")

        # Notes
        st.markdown("### 🧠 Notes")
        st.write(f"- Hotels: {reasoning.get('hotel_agent','')}")
        st.write(f"- Activities: {reasoning.get('poi_agent','')}")