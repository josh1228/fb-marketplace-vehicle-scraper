from typing import Optional
from pydantic import BaseModel


class VehicleListing(BaseModel):
    listing_id: str
    title: str
    price: Optional[str] = None
    location: Optional[str] = None
    mileage: Optional[str] = None
    year: Optional[int] = None
    make: Optional[str] = None
    model: Optional[str] = None
    image_url: Optional[str] = None
    listing_url: Optional[str] = None
    description: Optional[str] = None


class ScrapeRequest(BaseModel):
    location: str
    query: str = "vehicles"
    max_results: int = 20


class ScrapeResponse(BaseModel):
    listings: list[VehicleListing]
    total: int
    location: str
    query: str
