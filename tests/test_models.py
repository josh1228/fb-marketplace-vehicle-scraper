"""
Tests for models.py — Pydantic data models.
"""

import pytest
from pydantic import ValidationError

from models import ScrapeRequest, ScrapeResponse, VehicleListing


class TestVehicleListing:
    def test_minimal_listing(self):
        listing = VehicleListing(title="2020 Honda Civic")
        assert listing.title == "2020 Honda Civic"
        assert listing.listing_id is None
        assert listing.price is None
        assert listing.location is None
        assert listing.mileage is None
        assert listing.year is None
        assert listing.make is None
        assert listing.model is None
        assert listing.image_url is None
        assert listing.listing_url is None
        assert listing.description is None

    def test_full_listing(self):
        listing = VehicleListing(
            listing_id="123456789",
            title="2018 Honda Civic LX",
            price="$12,500",
            location="Brooklyn, NY",
            mileage="45,000 mi",
            year="2018",
            make="Honda",
            model="Civic",
            image_url="https://example.com/img.jpg",
            listing_url="https://www.facebook.com/marketplace/item/123456789",
            description="Clean title, one owner.",
        )
        assert listing.listing_id == "123456789"
        assert listing.title == "2018 Honda Civic LX"
        assert listing.price == "$12,500"
        assert listing.location == "Brooklyn, NY"
        assert listing.mileage == "45,000 mi"
        assert listing.year == "2018"
        assert listing.make == "Honda"
        assert listing.model == "Civic"
        assert listing.image_url == "https://example.com/img.jpg"
        assert listing.listing_url == "https://www.facebook.com/marketplace/item/123456789"
        assert listing.description == "Clean title, one owner."

    def test_title_required(self):
        with pytest.raises(ValidationError):
            VehicleListing()  # title is required


class TestScrapeRequest:
    def test_defaults(self):
        req = ScrapeRequest()
        assert req.location == "new-york-ny"
        assert req.vehicle_type == "cars-trucks"
        assert req.min_price is None
        assert req.max_price is None
        assert req.max_mileage is None
        assert req.max_results == 20

    def test_custom_values(self):
        req = ScrapeRequest(
            location="seattle-wa",
            vehicle_type="motorcycles",
            min_price=1000,
            max_price=10000,
            max_mileage=50000,
            max_results=5,
        )
        assert req.location == "seattle-wa"
        assert req.vehicle_type == "motorcycles"
        assert req.min_price == 1000
        assert req.max_price == 10000
        assert req.max_mileage == 50000
        assert req.max_results == 5


class TestScrapeResponse:
    def test_success_response(self):
        listings = [VehicleListing(title="2019 Toyota Camry")]
        resp = ScrapeResponse(success=True, count=1, listings=listings)
        assert resp.success is True
        assert resp.count == 1
        assert len(resp.listings) == 1
        assert resp.message is None

    def test_failure_response(self):
        resp = ScrapeResponse(
            success=False,
            count=0,
            listings=[],
            message="Failed to fetch page after retries.",
        )
        assert resp.success is False
        assert resp.count == 0
        assert resp.listings == []
        assert resp.message == "Failed to fetch page after retries."

    def test_empty_listings(self):
        resp = ScrapeResponse(success=True, count=0, listings=[])
        assert resp.count == 0
        assert resp.listings == []
