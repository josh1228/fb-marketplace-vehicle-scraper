"""
FastAPI application for the Facebook Marketplace vehicle scraper
and TikTok keyword scraper.
"""

import logging
from typing import Optional

from fastapi import FastAPI, HTTPException

from models import (
    ScrapeRequest,
    ScrapeResponse,
    TikTokHashtagRequest,
    TikTokScrapeRequest,
    TikTokScrapeResponse,
    TikTokUserRequest,
)
from scraper import scrape_vehicles
from tiktok_scraper import (
    scrape_tiktok,
    scrape_tiktok_hashtag,
    scrape_tiktok_trending,
    scrape_tiktok_user,
)

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
async def tiktok_scrape(request: TikTokScrapeRequest):
    """
    Scrape TikTok for videos matching a keyword (e.g. *abilify*).

    - **keyword**: Search term (default `abilify`)
    - **max_results**: Maximum number of videos to return (default 20)

    **Note:** This endpoint uses TikTok's general search and requires a valid
    `TIKTOK_MS_TOKEN` with prior search history.  For most use-cases the
    `/tiktok/hashtag` endpoint is more reliable.
    """
    try:
        result = await scrape_tiktok(request)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get(
    "/tiktok/scrape",
    response_model=TikTokScrapeResponse,
    summary="Scrape TikTok videos by keyword (GET)",
)
async def tiktok_scrape_get(keyword: str = "abilify", max_results: int = 20):
    """Convenience GET endpoint — same behavior as the POST endpoint."""
    request = TikTokScrapeRequest(keyword=keyword, max_results=max_results)
    try:
        result = await scrape_tiktok(request)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post(
    "/tiktok/hashtag",
    response_model=TikTokScrapeResponse,
    summary="Scrape TikTok videos by hashtag",
)
async def tiktok_hashtag(request: TikTokHashtagRequest):
    """
    Scrape TikTok for videos tagged with a hashtag (e.g. *#abilify*).

    This is the **recommended** endpoint for Abilify content — it does not
    require an authenticated ms_token and is more reliable than keyword search.

    - **hashtag**: Hashtag name without the `#` (default `abilify`)
    - **max_results**: Maximum number of videos to return (default 20)
    """
    try:
        result = await scrape_tiktok_hashtag(request)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get(
    "/tiktok/hashtag",
    response_model=TikTokScrapeResponse,
    summary="Scrape TikTok videos by hashtag (GET)",
)
async def tiktok_hashtag_get(hashtag: str = "abilify", max_results: int = 20):
    """Convenience GET endpoint — same behavior as the POST endpoint."""
    request = TikTokHashtagRequest(hashtag=hashtag, max_results=max_results)
    try:
        result = await scrape_tiktok_hashtag(request)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post(
    "/tiktok/user",
    response_model=TikTokScrapeResponse,
    summary="Scrape a TikTok user's videos",
)
async def tiktok_user(request: TikTokUserRequest):
    """
    Scrape videos posted by a specific TikTok user.

    - **username**: TikTok username (without the `@`)
    - **max_results**: Maximum number of videos to return (default 20)
    """
    try:
        result = await scrape_tiktok_user(request)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get(
    "/tiktok/user",
    response_model=TikTokScrapeResponse,
    summary="Scrape a TikTok user's videos (GET)",
)
async def tiktok_user_get(username: str, max_results: int = 20):
    """Convenience GET endpoint — same behavior as the POST endpoint."""
    request = TikTokUserRequest(username=username, max_results=max_results)
    try:
        result = await scrape_tiktok_user(request)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get(
    "/tiktok/trending",
    response_model=TikTokScrapeResponse,
    summary="Scrape TikTok trending / For-You feed videos",
)
async def tiktok_trending(max_results: int = 30):
    """
    Scrape TikTok's current trending (For-You feed) videos.

    Does not require an authenticated ms_token.

    - **max_results**: Maximum number of videos to return (default 30)
    """
    try:
        result = await scrape_tiktok_trending(max_results=max_results)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
