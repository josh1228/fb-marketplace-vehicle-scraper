from typing import Optional
from pydantic import BaseModel


# ── TikTok models ─────────────────────────────────────────────────────────────

class TikTokVideo(BaseModel):
    video_id: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    play_count: Optional[int] = None
    like_count: Optional[int] = None
    comment_count: Optional[int] = None
    share_count: Optional[int] = None
    cover_url: Optional[str] = None
    video_url: Optional[str] = None
    created_at: Optional[int] = None
    hashtags: list[str] = []
    sound_title: Optional[str] = None


class TikTokScrapeRequest(BaseModel):
    keyword: str = "abilify"
    max_results: int = 20


class TikTokHashtagRequest(BaseModel):
    hashtag: str = "abilify"
    max_results: int = 20


class TikTokUserRequest(BaseModel):
    username: str
    max_results: int = 20


class TikTokScrapeResponse(BaseModel):
    success: bool
    count: int
    keyword: str
    videos: list[TikTokVideo]
    message: Optional[str] = None


# ── Facebook Marketplace models ────────────────────────────────────────────────

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
