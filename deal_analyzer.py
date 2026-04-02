"""
Deal analysis for Facebook Marketplace vehicle listings.

Scores each listing relative to the rest of the result set using three signals:
  - price_score:   how far below the median price the listing is (higher = cheaper)
  - year_score:    how recent the model year is (higher = newer)
  - mileage_score: how low the mileage is (higher = fewer miles)

The combined deal_score is a weighted average in the range [–1, 1].
Listings whose deal_score exceeds DEAL_SCORE_THRESHOLD are flagged as
``is_good_deal=True``.
"""

import re
import statistics
from typing import Optional

from config import DEAL_SCORE_THRESHOLD
from models import VehicleListing

# Weights must sum to 1.0
_WEIGHT_PRICE = 0.60
_WEIGHT_YEAR = 0.25
_WEIGHT_MILEAGE = 0.15

# Reference year used to normalise model-year scores (roughly "oldest car we care about")
_YEAR_MIN = 1990
_YEAR_MAX = 2026  # updated every model-year cycle

# Mileage ceiling used for normalisation (anything ≥ this scores 0)
_MILEAGE_MAX = 200_000


def _parse_price(price_str: Optional[str]) -> Optional[int]:
    """Return the numeric value of a price string like '$12,500', or None."""
    if not price_str:
        return None
    digits = re.sub(r"[^\d]", "", price_str)
    return int(digits) if digits else None


def _parse_mileage(mileage_str: Optional[str]) -> Optional[int]:
    """Return the numeric value of a mileage string like '45,000 mi', or None."""
    if not mileage_str:
        return None
    digits = re.sub(r"[^\d]", "", mileage_str)
    return int(digits) if digits else None


def _parse_year(year_str: Optional[str]) -> Optional[int]:
    """Return the integer year from a year string like '2018', or None."""
    if not year_str:
        return None
    match = re.search(r"\b(19|20)\d{2}\b", year_str)
    return int(match.group(0)) if match else None


def _price_score(price: int, median_price: float) -> float:
    """
    Positive when the listing is below the median, negative when above.
    Clamped to [–1, 1].
    """
    if median_price == 0:
        return 0.0
    raw = (median_price - price) / median_price
    return max(-1.0, min(1.0, raw))


def _year_score(year: int) -> float:
    """Normalise year to [0, 1]; older cars score lower."""
    span = _YEAR_MAX - _YEAR_MIN
    if span == 0:
        return 0.0
    return max(0.0, min(1.0, (year - _YEAR_MIN) / span))


def _mileage_score(mileage: int) -> float:
    """Normalise mileage to [0, 1]; higher mileage scores lower."""
    return max(0.0, min(1.0, 1.0 - mileage / _MILEAGE_MAX))


def score_listings(listings: list[VehicleListing]) -> list[VehicleListing]:
    """
    Compute ``deal_score`` and ``is_good_deal`` for every listing in-place.

    Returns the same list (mutated) for convenience.
    """
    prices = [_parse_price(l.price) for l in listings]
    valid_prices = [p for p in prices if p is not None]
    median_price: Optional[float] = statistics.median(valid_prices) if valid_prices else None

    for listing, price_val in zip(listings, prices):
        score_parts: list[float] = []
        weight_sum = 0.0

        # --- price signal ---
        if price_val is not None and median_price is not None:
            score_parts.append(_WEIGHT_PRICE * _price_score(price_val, median_price))
            weight_sum += _WEIGHT_PRICE

        # --- year signal ---
        year_val = _parse_year(listing.year)
        if year_val is not None:
            score_parts.append(_WEIGHT_YEAR * _year_score(year_val))
            weight_sum += _WEIGHT_YEAR

        # --- mileage signal ---
        mileage_val = _parse_mileage(listing.mileage)
        if mileage_val is not None:
            score_parts.append(_WEIGHT_MILEAGE * _mileage_score(mileage_val))
            weight_sum += _WEIGHT_MILEAGE

        if weight_sum > 0:
            # Re-normalise so missing signals don't artificially lower the score
            deal_score = round(sum(score_parts) / weight_sum, 4)
        else:
            deal_score = None

        listing.deal_score = deal_score
        listing.is_good_deal = (deal_score is not None and deal_score >= DEAL_SCORE_THRESHOLD)

    return listings
