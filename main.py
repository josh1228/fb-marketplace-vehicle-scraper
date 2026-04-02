"""
FastAPI application for the Facebook Marketplace vehicle scraper.
"""

import logging
from typing import Optional

from fastapi import FastAPI, HTTPException

from models import ScrapeRequest, ScrapeResponse
from scraper import scrape_vehicles

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="FB Marketplace Vehicle Scraper",
    description=(
        "Educational API that scrapes vehicle listings from Facebook Marketplace. "
        "Ensure compliance with Facebook's Terms of Service before use."
    ),
    version="1.0.0",
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
    - **analyze_deals**: Score listings and flag good deals (default `true`)
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
    analyze_deals: bool = True,
):
    """Convenience GET endpoint — same behavior as the POST endpoint."""
    request = ScrapeRequest(
        location=location,
        vehicle_type=vehicle_type,
        min_price=min_price,
        max_price=max_price,
        max_mileage=max_mileage,
        max_results=max_results,
        analyze_deals=analyze_deals,
    )
    try:
        result = scrape_vehicles(request)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def _good_deals_from_request(request: ScrapeRequest) -> ScrapeResponse:
    """Run scrape with deal analysis and return only the good-deal listings."""
    request.analyze_deals = True
    result = scrape_vehicles(request)
    good = [l for l in result.listings if l.is_good_deal]
    good.sort(key=lambda l: l.deal_score or 0.0, reverse=True)
    return ScrapeResponse(
        success=result.success,
        count=len(good),
        listings=good,
        message=result.message,
    )


@app.post("/deals", response_model=ScrapeResponse, summary="Find good deals on vehicles")
def deals(request: ScrapeRequest):
    """
    Scrape Facebook Marketplace and return **only** listings flagged as good deals.

    Listings are scored with a heuristic that weighs price (60 %), model year (25 %),
    and mileage (15 %) and sorted by ``deal_score`` descending.

    Accepts the same parameters as `POST /scrape`.  Deal analysis is always enabled.
    """
    try:
        return _good_deals_from_request(request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/deals", response_model=ScrapeResponse, summary="Find good deals on vehicles (GET)")
def deals_get(
    location: str = "new-york-ny",
    vehicle_type: str = "cars-trucks",
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    max_mileage: Optional[int] = None,
    max_results: int = 20,
):
    """Convenience GET endpoint — same behavior as `POST /deals`."""
    request = ScrapeRequest(
        location=location,
        vehicle_type=vehicle_type,
        min_price=min_price,
        max_price=max_price,
        max_mileage=max_mileage,
        max_results=max_results,
        analyze_deals=True,
    )
    try:
        return _good_deals_from_request(request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

