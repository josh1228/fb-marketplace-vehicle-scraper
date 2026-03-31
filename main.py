"""
FastAPI application for the Facebook Marketplace vehicle scraper
and the Zillow / Redfin / Realtor.com real-estate scrapers.
"""

import logging
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException

from models import RealEstateRequest, RealEstateResponse, ScrapeRequest, ScrapeResponse
from real_estate_scraper import scrape_real_estate
from scraper import scrape_vehicles

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Vehicle & Real-Estate Scraper",
    description=(
        "Educational API that scrapes vehicle listings from Facebook Marketplace "
        "and real-estate listings from Zillow, Redfin, and Realtor.com. "
        "Ensure compliance with each platform's Terms of Service before use."
    ),
    version="2.0.0",
)


@app.get("/", summary="Health check")
def root():
    return {"status": "ok", "message": "FB Marketplace Vehicle Scraper is running."}


@app.post("/scrape", response_model=ScrapeResponse, summary="Scrape vehicle listings")
def scrape(request: ScrapeRequest):
    """
    Scrape Facebook Marketplace for vehicle listings.

    - **location**: Marketplace location slug (e.g. `new-york-ny`)
    - **vehicle_type**: Category slug (e.g. `cars-trucks`, `motorcycles`)
    - **min_price** / **max_price**: Optional price filters (USD)
    - **max_mileage**: Optional maximum mileage filter
    - **max_results**: Maximum number of listings to return (default 20)
    """
    try:
        result = scrape_vehicles(request)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get(
    "/scrape",
    response_model=ScrapeResponse,
    summary="Scrape vehicle listings (GET)",
)
def scrape_get(
    location: str = "new-york-ny",
    vehicle_type: str = "cars-trucks",
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    max_mileage: Optional[int] = None,
    max_results: int = 20,
):
    """Convenience GET endpoint — same behavior as the POST endpoint."""
    request = ScrapeRequest(
        location=location,
        vehicle_type=vehicle_type,
        min_price=min_price,
        max_price=max_price,
        max_mileage=max_mileage,
        max_results=max_results,
    )
    try:
        result = scrape_vehicles(request)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Real-estate endpoints (Zillow / Redfin / Realtor.com)
# ---------------------------------------------------------------------------


@app.post(
    "/real-estate/scrape",
    response_model=RealEstateResponse,
    summary="Scrape real-estate listings",
    tags=["Real Estate"],
)
def scrape_real_estate_post(request: RealEstateRequest):
    """
    Scrape real-estate listings from Zillow, Redfin, and/or Realtor.com.

    - **location**: City and state (e.g. `New York, NY`)
    - **min_price** / **max_price**: Optional price filters (USD)
    - **min_beds** / **max_beds**: Optional bedroom filters
    - **property_type**: Optional property type (e.g. `house`, `condo`, `townhouse`)
    - **max_results**: Maximum number of listings to return (default 20)
    - **source**: Data source — `zillow`, `redfin`, `realtor`, or `all` (default `all`)
    """
    try:
        result = scrape_real_estate(request)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get(
    "/real-estate/scrape",
    response_model=RealEstateResponse,
    summary="Scrape real-estate listings (GET)",
    tags=["Real Estate"],
)
def scrape_real_estate_get(
    location: str = "New York, NY",
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    min_beds: Optional[int] = None,
    max_beds: Optional[int] = None,
    property_type: Optional[str] = None,
    max_results: int = 20,
    source: Literal["zillow", "redfin", "realtor", "all"] = "all",
):
    """Convenience GET endpoint — same behavior as the POST endpoint."""
    request = RealEstateRequest(
        location=location,
        min_price=min_price,
        max_price=max_price,
        min_beds=min_beds,
        max_beds=max_beds,
        property_type=property_type,
        max_results=max_results,
        source=source,
    )
    try:
        result = scrape_real_estate(request)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
