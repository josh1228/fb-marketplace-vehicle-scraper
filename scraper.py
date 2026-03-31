"""
Facebook Marketplace vehicle scraper (educational implementation).

Note: Facebook Marketplace requires authentication and uses dynamic content
loaded via JavaScript. This module demonstrates the scraping approach using
requests and BeautifulSoup4. In practice, a headless browser (e.g. Playwright
or Selenium) would be needed for full functionality.
"""

import time
import logging
from typing import Optional

import requests
from bs4 import BeautifulSoup

import config
from models import VehicleListing

logger = logging.getLogger(__name__)

BASE_URL = "https://www.facebook.com/marketplace/{location}/vehicles"

HEADERS = {
    "User-Agent": config.USER_AGENT,
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _build_url(location: str, query: str) -> str:
    """Build the Facebook Marketplace search URL."""
    return f"{BASE_URL.format(location=location)}?query={requests.utils.quote(query)}"


def _parse_listing(card) -> Optional[VehicleListing]:
    """Parse a single listing card element into a VehicleListing."""
    try:
        listing_id = card.get("data-listing-id") or card.get("id") or ""
        title_el = card.select_one("[data-testid='marketplace-item-title'], .x1lliihq")
        title = title_el.get_text(strip=True) if title_el else "Unknown"

        price_el = card.select_one("[data-testid='marketplace-item-price'], .x193iq5w")
        price = price_el.get_text(strip=True) if price_el else None

        location_el = card.select_one("[data-testid='marketplace-item-location']")
        location = location_el.get_text(strip=True) if location_el else None

        image_el = card.select_one("img")
        image_url = image_el.get("src") if image_el else None

        link_el = card.select_one("a[href*='/marketplace/item/']")
        listing_url = None
        if link_el:
            href = link_el.get("href", "")
            listing_url = href if href.startswith("http") else f"https://www.facebook.com{href}"

        return VehicleListing(
            listing_id=listing_id,
            title=title,
            price=price,
            location=location,
            image_url=image_url,
            listing_url=listing_url,
        )
    except Exception as exc:
        logger.warning("Failed to parse listing card: %s", exc)
        return None


def scrape_listings(location: str, query: str = "vehicles", max_results: int = 20) -> list[VehicleListing]:
    """
    Scrape vehicle listings from Facebook Marketplace.

    Args:
        location: City or ZIP code to search in.
        query: Search query string (default: "vehicles").
        max_results: Maximum number of listings to return.

    Returns:
        A list of VehicleListing objects.
    """
    url = _build_url(location, query)
    listings: list[VehicleListing] = []

    for attempt in range(1, config.SCRAPER_RETRIES + 1):
        try:
            logger.info("Fetching listings from %s (attempt %d/%d)", url, attempt, config.SCRAPER_RETRIES)
            response = requests.get(
                url,
                headers=HEADERS,
                timeout=config.SCRAPER_TIMEOUT,
            )
            response.raise_for_status()
            break
        except requests.RequestException as exc:
            logger.warning("Request failed on attempt %d: %s", attempt, exc)
            if attempt < config.SCRAPER_RETRIES:
                time.sleep(2 ** attempt)
            else:
                raise

    soup = BeautifulSoup(response.text, "html.parser")

    # Facebook Marketplace renders most content via JS; this selector targets
    # server-rendered listing cards where available.
    cards = soup.select(
        "[data-testid='marketplace-search-feed-item'], "
        "div[class*='x3ct3a4'], "
        "div[data-pagelet*='MarketplaceItem']"
    )

    logger.info("Found %d raw listing cards", len(cards))

    for card in cards[:max_results]:
        listing = _parse_listing(card)
        if listing:
            listings.append(listing)
        time.sleep(1.0 / config.SCRAPER_RATE_LIMIT)

    return listings
