"""
FastAPI application for the Facebook Marketplace vehicle scraper
and TikTok keyword scraper.
"""

import logging
from typing import Optional

from fastapi import FastAPI, HTTPException

from models import ScrapeRequest, ScrapeResponse, TikTokScrapeRequest, TikTokScrapeResponse
from scraper import scrape_vehicles
from tiktok_scraper import scrape_tiktok

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


# ── TikTok endpoints ──────────────────────────────────────────────────────────


@app.post(
    "/tiktok/scrape",
    response_model=TikTokScrapeResponse,
    summary="Scrape TikTok videos by keyword",
)
def tiktok_scrape(request: TikTokScrapeRequest):
    """
    Scrape TikTok for videos matching a keyword (e.g. *abilify*).

    - **keyword**: Search term (default `abilify`)
    - **max_results**: Maximum number of videos to return (default 20)
    """
    try:
        result = scrape_tiktok(request)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get(
    "/tiktok/scrape",
    response_model=TikTokScrapeResponse,
    summary="Scrape TikTok videos by keyword (GET)",
)
def tiktok_scrape_get(keyword: str = "abilify", max_results: int = 20):
    """Convenience GET endpoint — same behavior as the POST endpoint."""
    request = TikTokScrapeRequest(keyword=keyword, max_results=max_results)
    try:
        result = scrape_tiktok(request)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
