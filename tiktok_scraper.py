"""
TikTok scraper — powered by TikTokApi v7 + Playwright.

Supported scraping modes:
  • Keyword search  — scrape_tiktok_keyword()   (requires a valid ms_token with prior search history)
  • Hashtag         — scrape_tiktok_hashtag()   (most reliable; no auth required)
  • User videos     — scrape_tiktok_user()      (requires sec_uid lookup; no auth required)
  • Trending        — scrape_tiktok_trending()  (no auth required)

TikTokApi drives a real headless Chromium browser (via Playwright) so all
JS-computed request signatures (X-Bogus, msToken, ttwid …) are generated
automatically.

NOTE: This module is provided for **educational purposes only**.
Scraping TikTok may violate TikTok's Terms of Service.
Always review and comply with the platform's terms before use.
"""

import logging
from contextlib import asynccontextmanager
from typing import Optional

from TikTokApi import TikTokApi

from config import TIKTOK_MS_TOKEN, TIKTOK_PROXY
from models import (
    TikTokHashtagRequest,
    TikTokScrapeRequest,
    TikTokScrapeResponse,
    TikTokUserRequest,
    TikTokVideo,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def _api_session():
    """Async context manager that yields an initialised TikTokApi instance."""
    ms_tokens = [TIKTOK_MS_TOKEN] if TIKTOK_MS_TOKEN else None
    proxy = TIKTOK_PROXY or None

    async with TikTokApi() as api:
        await api.create_sessions(
            ms_tokens=ms_tokens,
            num_sessions=1,
            sleep_after=3,
            headless=True,
            proxies=[proxy] if proxy else None,
        )
        yield api


def _parse_video(video) -> Optional[TikTokVideo]:
    """
    Extract a TikTokVideo from a TikTokApi Video object.

    Uses the Video's `as_dict` property (the raw API payload) plus the
    structured attributes set by TikTokApi for richer, typed access.
    """
    try:
        data = video.as_dict

        video_id = data.get("id")

        # Author — prefer the structured attribute, fall back to raw dict.
        author: Optional[str] = None
        if getattr(video, "author", None) is not None:
            author = getattr(video.author, "username", None) or getattr(
                video.author, "nickname", None
            )
        if not author:
            author_info = data.get("author", {})
            if isinstance(author_info, dict):
                author = author_info.get("uniqueId") or author_info.get("nickname")

        desc = data.get("desc", "")

        # Stats — prefer the structured attribute.
        stats = getattr(video, "stats", None) or data.get("stats", {})
        play_count = stats.get("playCount") if isinstance(stats, dict) else None
        like_count = stats.get("diggCount") if isinstance(stats, dict) else None
        comment_count = stats.get("commentCount") if isinstance(stats, dict) else None
        share_count = stats.get("shareCount") if isinstance(stats, dict) else None

        # Media URLs.
        cover_url: Optional[str] = None
        video_url: Optional[str] = None
        video_detail = data.get("video", {})
        if isinstance(video_detail, dict):
            cover_url = video_detail.get("cover") or video_detail.get("originCover")
            video_url = video_detail.get("playAddr") or video_detail.get("downloadAddr")

        # Creation timestamp — prefer structured attribute.
        created_at: Optional[int] = None
        if getattr(video, "create_time", None) is not None:
            try:
                created_at = int(video.create_time.timestamp())
            except (AttributeError, TypeError, ValueError):
                pass
        if created_at is None:
            raw_ts = data.get("createTime")
            created_at = int(raw_ts) if raw_ts is not None else None

        # Hashtags — prefer structured attribute, fall back to raw challenges list.
        hashtags: list[str] = []
        if getattr(video, "hashtags", None):
            hashtags = [
                getattr(ht, "name", "") for ht in video.hashtags if getattr(ht, "name", "")
            ]
        if not hashtags:
            challenges = data.get("challenges") or data.get("textExtra", [])
            if isinstance(challenges, list):
                hashtags = [
                    c.get("hashtagName") or c.get("title", "")
                    for c in challenges
                    if isinstance(c, dict) and (c.get("hashtagName") or c.get("title"))
                ]

        # Sound title.
        sound_title: Optional[str] = None
        if getattr(video, "sound", None) is not None:
            sound_title = getattr(video.sound, "title", None)
        if not sound_title:
            music = data.get("music", {})
            if isinstance(music, dict):
                sound_title = music.get("title")

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
            created_at=created_at,
            hashtags=hashtags,
            sound_title=sound_title,
        )
    except Exception as exc:
        logger.warning("Failed to parse TikTok video: %s", exc)
        return None


def _collect(videos: list[TikTokVideo], parsed: Optional[TikTokVideo], seen: set) -> None:
    """Append parsed video to the list, skipping duplicates by video_id.

    Only deduplicates when a video_id is present; videos without an ID are
    always included to avoid incorrectly dropping valid results.
    """
    if parsed is None:
        return
    if parsed.video_id:
        if parsed.video_id in seen:
            return
        seen.add(parsed.video_id)
    videos.append(parsed)


async def scrape_tiktok_keyword(request: TikTokScrapeRequest) -> TikTokScrapeResponse:
    """
    Scrape TikTok for videos matching a keyword.

    Uses TikTok's general search endpoint (`/api/search/item/full/`).

    Note: This endpoint requires an ms_token that has been used for a prior
    TikTok search session.  Set the TIKTOK_MS_TOKEN environment variable.
    If results are empty, use the hashtag endpoint instead.
    """
    logger.info(
        "Keyword scrape: '%s' (max %d, ms_token=%s, proxy=%s)",
        request.keyword,
        request.max_results,
        "set" if TIKTOK_MS_TOKEN else "not set",
        "set" if TIKTOK_PROXY else "not set",
    )
    try:
        videos: list[TikTokVideo] = []
        seen: set = set()

        async with _api_session() as api:
            async for video in api.search.search_type(
                request.keyword, "item", count=request.max_results
            ):
                _collect(videos, _parse_video(video), seen)

        logger.info("Keyword scrape done: %d videos for '%s'", len(videos), request.keyword)
        return TikTokScrapeResponse(
            success=True,
            count=len(videos),
            keyword=request.keyword,
            videos=videos,
        )
    except Exception as exc:
        logger.error("Keyword scrape failed for '%s': %s", request.keyword, exc)
        return TikTokScrapeResponse(
            success=False,
            count=0,
            keyword=request.keyword,
            videos=[],
            message=str(exc),
        )


async def scrape_tiktok_hashtag(request: TikTokHashtagRequest) -> TikTokScrapeResponse:
    """
    Scrape TikTok for videos tagged with a hashtag (e.g. #abilify).

    This is the most reliable scraping mode — it does not require an
    authenticated ms_token and is not subject to the search auth restriction.
    """
    logger.info(
        "Hashtag scrape: '#%s' (max %d, ms_token=%s, proxy=%s)",
        request.hashtag,
        request.max_results,
        "set" if TIKTOK_MS_TOKEN else "not set",
        "set" if TIKTOK_PROXY else "not set",
    )
    try:
        videos: list[TikTokVideo] = []
        seen: set = set()

        async with _api_session() as api:
            async for video in api.hashtag(name=request.hashtag).videos(
                count=request.max_results
            ):
                _collect(videos, _parse_video(video), seen)

        logger.info("Hashtag scrape done: %d videos for '#%s'", len(videos), request.hashtag)
        return TikTokScrapeResponse(
            success=True,
            count=len(videos),
            keyword=f"#{request.hashtag}",
            videos=videos,
        )
    except Exception as exc:
        logger.error("Hashtag scrape failed for '#%s': %s", request.hashtag, exc)
        return TikTokScrapeResponse(
            success=False,
            count=0,
            keyword=f"#{request.hashtag}",
            videos=[],
            message=str(exc),
        )


async def scrape_tiktok_user(request: TikTokUserRequest) -> TikTokScrapeResponse:
    """
    Scrape a TikTok user's posted videos by username.

    TikTokApi resolves the username → sec_uid automatically via a profile
    info request before fetching the video list.
    """
    logger.info(
        "User scrape: '@%s' (max %d, ms_token=%s, proxy=%s)",
        request.username,
        request.max_results,
        "set" if TIKTOK_MS_TOKEN else "not set",
        "set" if TIKTOK_PROXY else "not set",
    )
    try:
        videos: list[TikTokVideo] = []
        seen: set = set()

        async with _api_session() as api:
            async for video in api.user(username=request.username).videos(
                count=request.max_results
            ):
                _collect(videos, _parse_video(video), seen)

        logger.info("User scrape done: %d videos for '@%s'", len(videos), request.username)
        return TikTokScrapeResponse(
            success=True,
            count=len(videos),
            keyword=f"@{request.username}",
            videos=videos,
        )
    except Exception as exc:
        logger.error("User scrape failed for '@%s': %s", request.username, exc)
        return TikTokScrapeResponse(
            success=False,
            count=0,
            keyword=f"@{request.username}",
            videos=[],
            message=str(exc),
        )


async def scrape_tiktok_trending(max_results: int = 30) -> TikTokScrapeResponse:
    """
    Scrape TikTok's current trending / For-You feed videos.

    Does not require an authenticated ms_token.
    """
    logger.info(
        "Trending scrape: max %d (ms_token=%s, proxy=%s)",
        max_results,
        "set" if TIKTOK_MS_TOKEN else "not set",
        "set" if TIKTOK_PROXY else "not set",
    )
    try:
        videos: list[TikTokVideo] = []
        seen: set = set()

        async with _api_session() as api:
            async for video in api.trending.videos(count=max_results):
                _collect(videos, _parse_video(video), seen)

        logger.info("Trending scrape done: %d videos", len(videos))
        return TikTokScrapeResponse(
            success=True,
            count=len(videos),
            keyword="trending",
            videos=videos,
        )
    except Exception as exc:
        logger.error("Trending scrape failed: %s", exc)
        return TikTokScrapeResponse(
            success=False,
            count=0,
            keyword="trending",
            videos=[],
            message=str(exc),
        )


# Back-compat alias used by the keyword POST/GET endpoints.
scrape_tiktok = scrape_tiktok_keyword
