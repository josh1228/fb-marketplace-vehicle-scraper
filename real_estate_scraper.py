"""
Real-estate scrapers for Zillow, Redfin, and Realtor.com.

NOTE: This module is provided for **educational purposes only**.
Scraping these platforms may violate their Terms of Service.
Always review and comply with each platform's terms before use.
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
from models import PropertyListing, RealEstateRequest, RealEstateResponse

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Base URLs
# ---------------------------------------------------------------------------

ZILLOW_BASE = "https://www.zillow.com"
REDFIN_BASE = "https://www.redfin.com"
REALTOR_BASE = "https://www.realtor.com"


# ---------------------------------------------------------------------------
# Shared HTTP helpers (mirrors scraper.py)
# ---------------------------------------------------------------------------


def _fetch_page(url: str, session: requests.Session) -> Optional[str]:
    """Fetch a page with retry logic, respecting the configured rate limit."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    for attempt in range(1, SCRAPER_RETRIES + 1):
        try:
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


# ---------------------------------------------------------------------------
# Zillow
# ---------------------------------------------------------------------------


def _build_zillow_url(request: RealEstateRequest) -> str:
    """Build a Zillow search URL from a RealEstateRequest."""
    # Zillow uses slug-style location in the path: e.g. /new-york-ny/
    location_slug = request.location.lower().replace(", ", "-").replace(" ", "-")
    path = f"{ZILLOW_BASE}/{location_slug}/"
    params: dict[str, str] = {}
    if request.min_price is not None:
        params["price_min"] = str(request.min_price)
    if request.max_price is not None:
        params["price_max"] = str(request.max_price)
    if request.min_beds is not None:
        params["beds_min"] = str(request.min_beds)
    if request.max_beds is not None:
        params["beds_max"] = str(request.max_beds)
    if request.property_type:
        params["home_type"] = request.property_type
    return f"{path}?{urlencode(params)}" if params else path


def _parse_zillow_card(card) -> Optional[PropertyListing]:
    """Extract property data from a single Zillow listing card."""
    try:
        # Address
        address_el = card.find(attrs={"data-test": "property-card-addr"})
        if not address_el:
            address_el = card.find("address")
        address = address_el.get_text(strip=True) if address_el else None

        # Price
        price_el = card.find(attrs={"data-test": "property-card-price"})
        if not price_el:
            price_el = card.find(string=re.compile(r"\$[\d,]+"))
        price = price_el.get_text(strip=True) if hasattr(price_el, "get_text") else (
            price_el.strip() if price_el else None
        )

        # Beds / Baths / Sqft
        beds = baths = sqft = None
        details_el = card.find(attrs={"data-test": "property-card-details"})
        if details_el:
            texts = [li.get_text(strip=True) for li in details_el.find_all("li")]
            for t in texts:
                if re.search(r"\bbds?\b|\bbeds?\b", t, re.IGNORECASE):
                    beds = re.search(r"[\d.]+", t)
                    beds = beds.group(0) if beds else None
                elif re.search(r"\bbas?\b|\bbaths?\b", t, re.IGNORECASE):
                    baths = re.search(r"[\d.]+", t)
                    baths = baths.group(0) if baths else None
                elif re.search(r"sqft|sq\s*ft", t, re.IGNORECASE):
                    sqft = re.search(r"[\d,]+", t)
                    sqft = sqft.group(0) if sqft else None

        # Image
        img_el = card.find("img")
        image_url = img_el.get("src") if img_el else None

        # Link / ID
        link_el = card.find("a", href=True)
        listing_url = listing_id = None
        if link_el:
            href = link_el["href"]
            if not href.startswith("http"):
                href = f"{ZILLOW_BASE}{href}"
            listing_url = href
            id_match = re.search(r"_zpid", href) or re.search(r"/(\d+)_zpid", href)
            if id_match:
                m = re.search(r"/(\d+)_zpid", href)
                listing_id = m.group(1) if m else None

        return PropertyListing(
            listing_id=listing_id,
            address=address,
            price=price,
            beds=beds,
            baths=baths,
            sqft=sqft,
            image_url=image_url,
            listing_url=listing_url,
            source="zillow",
        )
    except Exception as exc:
        logger.warning("Failed to parse Zillow card: %s", exc)
        return None


def scrape_zillow(request: RealEstateRequest) -> list[PropertyListing]:
    """Scrape property listings from Zillow."""
    url = _build_zillow_url(request)
    logger.info("Scraping Zillow URL: %s", url)

    with requests.Session() as session:
        html = _fetch_page(url, session)

    if not html:
        logger.warning("Zillow: failed to fetch page")
        return []

    soup = BeautifulSoup(html, "html.parser")

    cards = soup.find_all("article", attrs={"data-test": "property-card"})
    if not cards:
        # Fallback: look for list items containing property links
        cards = soup.find_all("li", class_=re.compile(r"(?i)result|card|listing"))
    if not cards:
        cards = soup.find_all("a", href=re.compile(r"_zpid"))
        cards = [c.parent for c in cards if c.parent]

    listings: list[PropertyListing] = []
    for card in cards[: request.max_results]:
        listing = _parse_zillow_card(card)
        if listing:
            listings.append(listing)

    logger.info("Zillow: scraped %d listings", len(listings))
    return listings


# ---------------------------------------------------------------------------
# Redfin
# ---------------------------------------------------------------------------


def _build_redfin_url(request: RealEstateRequest) -> str:
    """Build a Redfin search URL from a RealEstateRequest."""
    path = f"{REDFIN_BASE}/city/search"
    params: dict[str, str] = {"location": request.location}
    if request.min_price is not None:
        params["min_price"] = str(request.min_price)
    if request.max_price is not None:
        params["max_price"] = str(request.max_price)
    if request.min_beds is not None:
        params["num_beds"] = str(request.min_beds)
    if request.property_type:
        params["property_type"] = request.property_type
    return f"{path}?{urlencode(params)}"


def _parse_redfin_card(card) -> Optional[PropertyListing]:
    """Extract property data from a single Redfin listing card."""
    try:
        # Address
        address_el = card.find(class_=re.compile(r"(?i)address|streetLine"))
        address = address_el.get_text(strip=True) if address_el else None

        # Price
        price_el = card.find(class_=re.compile(r"(?i)price|listPrice"))
        price = price_el.get_text(strip=True) if price_el else None
        if not price:
            price_raw = card.find(string=re.compile(r"\$[\d,]+"))
            price = price_raw.strip() if price_raw else None

        # Stats row (beds / baths / sqft)
        beds = baths = sqft = None
        stat_els = card.find_all(class_=re.compile(r"(?i)stat|amenity|beds|baths|sqft"))
        for el in stat_els:
            text = el.get_text(strip=True)
            if re.search(r"bed", text, re.IGNORECASE):
                m = re.search(r"[\d.]+", text)
                beds = m.group(0) if m else None
            elif re.search(r"bath", text, re.IGNORECASE):
                m = re.search(r"[\d.]+", text)
                baths = m.group(0) if m else None
            elif re.search(r"sq\s*ft|sqft", text, re.IGNORECASE):
                m = re.search(r"[\d,]+", text)
                sqft = m.group(0) if m else None

        # Image
        img_el = card.find("img")
        image_url = img_el.get("src") if img_el else None

        # Link / ID
        link_el = card.find("a", href=True)
        listing_url = listing_id = None
        if link_el:
            href = link_el["href"]
            if not href.startswith("http"):
                href = f"{REDFIN_BASE}{href}"
            listing_url = href
            m = re.search(r"/(\d+)$", href.rstrip("/"))
            listing_id = m.group(1) if m else None

        return PropertyListing(
            listing_id=listing_id,
            address=address,
            price=price,
            beds=beds,
            baths=baths,
            sqft=sqft,
            image_url=image_url,
            listing_url=listing_url,
            source="redfin",
        )
    except Exception as exc:
        logger.warning("Failed to parse Redfin card: %s", exc)
        return None


def scrape_redfin(request: RealEstateRequest) -> list[PropertyListing]:
    """Scrape property listings from Redfin."""
    url = _build_redfin_url(request)
    logger.info("Scraping Redfin URL: %s", url)

    with requests.Session() as session:
        html = _fetch_page(url, session)

    if not html:
        logger.warning("Redfin: failed to fetch page")
        return []

    soup = BeautifulSoup(html, "html.parser")

    cards = soup.find_all("div", class_=re.compile(r"(?i)HomeCard|homeCard|listing-card"))
    if not cards:
        cards = soup.find_all("div", attrs={"data-rf-test-id": re.compile(r"(?i)listing|card")})
    if not cards:
        cards = soup.find_all("a", href=re.compile(r"/home/"))
        cards = [c.parent for c in cards if c.parent]

    listings: list[PropertyListing] = []
    for card in cards[: request.max_results]:
        listing = _parse_redfin_card(card)
        if listing:
            listings.append(listing)

    logger.info("Redfin: scraped %d listings", len(listings))
    return listings


# ---------------------------------------------------------------------------
# Realtor.com
# ---------------------------------------------------------------------------


def _build_realtor_url(request: RealEstateRequest) -> str:
    """Build a Realtor.com search URL from a RealEstateRequest."""
    # Realtor.com uses slug like city_state: "new-york_ny"
    location_slug = (
        request.location.lower()
        .replace(", ", "_")
        .replace(",", "_")
        .replace(" ", "-")
    )
    path = f"{REALTOR_BASE}/realestateandhomes-search/{location_slug}"
    params: dict[str, str] = {}
    if request.min_price is not None:
        params["price-min"] = str(request.min_price)
    if request.max_price is not None:
        params["price-max"] = str(request.max_price)
    if request.min_beds is not None:
        params["beds-min"] = str(request.min_beds)
    if request.max_beds is not None:
        params["beds-max"] = str(request.max_beds)
    if request.property_type:
        params["prop-type"] = request.property_type
    return f"{path}?{urlencode(params)}" if params else path


def _parse_realtor_card(card) -> Optional[PropertyListing]:
    """Extract property data from a single Realtor.com listing card."""
    try:
        # Address
        address_el = card.find(attrs={"data-testid": "card-address"})
        if not address_el:
            address_el = card.find(class_=re.compile(r"(?i)address|truncate"))
        address = address_el.get_text(strip=True) if address_el else None

        # Price
        price_el = card.find(attrs={"data-testid": "card-price"})
        if not price_el:
            price_el = card.find(string=re.compile(r"\$[\d,]+"))
        price = price_el.get_text(strip=True) if hasattr(price_el, "get_text") else (
            price_el.strip() if price_el else None
        )

        # Beds / baths / sqft
        beds = baths = sqft = None
        meta_items = card.find_all(attrs={"data-testid": re.compile(r"(?i)bed|bath|sqft|area")})
        for item in meta_items:
            label = item.get("data-testid", "")
            value = item.get_text(strip=True)
            if "bed" in label.lower():
                beds = re.sub(r"[^\d.]", "", value) or None
            elif "bath" in label.lower():
                baths = re.sub(r"[^\d.]", "", value) or None
            elif "sqft" in label.lower() or "area" in label.lower():
                sqft = re.sub(r"[^\d,]", "", value) or None

        if not (beds or baths):
            # Fallback: parse list items
            for li in card.find_all("li"):
                text = li.get_text(strip=True)
                if re.search(r"\bbd\b|\bbed", text, re.IGNORECASE) and not beds:
                    m = re.search(r"[\d.]+", text)
                    beds = m.group(0) if m else None
                elif re.search(r"\bba\b|\bbath", text, re.IGNORECASE) and not baths:
                    m = re.search(r"[\d.]+", text)
                    baths = m.group(0) if m else None
                elif re.search(r"sq\s*ft|sqft", text, re.IGNORECASE) and not sqft:
                    m = re.search(r"[\d,]+", text)
                    sqft = m.group(0) if m else None

        # Image
        img_el = card.find("img")
        image_url = img_el.get("src") if img_el else None

        # Link / ID
        link_el = card.find("a", href=True)
        listing_url = listing_id = None
        if link_el:
            href = link_el["href"]
            if not href.startswith("http"):
                href = f"{REALTOR_BASE}{href}"
            listing_url = href
            m = re.search(r"_(\d+)$", href.rstrip("/"))
            if not m:
                m = re.search(r"/(\d+)/?$", href)
            listing_id = m.group(1) if m else None

        return PropertyListing(
            listing_id=listing_id,
            address=address,
            price=price,
            beds=beds,
            baths=baths,
            sqft=sqft,
            image_url=image_url,
            listing_url=listing_url,
            source="realtor",
        )
    except Exception as exc:
        logger.warning("Failed to parse Realtor.com card: %s", exc)
        return None


def scrape_realtor(request: RealEstateRequest) -> list[PropertyListing]:
    """Scrape property listings from Realtor.com."""
    url = _build_realtor_url(request)
    logger.info("Scraping Realtor.com URL: %s", url)

    with requests.Session() as session:
        html = _fetch_page(url, session)

    if not html:
        logger.warning("Realtor.com: failed to fetch page")
        return []

    soup = BeautifulSoup(html, "html.parser")

    cards = soup.find_all("div", attrs={"data-testid": re.compile(r"(?i)card|listing")})
    if not cards:
        cards = soup.find_all(
            "li",
            class_=re.compile(r"(?i)card|listing|result"),
        )
    if not cards:
        cards = soup.find_all("a", href=re.compile(r"/realestateandhomes-detail/"))
        cards = [c.parent for c in cards if c.parent]

    listings: list[PropertyListing] = []
    for card in cards[: request.max_results]:
        listing = _parse_realtor_card(card)
        if listing:
            listings.append(listing)

    logger.info("Realtor.com: scraped %d listings", len(listings))
    return listings


# ---------------------------------------------------------------------------
# Aggregator
# ---------------------------------------------------------------------------


def scrape_real_estate(request: RealEstateRequest) -> RealEstateResponse:
    """
    Scrape real-estate listings from one or all supported sources.

    Supported sources: ``zillow``, ``redfin``, ``realtor``, ``all``.
    """
    all_listings: list[PropertyListing] = []

    source = request.source.lower()

    if source in ("zillow", "all"):
        all_listings.extend(scrape_zillow(request))

    if source in ("redfin", "all"):
        all_listings.extend(scrape_redfin(request))

    if source in ("realtor", "all"):
        all_listings.extend(scrape_realtor(request))

    if source not in ("zillow", "redfin", "realtor", "all"):
        return RealEstateResponse(
            success=False,
            count=0,
            listings=[],
            message=f"Unknown source '{source}'. Choose from: zillow, redfin, realtor, all.",
        )

    # When source is "all", honor max_results across the combined set
    if source == "all":
        all_listings = all_listings[: request.max_results]

    return RealEstateResponse(
        success=True,
        count=len(all_listings),
        listings=all_listings,
        message=None,
    )
