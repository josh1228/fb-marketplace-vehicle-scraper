"""
TikTok keyword scraper.

NOTE: This module is provided for **educational purposes only**.
Scraping TikTok may violate TikTok's Terms of Service.
Always review and comply with the platform's terms before use.
"""

import logging
import time
from typing import Optional
from urllib.parse import urlencode

import requests

from config import (
    SCRAPER_RATE_LIMIT,
    SCRAPER_RETRIES,
    SCRAPER_TIMEOUT,
    USER_AGENT,
)
from models import TikTokScrapeRequest, TikTokScrapeResponse, TikTokVideo

logger = logging.getLogger(__name__)

# TikTok unofficial search API
_SEARCH_URL = "https://www.tiktok.com/api/search/general/full/"

_HEADERS = {
    # Use a real browser UA so TikTok does not reject the request immediately;
    # the project-level USER_AGENT env-var is intentionally overridden here
    # because TikTok's API requires a browser-style User-Agent string.
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.tiktok.com/",
    "Origin": "https://www.tiktok.com",
}


def _build_url(keyword: str, cursor: int = 0, count: int = 20) -> str:
    params = {
        "keyword": keyword,
        "count": count,
        "cursor": cursor,
        "app_language": "en",
        "app_name": "tiktok_web",
        "device_platform": "web_pc",
        "os": "windows",
        "priority_region": "",
        "referer": "",
        "region": "US",
        "screen_height": 1080,
        "screen_width": 1920,
        "tz_name": "America/New_York",
        "webcast_language": "en",
    }
    return f"{_SEARCH_URL}?{urlencode(params)}"


def _parse_video(item: dict) -> Optional[TikTokVideo]:
    """Extract a TikTokVideo from a raw search-result item dict."""
    try:
        video_info = item.get("item", item)
        video_id = video_info.get("id")

        author = None
        author_info = video_info.get("author", {})
        if isinstance(author_info, dict):
            author = author_info.get("uniqueId") or author_info.get("nickname")

        desc = video_info.get("desc", "")

        stats = video_info.get("stats", {})
        play_count = stats.get("playCount")
        like_count = stats.get("diggCount")
        comment_count = stats.get("commentCount")
        share_count = stats.get("shareCount")

        cover_url = None
        video_url = None
        video_detail = video_info.get("video", {})
        if isinstance(video_detail, dict):
            cover_url = video_detail.get("cover") or video_detail.get("originCover")
            video_url = video_detail.get("playAddr") or video_detail.get("downloadAddr")

        created_at = video_info.get("createTime")

        return TikTokVideo(
            video_id=str(video_id) if video_id else None,
            author=author,
            description=desc,
            play_count=int(play_count) if play_count is not None else None,
            like_count=int(like_count) if like_count is not None else None,
            comment_count=int(comment_count) if comment_count is not None else None,
            share_count=int(share_count) if share_count is not None else None,
            cover_url=cover_url,
            video_url=video_url,
            created_at=int(created_at) if created_at is not None else None,
        )
    except Exception as exc:
        logger.warning("Failed to parse TikTok video item: %s", exc)
        return None


def _fetch_json(url: str, session: requests.Session) -> Optional[dict]:
    """Fetch JSON from the TikTok API with retry logic."""
    for attempt in range(1, SCRAPER_RETRIES + 1):
        try:
            if SCRAPER_RATE_LIMIT > 0:
                time.sleep(60.0 / SCRAPER_RATE_LIMIT)
            response = session.get(url, headers=_HEADERS, timeout=SCRAPER_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            logger.warning(
                "TikTok attempt %d/%d failed for %s: %s",
                attempt,
                SCRAPER_RETRIES,
                url,
                exc,
            )
            if attempt < SCRAPER_RETRIES:
                time.sleep(2 ** attempt)
        except ValueError as exc:
            logger.warning("TikTok response is not valid JSON: %s", exc)
            return None
    return None


def scrape_tiktok(request: TikTokScrapeRequest) -> TikTokScrapeResponse:
    """
    Scrape TikTok for videos matching a keyword.

    Returns a TikTokScrapeResponse containing parsed TikTokVideo objects.
    """
    url = _build_url(keyword=request.keyword, count=min(request.max_results, 20))
    logger.info("Scraping TikTok URL: %s", url)

    with requests.Session() as session:
        data = _fetch_json(url, session)

    if data is None:
        return TikTokScrapeResponse(
            success=False,
            count=0,
            keyword=request.keyword,
            videos=[],
            message="Failed to fetch results from TikTok after retries.",
        )

    # The search API nests results under different keys depending on the endpoint version:
    #   "data"      – returned by /api/search/general/full/ (current web search API)
    #   "item_list" – returned by older hashtag/challenge endpoints (snake_case variant)
    #   "itemList"  – returned by some mobile-API mirrors (camelCase variant)
    raw_items = (
        data.get("data")
        or data.get("item_list")
        or data.get("itemList")
        or []
    )

    videos: list[TikTokVideo] = []
    for item in raw_items[: request.max_results]:
        video = _parse_video(item)
        if video:
            videos.append(video)

    logger.info("Scraped %d TikTok videos for keyword '%s'", len(videos), request.keyword)
    return TikTokScrapeResponse(
        success=True,
        count=len(videos),
        keyword=request.keyword,
        videos=videos,
        message=None,
    )
