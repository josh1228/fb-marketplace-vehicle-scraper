"""
Facebook Marketplace vehicle scraper.

NOTE: This module is provided for **educational purposes only**.
Scraping Facebook Marketplace may violate Facebook's Terms of Service.
Always review and comply with the platform's terms before use.
"""

import logging
import re
import time
from typing import Optional
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

from config import (
    SCRAPER_RATE_LIMIT,
    SCRAPER_RETRIES,
    SCRAPER_TIMEOUT,
    USER_AGENT,
)
from models import ScrapeRequest, ScrapeResponse, VehicleListing

logger = logging.getLogger(__name__)

BASE_URL = "https://www.facebook.com/marketplace"


def _build_url(request: ScrapeRequest) -> str:
    """Build the Facebook Marketplace search URL from a ScrapeRequest."""
    path = f"{BASE_URL}/{request.location}/{request.vehicle_type}/"
    params: dict[str, str] = {}
    if request.min_price is not None:
        params["minPrice"] = str(request.min_price)
    if request.max_price is not None:
        params["maxPrice"] = str(request.max_price)
    if request.max_mileage is not None:
        params["maxMileage"] = str(request.max_mileage)
    return f"{path}?{urlencode(params)}" if params else path


def _parse_listing(card) -> Optional[VehicleListing]:
    """Extract vehicle data from a single listing card element."""
    try:
        title_el = card.find(attrs={"aria-label": True})
        title = title_el["aria-label"] if title_el else ""
        if not title:
            span = card.find("span", class_=re.compile(r".*"))
            title = span.get_text(strip=True) if span else "Unknown"

        price_el = card.find(string=re.compile(r"\$[\d,]+"))
        price = price_el.strip() if price_el else None

        spans = card.find_all("span")
        location = None
        for span in spans:
            text = span.get_text(strip=True)
            if "," in text and len(text) < 50:
                location = text
                break

        img_el = card.find("img")
        image_url = img_el.get("src") if img_el else None

        link_el = card.find("a", href=True)
        listing_url = None
        listing_id = None
        if link_el:
            href = link_el["href"]
            if not href.startswith("http"):
                href = f"https://www.facebook.com{href}"
            listing_url = href
            match = re.search(r"/item/(\d+)", href)
            if match:
                listing_id = match.group(1)

        year_match = re.search(r"\b(19|20)\d{2}\b", title)
        year = year_match.group(0) if year_match else None

        return VehicleListing(
            listing_id=listing_id,
            title=title,
            price=price,
            location=location,
            year=year,
            image_url=image_url,
            listing_url=listing_url,
        )
    except Exception as exc:
        logger.warning("Failed to parse listing card: %s", exc)
        return None


def _fetch_page(url: str, session: requests.Session) -> Optional[str]:
    """Fetch a page with retry logic, respecting the configured rate limit."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    for attempt in range(1, SCRAPER_RETRIES + 1):
        try:
            # Respect rate limit before each request (requests per minute → seconds gap)
            if SCRAPER_RATE_LIMIT > 0:
                time.sleep(60.0 / SCRAPER_RATE_LIMIT)
            response = session.get(url, headers=headers, timeout=SCRAPER_TIMEOUT)
            response.raise_for_status()
            return response.text
        except requests.RequestException as exc:
            logger.warning("Attempt %d/%d failed for %s: %s", attempt, SCRAPER_RETRIES, url, exc)
            if attempt < SCRAPER_RETRIES:
                time.sleep(2 ** attempt)
    return None


def scrape_vehicles(request: ScrapeRequest) -> ScrapeResponse:
    """
    Scrape vehicle listings from Facebook Marketplace.

    Returns a ScrapeResponse containing parsed VehicleListing objects.
    """
    url = _build_url(request)
    logger.info("Scraping URL: %s", url)

    with requests.Session() as session:
        html = _fetch_page(url, session)

    if html is None:
        return ScrapeResponse(
            success=False,
            count=0,
            listings=[],
            message="Failed to fetch page after retries.",
        )

    soup = BeautifulSoup(html, "html.parser")

    # Facebook Marketplace renders via React; look for listing cards by common patterns.
    cards = soup.find_all("div", attrs={"data-testid": re.compile(r"(?i)listing|marketplace")})
    if not cards:
        cards = soup.find_all("a", href=re.compile(r"/marketplace/item/"))
        cards = [c.parent for c in cards if c.parent]

    listings: list[VehicleListing] = []
    for card in cards[: request.max_results]:
        listing = _parse_listing(card)
        if listing:
            listings.append(listing)

    logger.info("Scraped %d listings", len(listings))
    return ScrapeResponse(
        success=True,
        count=len(listings),
        listings=listings,
        message=None,
    )
