# fb-marketplace-vehicle-scraper

> **Educational purposes only.**  
> Scraping Facebook Marketplace may violate Facebook's Terms of Service. Review and comply with the platform's terms before using this project.

## Overview

A FastAPI-based REST API that scrapes vehicle listings from Facebook Marketplace using `requests` and `BeautifulSoup4`.

## Project Structure

```
├── config.py             # Environment-driven configuration
├── models.py             # Pydantic data models
├── scraper.py            # FB Marketplace scraping logic
├── tiktok_scraper.py     # TikTok keyword scraping logic
├── main.py               # FastAPI application
├── Procfile              # Heroku entry point
└── requirements.txt      # Python dependencies
```

## Setup

```bash
# Clone the repository
git clone https://github.com/josh1228/fb-marketplace-vehicle-scraper.git
cd fb-marketplace-vehicle-scraper

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser binaries (required for TikTok scraping)
playwright install chromium

# (Optional) copy and edit environment variables
cp .env.example .env
```

## Running Locally

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

## API Endpoints

### `GET /`
Health check.

### `POST /scrape`
Scrape vehicle listings.

**Request body (JSON):**
```json
{
  "location":     "new-york-ny",
  "vehicle_type": "cars-trucks",
  "min_price":    5000,
  "max_price":    20000,
  "max_mileage":  100000,
  "max_results":  20
}
```

**Response:**
```json
{
  "success": true,
  "count": 5,
  "listings": [
    {
      "listing_id": "123456789",
      "title": "2018 Honda Civic",
      "price": "$12,500",
      "location": "Brooklyn, NY",
      "year": "2018",
      "image_url": "https://...",
      "listing_url": "https://www.facebook.com/marketplace/item/123456789"
    }
  ]
}
```

### `GET /scrape`
Same as POST but via query parameters:
```
GET /scrape?location=new-york-ny&vehicle_type=cars-trucks&max_price=15000
```

---

## TikTok Endpoints

> **Recommended for Abilify content:** use `/tiktok/hashtag` — it is the most
> reliable mode and does not require an authenticated `TIKTOK_MS_TOKEN`.

### `POST /tiktok/hashtag` ⭐ recommended
Scrape videos tagged with a hashtag.

```json
{ "hashtag": "abilify", "max_results": 20 }
```
```
GET /tiktok/hashtag?hashtag=abilify&max_results=20
```

### `POST /tiktok/scrape`
Scrape videos by keyword (general search). Requires a valid `TIKTOK_MS_TOKEN`
with prior search history; otherwise returns empty results.

```json
{ "keyword": "abilify", "max_results": 20 }
```
```
GET /tiktok/scrape?keyword=abilify&max_results=20
```

### `POST /tiktok/user`
Scrape videos posted by a specific user.

```json
{ "username": "someuser", "max_results": 20 }
```
```
GET /tiktok/user?username=someuser&max_results=20
```

### `GET /tiktok/trending`
Scrape TikTok's current trending / For-You feed. No auth required.

```
GET /tiktok/trending?max_results=30
```

**All TikTok endpoints return the same response shape:**
```json
{
  "success": true,
  "count": 5,
  "keyword": "#abilify",
  "videos": [
    {
      "video_id": "7123456789012345678",
      "author": "someuser",
      "description": "My experience with Abilify #abilify #mentalhealth",
      "play_count": 45000,
      "like_count": 3200,
      "comment_count": 180,
      "share_count": 75,
      "cover_url": "https://...",
      "video_url": "https://...",
      "created_at": 1714000000,
      "hashtags": ["abilify", "mentalhealth"],
      "sound_title": "original sound"
    }
  ]
}
```

## Configuration

Set the following environment variables (or add them to a `.env` file):

| Variable            | Default              | Description                                                        |
|---------------------|----------------------|--------------------------------------------------------------------|
| `SCRAPER_RATE_LIMIT`| `10`                 | Max requests per minute                                            |
| `SCRAPER_TIMEOUT`   | `30`                 | HTTP request timeout (seconds)                                     |
| `SCRAPER_RETRIES`   | `3`                  | Number of retry attempts on failure                                |
| `API_HOST`          | `localhost`          | API host                                                           |
| `API_PORT`          | `8080`               | API port                                                           |
| `USER_AGENT`        | `fb-marketplace-scraper` | User-Agent header for requests                                 |
| `TIKTOK_MS_TOKEN`   | *(not set)*          | TikTok `msToken` cookie — required for keyword search, optional for hashtag/user/trending |
| `TIKTOK_PROXY`      | *(not set)*          | HTTP/SOCKS proxy for TikTok requests, e.g. `http://user:pass@host:port` |

### Obtaining `TIKTOK_MS_TOKEN`

1. Open [tiktok.com](https://www.tiktok.com) in Chrome/Firefox and log in (or stay logged out — the cookie is still set).
2. Open DevTools → **Application** tab → **Cookies** → `https://www.tiktok.com`.
3. Copy the value of the `msToken` cookie.
4. Set it as the `TIKTOK_MS_TOKEN` environment variable.

> **Tip:** For keyword search to work reliably, log in to TikTok and
> perform at least one manual search in the browser before copying the token.

## Heroku Deployment

The `Procfile` includes a `release` phase that automatically installs the Chromium browser binary before the web dyno starts (required for TikTok scraping).

```bash
# Create a new Heroku app
heroku create

# Push to Heroku
git push heroku main

# Set environment variables
heroku config:set SCRAPER_RATE_LIMIT=5
heroku config:set TIKTOK_MS_TOKEN=<your_ms_token>
heroku config:set TIKTOK_PROXY=http://user:pass@proxy-host:port   # optional
```
