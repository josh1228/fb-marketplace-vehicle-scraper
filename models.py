from typing import Optional
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
    deal_score: Optional[float] = None
    is_good_deal: Optional[bool] = None


class ScrapeRequest(BaseModel):
    location: str = "new-york-ny"
    max_price: Optional[int] = None
    min_price: Optional[int] = None
    max_mileage: Optional[int] = None
    vehicle_type: str = "cars-trucks"
    max_results: int = 20
    analyze_deals: bool = True


class ScrapeResponse(BaseModel):
    success: bool
    count: int
    listings: list[VehicleListing]
    message: Optional[str] = None
