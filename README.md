# fb-marketplace-vehicle-scraper

> **Educational purposes only.**  
> Scraping Facebook Marketplace may violate Facebook's Terms of Service. Review and comply with the platform's terms before using this project.

## Overview

A FastAPI-based REST API that scrapes vehicle listings from Facebook Marketplace using `requests` and `BeautifulSoup4`.  
A built-in **deal analyser** scores every listing on price, model year, and mileage so you can quickly surface the best-value cars.

## Project Structure

```
├── config.py          # Environment-driven configuration
├── models.py          # Pydantic data models
├── scraper.py         # Core scraping logic
├── deal_analyzer.py   # Heuristic deal-scoring engine
├── main.py            # FastAPI application
├── Procfile           # Heroku entry point
└── requirements.txt   # Python dependencies
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
  "location":       "new-york-ny",
  "vehicle_type":   "cars-trucks",
  "min_price":      5000,
  "max_price":      20000,
  "max_mileage":    100000,
  "max_results":    20,
  "analyze_deals":  true
}
```

**Response:**
```json
{
  "success": true,
  "count": 5,
  "listings": [
    {
      "listing_id":  "123456789",
      "title":       "2018 Honda Civic",
      "price":       "$12,500",
      "location":    "Brooklyn, NY",
      "year":        "2018",
      "image_url":   "https://...",
      "listing_url": "https://www.facebook.com/marketplace/item/123456789",
      "deal_score":  0.23,
      "is_good_deal": true
    }
  ]
}
```

### `GET /scrape`
Same as POST but via query parameters:
```
GET /scrape?location=new-york-ny&vehicle_type=cars-trucks&max_price=15000&analyze_deals=true
```

### `POST /deals`
Scrape listings and return **only the good deals**, sorted by `deal_score` descending.  
Accepts the same body as `POST /scrape`.

### `GET /deals`
Same as `POST /deals` but via query parameters:
```
GET /deals?location=new-york-ny&max_price=15000&max_mileage=80000
```

## Deal Scoring

Each listing receives a `deal_score` in **[–1, 1]** computed from three signals:

| Signal       | Weight | Description                                      |
|--------------|--------|--------------------------------------------------|
| Price        | 60 %   | How far below the median price of all results    |
| Model year   | 25 %   | How recent the vehicle year is                   |
| Mileage      | 15 %   | How low the reported mileage is                  |

A listing is flagged `is_good_deal = true` when its `deal_score ≥ DEAL_SCORE_THRESHOLD` (default **0.1**).

## Configuration

Set the following environment variables (or add them to a `.env` file):

| Variable               | Default                  | Description                                        |
|------------------------|--------------------------|----------------------------------------------------|
| `SCRAPER_RATE_LIMIT`   | `10`                     | Max requests per minute                            |
| `SCRAPER_TIMEOUT`      | `30`                     | HTTP request timeout (seconds)                     |
| `SCRAPER_RETRIES`      | `3`                      | Number of retry attempts on failure                |
| `API_HOST`             | `localhost`              | API host                                           |
| `API_PORT`             | `8080`                   | API port                                           |
| `USER_AGENT`           | `fb-marketplace-scraper` | User-Agent header for requests                     |
| `DEAL_SCORE_THRESHOLD` | `0.1`                    | Minimum deal_score to be flagged as a good deal    |

## Heroku Deployment

```bash
# Create a new Heroku app
heroku create

# Push to Heroku
git push heroku main

# Set environment variables
heroku config:set SCRAPER_RATE_LIMIT=5 DEAL_SCORE_THRESHOLD=0.15
```

