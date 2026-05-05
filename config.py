import os

SCRAPER_RATE_LIMIT = int(os.getenv('SCRAPER_RATE_LIMIT', '10'))
SCRAPER_TIMEOUT = int(os.getenv('SCRAPER_TIMEOUT', '30'))
SCRAPER_RETRIES = int(os.getenv('SCRAPER_RETRIES', '3'))
API_HOST = os.getenv('API_HOST', 'localhost')
API_PORT = int(os.getenv('API_PORT', '8080'))
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///:memory:')
USER_AGENT = os.getenv('USER_AGENT', 'fb-marketplace-scraper')

# TikTok ms_token cookie value obtained from a logged-in TikTok browser session.
# Optional but strongly recommended — without it TikTok is more likely to
# rate-limit or block requests.  Set via the TIKTOK_MS_TOKEN environment variable.
TIKTOK_MS_TOKEN = os.getenv('TIKTOK_MS_TOKEN')

# Optional HTTP/SOCKS proxy for TikTok requests, e.g. "http://user:pass@host:port"
TIKTOK_PROXY = os.getenv('TIKTOK_PROXY')
