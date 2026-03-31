import logging

from fastapi import FastAPI, HTTPException

import config
from models import ScrapeRequest, ScrapeResponse
from scraper import scrape_listings

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="FB Marketplace Vehicle Scraper",
    description="Educational scraper for Facebook Marketplace vehicle listings.",
    version="1.0.0",
)


@app.get("/health")
def health_check():
    """Health-check endpoint."""
    return {"status": "ok"}


@app.post("/scrape", response_model=ScrapeResponse)
def scrape(request: ScrapeRequest):
    """
    Scrape vehicle listings from Facebook Marketplace.

    - **location**: city name or ZIP code to search
    - **query**: search keywords (default: "vehicles")
    - **max_results**: maximum listings to return (default: 20)
    """
    if request.max_results < 1 or request.max_results > 100:
        raise HTTPException(status_code=400, detail="max_results must be between 1 and 100")

    try:
        listings = scrape_listings(
            location=request.location,
            query=request.query,
            max_results=request.max_results,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Scraping failed: {exc}") from exc

    return ScrapeResponse(
        listings=listings,
        total=len(listings),
        location=request.location,
        query=request.query,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=False,
    )
