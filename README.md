# fb-marketplace-vehicle-scraper

An educational implementation of a vehicle scraper for Facebook Marketplace, exposed as a REST API built with FastAPI and deployable to Heroku.

> **Note:** This project is for educational purposes only. Automated scraping of Facebook Marketplace may violate Facebook's Terms of Service. Use responsibly.

## Project Structure

```
├── config.py        # Configuration via environment variables
├── models.py        # Pydantic data models
├── scraper.py       # Core scraping logic (requests + BeautifulSoup4)
├── main.py          # FastAPI application
├── Procfile         # Heroku process definition
└── requirements.txt # Python dependencies
```

## Setup

1. Clone the repository and install dependencies:

```bash
git clone https://github.com/josh1228/fb-marketplace-vehicle-scraper.git
cd fb-marketplace-vehicle-scraper
pip install -r requirements.txt
```

2. (Optional) Copy and configure environment variables:

```bash
cp .env.example .env
# Edit .env as needed
```

## Running Locally

```bash
python main.py
```

The API will start at `http://localhost:8080`. Visit `http://localhost:8080/docs` for the interactive Swagger UI.

### Example Request

```bash
curl -X POST http://localhost:8080/scrape \
  -H "Content-Type: application/json" \
  -d '{"location": "seattle", "query": "trucks", "max_results": 10}'
```

## Configuration

All settings are controlled via environment variables (see `config.py`):

| Variable            | Default                  | Description                        |
|---------------------|--------------------------|------------------------------------|
| `API_HOST`          | `localhost`              | Host to bind the API server        |
| `API_PORT`          | `8080`                   | Port to bind the API server        |
| `SCRAPER_RATE_LIMIT`| `10`                     | Max requests per second            |
| `SCRAPER_TIMEOUT`   | `30`                     | HTTP request timeout (seconds)     |
| `SCRAPER_RETRIES`   | `3`                      | Number of retry attempts           |
| `DATABASE_URL`      | `sqlite:///:memory:`     | Database connection string         |
| `USER_AGENT`        | `fb-marketplace-scraper` | User-Agent header for requests     |

## API Endpoints

| Method | Path      | Description                        |
|--------|-----------|------------------------------------|
| GET    | `/health` | Health-check                       |
| POST   | `/scrape` | Scrape vehicle listings            |

## Heroku Deployment

1. Create a new Heroku app:

```bash
heroku create your-app-name
```

2. Push to Heroku:

```bash
git push heroku main
```

3. Set environment variables:

```bash
heroku config:set SCRAPER_RATE_LIMIT=5
```

## Commit Signature Verification

### About vigilant mode

GitHub can display a verification status on every commit and tag to show whether the signature is trusted. By default:

- **Verified** — the commit is signed with a GPG, SSH, or S/MIME key that GitHub successfully verified.
- **Unverified** — the commit has a signature that could not be verified.
- No badge — the commit is unsigned and the committer has not enabled vigilant mode.

Enabling **vigilant mode** replaces the "no badge" state with an explicit **Unverified** badge on every unsigned commit or tag you push, giving reviewers stronger confidence that signed commits genuinely came from you.

With vigilant mode active, all of your commits and tags are marked with one of three statuses:

| Status | Description |
|---|---|
| **Verified** | The commit is signed, the signature was successfully verified, and the committer is the only author who has enabled vigilant mode. |
| **Partially verified** | The commit is signed and the signature was successfully verified, but the commit has an author who: (a) is not the committer and (b) has also enabled vigilant mode. The signature does not guarantee the author's consent, so the commit is only partially verified. |
| **Unverified** | Any of the following is true: the commit is signed but the signature could not be verified; the commit is not signed and the committer has enabled vigilant mode; or the commit is not signed and an author has enabled vigilant mode. |

> **Tip:** Only enable vigilant mode if you sign *all* of your commits and tags, and use a GitHub-verified email address as your committer email. Any unsigned commits you push afterwards will be explicitly marked **Unverified**.

### Enabling vigilant mode

1. In the upper-right corner of any page on GitHub, click your profile picture, then click **Settings**.
2. In the "Access" section of the sidebar, click **SSH and GPG keys**.
3. Under "Vigilant mode," select **Flag unsigned commits as unverified**.

