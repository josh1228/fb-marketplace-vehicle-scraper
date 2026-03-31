import os

from dotenv import load_dotenv

load_dotenv()

SCRAPER_RATE_LIMIT = int(os.getenv('SCRAPER_RATE_LIMIT', 10))
SCRAPER_TIMEOUT = int(os.getenv('SCRAPER_TIMEOUT', 30))
SCRAPER_RETRIES = int(os.getenv('SCRAPER_RETRIES', 3))
API_HOST = os.getenv('API_HOST', 'localhost')
API_PORT = int(os.getenv('API_PORT', 8080))
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///:memory:')
USER_AGENT = os.getenv('USER_AGENT', 'fb-marketplace-scraper')

# Configuration settings for the scraper

