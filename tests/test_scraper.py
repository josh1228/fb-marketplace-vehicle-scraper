"""
Tests for scraper.py — URL builder, HTML parser, page fetcher, and main orchestrator.
"""

import textwrap
from unittest.mock import MagicMock, patch

import pytest
import requests

from models import ScrapeRequest, VehicleListing
from scraper import _build_url, _fetch_page, _parse_listing, scrape_vehicles


# ── _build_url ────────────────────────────────────────────────────────────────

class TestBuildUrl:
    def test_no_filters(self):
        req = ScrapeRequest(location="new-york-ny", vehicle_type="cars-trucks")
        url = _build_url(req)
        assert url == "https://www.facebook.com/marketplace/new-york-ny/cars-trucks/"

    def test_min_price_only(self):
        req = ScrapeRequest(location="los-angeles-ca", vehicle_type="cars-trucks", min_price=5000)
        url = _build_url(req)
        assert "minPrice=5000" in url
        assert "maxPrice" not in url

    def test_max_price_only(self):
        req = ScrapeRequest(location="chicago-il", vehicle_type="motorcycles", max_price=15000)
        url = _build_url(req)
        assert "maxPrice=15000" in url
        assert "minPrice" not in url

    def test_all_filters(self):
        req = ScrapeRequest(
            location="seattle-wa",
            vehicle_type="cars-trucks",
            min_price=2000,
            max_price=20000,
            max_mileage=100000,
        )
        url = _build_url(req)
        assert "minPrice=2000" in url
        assert "maxPrice=20000" in url
        assert "maxMileage=100000" in url

    def test_url_starts_with_base(self):
        req = ScrapeRequest(location="miami-fl", vehicle_type="rvs-campers")
        url = _build_url(req)
        assert url == "https://www.facebook.com/marketplace/miami-fl/rvs-campers/"


# ── _parse_listing ─────────────────────────────────────────────────────────────

def _make_card(html: str):
    """Helper: wrap HTML in a BeautifulSoup tag so _parse_listing can consume it."""
    from bs4 import BeautifulSoup
    return BeautifulSoup(html, "html.parser")


class TestParseListing:
    def test_full_card(self):
        html = textwrap.dedent("""
            <div>
              <a href="/marketplace/item/111222333" aria-label="2019 Ford F-150">
                <img src="https://example.com/truck.jpg" />
              </a>
              <span>$18,500</span>
              <span>Dallas, TX</span>
            </div>
        """)
        card = _make_card(html)
        result = _parse_listing(card)
        assert result is not None
        assert result.listing_id == "111222333"
        assert result.title == "2019 Ford F-150"
        assert result.price == "$18,500"
        assert result.image_url == "https://example.com/truck.jpg"
        assert result.listing_url == "https://www.facebook.com/marketplace/item/111222333"
        assert result.year == "2019"

    def test_relative_href_becomes_absolute(self):
        html = '<div><a href="/marketplace/item/999">Car</a></div>'
        card = _make_card(html)
        result = _parse_listing(card)
        assert result is not None
        assert result.listing_url == "https://www.facebook.com/marketplace/item/999"

    def test_no_year_in_title(self):
        html = '<div><a href="/marketplace/item/1" aria-label="Honda Civic">link</a></div>'
        card = _make_card(html)
        result = _parse_listing(card)
        assert result is not None
        assert result.year is None

    def test_year_extracted_from_title(self):
        html = '<div><a href="/marketplace/item/2" aria-label="2022 Toyota RAV4">x</a></div>'
        card = _make_card(html)
        result = _parse_listing(card)
        assert result is not None
        assert result.year == "2022"

    def test_no_price_returns_none(self):
        html = '<div><a href="/marketplace/item/3" aria-label="Old Car">x</a></div>'
        card = _make_card(html)
        result = _parse_listing(card)
        assert result is not None
        assert result.price is None

    def test_no_image_returns_none(self):
        html = '<div><a href="/marketplace/item/4">Car</a><span>$5,000</span></div>'
        card = _make_card(html)
        result = _parse_listing(card)
        assert result is not None
        assert result.image_url is None

    def test_location_extracted_from_span(self):
        html = textwrap.dedent("""
            <div>
              <a href="/marketplace/item/5" aria-label="2020 Jeep Wrangler">j</a>
              <span>Phoenix, AZ</span>
            </div>
        """)
        card = _make_card(html)
        result = _parse_listing(card)
        assert result is not None
        assert result.location == "Phoenix, AZ"


# ── _fetch_page ────────────────────────────────────────────────────────────────

class TestFetchPage:
    def test_success_on_first_attempt(self):
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "<html>ok</html>"
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response

        with patch("scraper.time.sleep"):
            html = _fetch_page("https://example.com", mock_session)

        assert html == "<html>ok</html>"
        assert mock_session.get.call_count == 1

    def test_returns_none_after_all_retries_fail(self):
        mock_session = MagicMock()
        mock_session.get.side_effect = requests.RequestException("connection error")

        with patch("scraper.time.sleep"), patch("scraper.SCRAPER_RETRIES", 3):
            html = _fetch_page("https://example.com", mock_session)

        assert html is None
        assert mock_session.get.call_count == 3

    def test_succeeds_after_retry(self):
        mock_session = MagicMock()
        ok_response = MagicMock()
        ok_response.text = "<html>retry ok</html>"
        ok_response.raise_for_status.return_value = None

        mock_session.get.side_effect = [
            requests.RequestException("first fail"),
            ok_response,
        ]

        with patch("scraper.time.sleep"), patch("scraper.SCRAPER_RETRIES", 3):
            html = _fetch_page("https://example.com", mock_session)

        assert html == "<html>retry ok</html>"
        assert mock_session.get.call_count == 2

    def test_rate_limit_sleep_called(self):
        mock_session = MagicMock()
        ok_response = MagicMock()
        ok_response.text = "<html></html>"
        ok_response.raise_for_status.return_value = None
        mock_session.get.return_value = ok_response

        rate_limit = 60
        with patch("scraper.time.sleep") as mock_sleep, patch("scraper.SCRAPER_RATE_LIMIT", rate_limit):
            _fetch_page("https://example.com", mock_session)

        mock_sleep.assert_called_once_with(pytest.approx(60.0 / rate_limit))


# ── scrape_vehicles ────────────────────────────────────────────────────────────

SAMPLE_HTML = textwrap.dedent("""
    <html><body>
      <div data-testid="marketplace_listing_item">
        <a href="/marketplace/item/100001" aria-label="2021 Chevrolet Tahoe">
          <img src="https://example.com/tahoe.jpg" />
        </a>
        <span>$35,000</span>
        <span>Houston, TX</span>
      </div>
      <div data-testid="marketplace_listing_item">
        <a href="/marketplace/item/100002" aria-label="2017 BMW 3 Series">
          <img src="https://example.com/bmw.jpg" />
        </a>
        <span>$22,000</span>
        <span>Austin, TX</span>
      </div>
    </body></html>
""")


class TestScrapeVehicles:
    def test_successful_scrape(self):
        req = ScrapeRequest(location="houston-tx", vehicle_type="cars-trucks", max_results=10)

        with patch("scraper._fetch_page", return_value=SAMPLE_HTML):
            response = scrape_vehicles(req)

        assert response.success is True
        assert response.count == 2
        assert len(response.listings) == 2
        assert response.message is None

    def test_listing_fields_populated(self):
        req = ScrapeRequest(location="houston-tx", vehicle_type="cars-trucks")

        with patch("scraper._fetch_page", return_value=SAMPLE_HTML):
            response = scrape_vehicles(req)

        first = response.listings[0]
        assert first.listing_id == "100001"
        assert first.title == "2021 Chevrolet Tahoe"
        assert first.price == "$35,000"
        assert first.year == "2021"
        assert first.listing_url == "https://www.facebook.com/marketplace/item/100001"

    def test_fetch_failure_returns_error_response(self):
        req = ScrapeRequest(location="houston-tx", vehicle_type="cars-trucks")

        with patch("scraper._fetch_page", return_value=None):
            response = scrape_vehicles(req)

        assert response.success is False
        assert response.count == 0
        assert response.listings == []
        assert response.message is not None

    def test_max_results_limits_output(self):
        req = ScrapeRequest(location="houston-tx", vehicle_type="cars-trucks", max_results=1)

        with patch("scraper._fetch_page", return_value=SAMPLE_HTML):
            response = scrape_vehicles(req)

        assert response.count <= 1
        assert len(response.listings) <= 1

    def test_empty_page_returns_empty_listings(self):
        req = ScrapeRequest(location="nowhere", vehicle_type="cars-trucks")
        empty_html = "<html><body></body></html>"

        with patch("scraper._fetch_page", return_value=empty_html):
            response = scrape_vehicles(req)

        assert response.success is True
        assert response.count == 0
        assert response.listings == []
