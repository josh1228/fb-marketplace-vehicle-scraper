from typing import Literal, Optional
from pydantic import BaseModel


class VehicleListing(BaseModel):
    listing_id: Optional[str] = None
    title: str
    price: Optional[str] = None
    location: Optional[str] = None
    mileage: Optional[str] = None
    year: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    image_url: Optional[str] = None
    listing_url: Optional[str] = None
    description: Optional[str] = None


class ScrapeRequest(BaseModel):
    location: str = "new-york-ny"
    max_price: Optional[int] = None
    min_price: Optional[int] = None
    max_mileage: Optional[int] = None
    vehicle_type: str = "cars-trucks"
    max_results: int = 20


class ScrapeResponse(BaseModel):
    success: bool
    count: int
    listings: list[VehicleListing]
    message: Optional[str] = None


# ---------------------------------------------------------------------------
# Real-estate models
# ---------------------------------------------------------------------------


class PropertyListing(BaseModel):
    listing_id: Optional[str] = None
    address: Optional[str] = None
    price: Optional[str] = None
    beds: Optional[str] = None
    baths: Optional[str] = None
    sqft: Optional[str] = None
    property_type: Optional[str] = None
    image_url: Optional[str] = None
    listing_url: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None


class RealEstateRequest(BaseModel):
    location: str = "New York, NY"
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    min_beds: Optional[int] = None
    max_beds: Optional[int] = None
    property_type: Optional[str] = None  # e.g. "house", "condo", "townhouse"
    max_results: int = 20
    source: Literal["zillow", "redfin", "realtor", "all"] = "all"


class RealEstateResponse(BaseModel):
    success: bool
    count: int
    listings: list[PropertyListing]
    message: Optional[str] = None
