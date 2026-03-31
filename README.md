# fb-marketplace-vehicle-scraper

> **Educational purposes only.**  
> Scraping Facebook Marketplace, Zillow, Redfin, and Realtor.com may violate those platforms' Terms of Service. Review and comply with each platform's terms before using this project.

## Overview

A FastAPI-based REST API that scrapes:

- **Vehicle listings** from Facebook Marketplace (using `requests` + `BeautifulSoup4`)
- **Real-estate listings** from Zillow, Redfin, and Realtor.com

## Project Structure

```
├── config.py                # Environment-driven configuration
├── models.py                # Pydantic data models
├── scraper.py               # Facebook Marketplace vehicle scraping logic
├── real_estate_scraper.py   # Zillow / Redfin / Realtor.com scraping logic
├── main.py                  # FastAPI application
├── Procfile                 # Heroku entry point
└── requirements.txt         # Python dependencies
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

---

### Vehicle Endpoints

#### `POST /scrape`
Scrape vehicle listings from Facebook Marketplace.

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

#### `GET /scrape`
Same as POST but via query parameters:
```
GET /scrape?location=new-york-ny&vehicle_type=cars-trucks&max_price=15000
```

---

### Real-Estate Endpoints (Zillow · Redfin · Realtor.com)

#### `POST /real-estate/scrape`
Scrape property listings from Zillow, Redfin, and/or Realtor.com.

**Request body (JSON):**
```json
{
  "location":      "New York, NY",
  "min_price":     300000,
  "max_price":     800000,
  "min_beds":      2,
  "max_beds":      4,
  "property_type": "house",
  "max_results":   20,
  "source":        "all"
}
```

| Field           | Type    | Default        | Description                                              |
|-----------------|---------|----------------|----------------------------------------------------------|
| `location`      | string  | `New York, NY` | City and state                                           |
| `min_price`     | integer | —              | Minimum listing price (USD)                              |
| `max_price`     | integer | —              | Maximum listing price (USD)                              |
| `min_beds`      | integer | —              | Minimum number of bedrooms                               |
| `max_beds`      | integer | —              | Maximum number of bedrooms                               |
| `property_type` | string  | —              | e.g. `house`, `condo`, `townhouse`                       |
| `max_results`   | integer | `20`           | Maximum listings to return                               |
| `source`        | string  | `all`          | `zillow`, `redfin`, `realtor`, or `all`                  |

**Response:**
```json
{
  "success": true,
  "count": 6,
  "listings": [
    {
      "listing_id": "987654321",
      "address": "123 Main St, New York, NY 10001",
      "price": "$649,000",
      "beds": "3",
      "baths": "2",
      "sqft": "1,450",
      "property_type": null,
      "image_url": "https://...",
      "listing_url": "https://www.zillow.com/homedetails/...",
      "source": "zillow"
    }
  ]
}
```

#### `GET /real-estate/scrape`
Same as POST but via query parameters:
```
GET /real-estate/scrape?location=Austin%2C+TX&max_price=500000&min_beds=3&source=zillow
```

---

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
