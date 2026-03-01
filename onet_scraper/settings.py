# Scrapy settings for onet_scraper project
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BOT_NAME = "onet_scraper"

SPIDER_MODULES = ["onet_scraper.spiders"]
NEWSPIDER_MODULE = "onet_scraper.spiders"

ADDONS = {}  # type: ignore

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# Using a standard browser UA to blend in (Works on Windows/Linux)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Concurrency and throttling settings
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 2  # Slower but safer for 24/7 server operation

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# Logging Configuration (Cross-platform compatible)
# Log to a file named 'scraper.log' in the project root
BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"

if not LOG_DIR.exists():
    LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = str(LOG_DIR / "scraper.log")
LOG_LEVEL = "INFO"

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    "onet_scraper.middlewares.TorMiddleware": 543,
}

# Tor Settings
TOR_PROXY = "socks5://127.0.0.1:9050"
TOR_CONTROL_PORT = 9051
TOR_PASSWORD = os.getenv("TOR_PASSWORD", "")
TOR_ENABLED = False  # Set to True when Tor is running (production). False = direct connection (testing)
TOR_CONNECTION_TIMEOUT = 30  # Timeout for Tor requests in seconds
TOR_MAX_RETRIES = 3

# Database Configuration
# Default: SQLite (zero-config, for local use)
# Production: set DATABASE_URL=postgresql://user:pass@host:5432/dbname in .env
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/articles.db")

# Configure item pipelines
ITEM_PIPELINES = {
    "onet_scraper.pipelines.PydanticValidationPipeline": 100,
    "onet_scraper.pipelines.DatabasePipeline": 300,
    # "onet_scraper.pipelines.JsonWriterPipeline": 400,  # Uncomment for JSONL export (debugging)
}

# Set settings whose default value is deprecated to a future-proof value
FEED_EXPORT_ENCODING = "utf-8"

# Usage of asyncio reactor for async middleware support
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
