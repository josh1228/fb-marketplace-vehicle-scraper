"""
Tests for main.py — FastAPI application endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app
from models import ScrapeResponse, VehicleListing

client = TestClient(app)

MOCK_LISTINGS = [
    VehicleListing(
        listing_id="999000",
        title="2020 Toyota Camry",
        price="$18,000",
        location="New York, NY",
        year="2020",
        listing_url="https://www.facebook.com/marketplace/item/999000",
    )
]

MOCK_SUCCESS_RESPONSE = ScrapeResponse(
    success=True,
    count=1,
    listings=MOCK_LISTINGS,
)

MOCK_EMPTY_RESPONSE = ScrapeResponse(
    success=True,
    count=0,
    listings=[],
)

MOCK_FAILURE_RESPONSE = ScrapeResponse(
    success=False,
    count=0,
    listings=[],
    message="Failed to fetch page after retries.",
)


class TestRootEndpoint:
    def test_health_check_returns_200(self):
        response = client.get("/")
        assert response.status_code == 200

    def test_health_check_body(self):
        response = client.get("/")
        data = response.json()
        assert data["status"] == "ok"
        assert "message" in data


class TestPostScrapeEndpoint:
    def test_successful_scrape(self):
        with patch("main.scrape_vehicles", return_value=MOCK_SUCCESS_RESPONSE):
            response = client.post(
                "/scrape",
                json={
                    "location": "new-york-ny",
                    "vehicle_type": "cars-trucks",
                    "max_results": 20,
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 1
        assert len(data["listings"]) == 1

    def test_listing_fields_in_response(self):
        with patch("main.scrape_vehicles", return_value=MOCK_SUCCESS_RESPONSE):
            response = client.post("/scrape", json={"location": "new-york-ny"})
        listing = response.json()["listings"][0]
        assert listing["listing_id"] == "999000"
        assert listing["title"] == "2020 Toyota Camry"
        assert listing["price"] == "$18,000"
        assert listing["year"] == "2020"

    def test_empty_results(self):
        with patch("main.scrape_vehicles", return_value=MOCK_EMPTY_RESPONSE):
            response = client.post("/scrape", json={"location": "new-york-ny"})
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["listings"] == []

    def test_scraper_failure_still_returns_200(self):
        with patch("main.scrape_vehicles", return_value=MOCK_FAILURE_RESPONSE):
            response = client.post("/scrape", json={"location": "new-york-ny"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["message"] is not None

    def test_internal_error_returns_500(self):
        with patch("main.scrape_vehicles", side_effect=RuntimeError("unexpected")):
            response = client.post("/scrape", json={"location": "new-york-ny"})
        assert response.status_code == 500

    def test_default_location_used_when_omitted(self):
        with patch("main.scrape_vehicles", return_value=MOCK_EMPTY_RESPONSE) as mock_scrape:
            client.post("/scrape", json={})
        call_args = mock_scrape.call_args[0][0]
        assert call_args.location == "new-york-ny"

    def test_price_filters_passed_through(self):
        with patch("main.scrape_vehicles", return_value=MOCK_EMPTY_RESPONSE) as mock_scrape:
            client.post(
                "/scrape",
                json={"location": "chicago-il", "min_price": 3000, "max_price": 12000},
            )
        call_args = mock_scrape.call_args[0][0]
        assert call_args.min_price == 3000
        assert call_args.max_price == 12000


class TestGetScrapeEndpoint:
    def test_get_returns_200(self):
        with patch("main.scrape_vehicles", return_value=MOCK_SUCCESS_RESPONSE):
            response = client.get("/scrape?location=new-york-ny")
        assert response.status_code == 200

    def test_get_default_params(self):
        with patch("main.scrape_vehicles", return_value=MOCK_EMPTY_RESPONSE) as mock_scrape:
            client.get("/scrape")
        call_args = mock_scrape.call_args[0][0]
        assert call_args.location == "new-york-ny"
        assert call_args.vehicle_type == "cars-trucks"
        assert call_args.max_results == 20

    def test_get_with_query_params(self):
        with patch("main.scrape_vehicles", return_value=MOCK_EMPTY_RESPONSE) as mock_scrape:
            client.get("/scrape?location=miami-fl&vehicle_type=motorcycles&max_price=8000&max_results=5")
        call_args = mock_scrape.call_args[0][0]
        assert call_args.location == "miami-fl"
        assert call_args.vehicle_type == "motorcycles"
        assert call_args.max_price == 8000
        assert call_args.max_results == 5

    def test_get_internal_error_returns_500(self):
        with patch("main.scrape_vehicles", side_effect=ValueError("boom")):
            response = client.get("/scrape")
        assert response.status_code == 500
