"""
Core configuration and constants for CardwiseOffer Backend
"""

import os
from typing import List

# Environment
APP_ENV = os.getenv("APP_ENV", "dev")

# API Settings
API_PREFIX = "/api/v1"

# CORS - env var for prod, permissive for dev
_allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
CORS_ORIGINS: List[str] = (
    [o.strip() for o in _allowed_origins_env.split(",") if o.strip()]
    if _allowed_origins_env
    else [
        "http://localhost:8080",
        "http://localhost:5173",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:5173",
    ]
)


# Rate Limiting (env-configurable)
class RateLimitConfig:
    GLOBAL_LIMIT = int(os.getenv("RATE_LIMIT_GLOBAL", "30"))  # requests
    GLOBAL_WINDOW_SEC = int(os.getenv("RATE_LIMIT_GLOBAL_WINDOW", "60"))  # seconds
    SEARCH_LIMIT = int(os.getenv("RATE_LIMIT_SEARCH", "5"))  # requests
    SEARCH_WINDOW_SEC = int(os.getenv("RATE_LIMIT_SEARCH_WINDOW", "10"))  # seconds


# Data paths - cwo_backend/data/ folder (two levels up from app/core/)
DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data"
)
OFFERS_EXCEL = os.path.join(DATA_DIR, "offers.xlsx")
AIRPORTS_JSON = os.path.join(DATA_DIR, "airports.json")
AIRPORTS_EXCEL = os.path.join(DATA_DIR, "India_Domestic_Airports_Top100.xlsx")
FEATURE_FLAGS_JSON = os.path.join(DATA_DIR, "feature_flags.json")

# Immutable generated offer snapshots
OFFERS_SNAPSHOT_PATH = os.getenv(
    "OFFERS_SNAPSHOT_PATH", os.path.join(DATA_DIR, "generated", "offers.snapshot.json")
)
METADATA_SNAPSHOT_PATH = os.getenv(
    "METADATA_SNAPSHOT_PATH",
    os.path.join(DATA_DIR, "generated", "metadata.snapshot.json"),
)
MANIFEST_PATH = os.getenv(
    "MANIFEST_PATH", os.path.join(DATA_DIR, "generated", "manifest.json")
)
BOOKING_WINDOW_DAYS = int(os.getenv("BOOKING_WINDOW_DAYS", "10"))
SUPPORTED_PLATFORMS = tuple(
    value.strip().upper()
    for value in os.getenv("SUPPORTED_PLATFORMS", "MAKEMYTRIP,CLEARTRIP").split(",")
    if value.strip()
)


# Offer Engine Constants
class OfferEngineConfig:
    MIN_BASE_FARE = 1400
    MAX_BASE_FARE = 1850
    MIN_PRICE_VAR = 100
    MAX_PRICE_VAR = 300
    MIN_FINAL_PRICE = 999
    UNLOCKED_OFFERS_FOR_GUEST = 2


# Price Strip Configuration
class PriceStripConfig:
    STRIP_DAYS_COUNT = 7  # Number of days in price strip (always 7)
    DATE_FORMAT = "%Y-%m-%d"  # ISO date format
    PRICE_VAR_MIN = 100  # Minimum price variation
    PRICE_VAR_MAX = 300  # Maximum price variation


# Payment Method Constants (strict canonical values)
class PaymentMethodConfig:
    VALID_METHODS = ["CREDIT", "DEBIT", "NO_CARD"]
    DEFAULT_METHOD = "NO_CARD"


# Card Selection Limits
MAX_CARD_SELECTION = 2  # Max cards user can select

# Platform URLs
PLATFORM_URLS = {
    "MakeMyTrip": "https://www.makemytrip.com/",
    "Cleartrip": "https://www.cleartrip.com/",
    "Ixigo": "https://www.ixigo.com/",
    "Goibibo": "https://www.goibibo.com/",
}

# Default platform base prices (for 7-day strip)
DEFAULT_PLATFORM_PRICES = {
    "MakeMyTrip_web": 1575,
    "MakeMyTrip_app": 1545,
    "Ixigo_web": 1600,
    "Ixigo_app": 1565,
    "Cleartrip_web": 1580,
    "Cleartrip_app": 1550,
}
