# fb-marketplace-vehicle-scraper

> **Educational purposes only.**  
> Scraping Facebook Marketplace may violate Facebook's Terms of Service. Review and comply with the platform's terms before using this project.

## Overview

This project has two components:

1. **Chrome Extension** – A feature-rich browser extension that runs directly inside Chrome, scanning Facebook Marketplace in real time, scoring every listing, and surfacing the best car deals automatically.
2. **FastAPI Backend** – A REST API that scrapes vehicle listings from Facebook Marketplace using `requests` and `BeautifulSoup4` (server-side companion, optional).

---

## 🚗 Chrome Extension

### Features

| Feature | Description |
|---|---|
| **Auto-Scan** | Configurable alarm (1–1440 min) that triggers a scan of any open Marketplace tab or opens a new one automatically |
| **Deal Scoring** | Every listing is scored 0–100 based on price, model year, and mileage |
| **Hot-Deal Badges** | Green/amber/red badges are injected directly onto listing cards on the Marketplace page |
| **Desktop Notifications** | Chrome notification fires whenever a new hot deal (above your threshold) is detected |
| **Deals Tab** | Sortable, filterable list of all stored deals with thumbnails and score pills |
| **Filters** | Set max price, min year, max mileage, keyword, score threshold, and scan interval |
| **Price Analyser** | Live stats: count, avg/min/max price, avg score, hot-deal count |
| **Deal Score Calculator** | Enter any price/year/mileage to instantly preview its deal score |
| **Export to CSV** | One-click download of all stored deals as a spreadsheet |
| **Open Marketplace** | Open any FB Marketplace category + location with your saved filters pre-applied |
| **Compare Deals** | Side-by-side comparison table for up to 3 listings |
| **Price-Drop Tracker** | Highlights listings whose titles mention a price reduction |
| **Options Page** | Full settings page (auto-scan, thresholds, storage limit, notifications) |

### Installation (Developer Mode)

1. Clone or download this repository.
2. Open Chrome and navigate to `chrome://extensions/`.
3. Enable **Developer mode** (top-right toggle).
4. Click **Load unpacked** and select the `chrome-extension/` folder.
5. The 🚗 icon will appear in your toolbar.

### How to Use

1. Click the toolbar icon to open the popup.
2. Visit `facebook.com/marketplace/category/cars-trucks` (or any Marketplace vehicle search).
3. The extension automatically scans the page and injects deal-score badges onto every listing card.
4. Click **⟳ Scan** in the popup to manually trigger a scan.
5. Toggle **Auto** to enable periodic background scanning.
6. Use the **🔍 Filters** tab to narrow deals by price, year, mileage, and keyword.
7. Use the **🛠 Tools** tab for price analysis, CSV export, deal comparison, and more.
8. Click **⚙** to open full settings.

### Extension File Structure

```
chrome-extension/
├── manifest.json        # Manifest V3 extension definition
├── background.js        # Service worker: alarms, storage, notifications, scoring
├── content.js           # Injected into FB Marketplace: parses cards, injects badges
├── content.css          # Styles for injected badges
├── popup.html           # Extension popup UI
├── popup.css            # Popup styles
├── popup.js             # Popup logic (all tabs + tools)
├── options.html         # Full settings page
├── options.css          # Settings page styles
├── options.js           # Settings page logic
└── icons/
    ├── icon16.png
    ├── icon48.png
    └── icon128.png
```

---

## 🖥 FastAPI Backend (optional)

### Project Structure

```
├── config.py          # Environment-driven configuration
├── models.py          # Pydantic data models
├── scraper.py         # Core scraping logic
├── main.py            # FastAPI application
├── Procfile           # Heroku entry point
└── requirements.txt   # Python dependencies
```

## Setup

```bash
# Clone the repository
git clone https://github.com/josh1228/fb-marketplace-vehicle-scraper.git
cd fb-marketplace-vehicle-scraper

# Install Python dependencies (backend only)
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
