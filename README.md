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

### `POST /tiktok/scrape`
Scrape TikTok for videos matching a keyword.

**Request body (JSON):**
```json
{
  "keyword": "abilify",
  "max_results": 20
}
```

**Response:**
```json
{
  "success": true,
  "count": 5,
  "keyword": "abilify",
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
      "created_at": 1714000000
    }
  ]
}
```

### `GET /tiktok/scrape`
Same as POST but via query parameters:
```
GET /tiktok/scrape?keyword=abilify&max_results=20
```

## Configuration

Set the following environment variables (or add them to a `.env` file):

| Variable            | Default              | Description                          |
|---------------------|----------------------|--------------------------------------|
| `SCRAPER_RATE_LIMIT`| `10`                 | Max requests per minute              |
| `SCRAPER_TIMEOUT`   | `30`                 | HTTP request timeout (seconds)       |
| `SCRAPER_RETRIES`   | `3`                  | Number of retry attempts on failure  |
| `API_HOST`          | `localhost`          | API host                             |
| `API_PORT`          | `8080`               | API port                             |
| `USER_AGENT`        | `fb-marketplace-scraper` | User-Agent header for requests   |

## Heroku Deployment

```bash
# Create a new Heroku app
heroku create

# Push to Heroku
git push heroku main

# Set environment variables
heroku config:set SCRAPER_RATE_LIMIT=5
```
