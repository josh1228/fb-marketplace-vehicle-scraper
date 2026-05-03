"""
TikTok keyword scraper — powered by TikTokApi + Playwright.

This module replaces the previous raw-requests approach.  TikTokApi drives a
real headless Chromium browser (via Playwright) so that TikTok's JS-computed
request signatures (X-Bogus, msToken, ttwid …) are generated automatically.

NOTE: This module is provided for **educational purposes only**.
Scraping TikTok may violate TikTok's Terms of Service.
Always review and comply with the platform's terms before use.
"""

import logging
from typing import Optional

from TikTokApi import TikTokApi

from config import TIKTOK_MS_TOKEN
from models import TikTokScrapeRequest, TikTokScrapeResponse, TikTokVideo

logger = logging.getLogger(__name__)


def _parse_video_dict(data: dict) -> Optional[TikTokVideo]:
    """Extract a TikTokVideo from the raw dict returned by video.as_dict."""
    try:
        video_id = data.get("id")

        author = None
        author_info = data.get("author", {})
        if isinstance(author_info, dict):
            author = author_info.get("uniqueId") or author_info.get("nickname")

        desc = data.get("desc", "")

        stats = data.get("stats", {})
        play_count = stats.get("playCount")
        like_count = stats.get("diggCount")
        comment_count = stats.get("commentCount")
        share_count = stats.get("shareCount")

        cover_url = None
        video_url = None
        video_detail = data.get("video", {})
        if isinstance(video_detail, dict):
            cover_url = video_detail.get("cover") or video_detail.get("originCover")
            video_url = video_detail.get("playAddr") or video_detail.get("downloadAddr")

        created_at = data.get("createTime")

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


async def scrape_tiktok(request: TikTokScrapeRequest) -> TikTokScrapeResponse:
    """
    Scrape TikTok for videos matching a keyword using TikTokApi + Playwright.

    TikTokApi spins up a headless Chromium session so all required cookies and
    request signatures are handled automatically.

    Returns a TikTokScrapeResponse containing parsed TikTokVideo objects.
    """
    # Provide the ms_token cookie if configured — improves reliability.
    ms_tokens = [TIKTOK_MS_TOKEN] if TIKTOK_MS_TOKEN else None

    logger.info(
        "Starting TikTok scrape for keyword '%s' (max %d results, ms_token=%s)",
        request.keyword,
        request.max_results,
        "set" if ms_tokens else "not set",
    )

    try:
        videos: list[TikTokVideo] = []

        async with TikTokApi() as api:
            await api.create_sessions(
                ms_tokens=ms_tokens,
                num_sessions=1,
                sleep_after=3,
                headless=True,
            )

            async for video in api.search.videos(
                request.keyword, count=request.max_results
            ):
                parsed = _parse_video_dict(video.as_dict)
                if parsed:
                    videos.append(parsed)

        logger.info(
            "Scraped %d TikTok videos for keyword '%s'",
            len(videos),
            request.keyword,
        )
        return TikTokScrapeResponse(
            success=True,
            count=len(videos),
            keyword=request.keyword,
            videos=videos,
        )

    except Exception as exc:
        logger.error("TikTok scrape failed: %s", exc)
        return TikTokScrapeResponse(
            success=False,
            count=0,
            keyword=request.keyword,
            videos=[],
            message=str(exc),
        )
