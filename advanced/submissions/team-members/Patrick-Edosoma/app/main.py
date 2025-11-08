import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.schemas import PlanRequest, PlanResponse
from app.core import plan_trip_core

load_dotenv(override=True)

app = FastAPI(title="TripSmith API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthz")
def health() -> dict:
    return {"status": "ok"}

@app.post("/plan", response_model=PlanResponse)
def plan(req: PlanRequest):
    if req.end_date <= req.start_date:
        raise HTTPException(status_code=400, detail="end_date must be after start_date")

    data = plan_trip_core(
        origin=req.origin.upper(),
        destination=req.destination.upper(),
        start_date=req.start_date,
        end_date=req.end_date,
        budget_per_night=req.budget_per_night,
        interests=req.interests,
    )
    return data
