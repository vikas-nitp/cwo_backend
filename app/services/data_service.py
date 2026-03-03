"""
Data Service - Loads data from files (Excel, JSON)

Data Sources:
- offers.xlsx: Only offers data (sheet: offers)
- airports.json: All airports
- feature_flags.json: Feature flags
"""

import json
import os
from typing import Any, Dict, List, Optional
import pandas as pd

from app.core.config import (
    DATA_DIR,
    OFFERS_EXCEL,
    AIRPORTS_JSON,
    AIRPORTS_EXCEL,
    FEATURE_FLAGS_JSON,
    DEFAULT_PLATFORM_PRICES,
)
from app.core.logging import get_logger

logger = get_logger("app.services.data")


# ────────────────────────────────────────────────────────────────────
# In-Memory Cache
# ────────────────────────────────────────────────────────────────────

_cache: Dict[str, Any] = {
    "offers": [],
    "airports": [],
    "feature_flags": {},
    "banks": [],
    "platforms": [],
    "loaded": False,
}


# ────────────────────────────────────────────────────────────────────
# Loaders
# ────────────────────────────────────────────────────────────────────

def _load_offers_from_excel() -> List[Dict[str, Any]]:
    """Load offers from Excel file"""
    if not os.path.exists(OFFERS_EXCEL):
        logger.warning(f"offers.xlsx not found at {OFFERS_EXCEL}")
        return []
    
    df = pd.read_excel(OFFERS_EXCEL, sheet_name="offers")
    df = df.fillna("")
    
    offers = []
    for _, row in df.iterrows():
        offer = {
            "offer_id": str(row.get("offer_id", "")).strip(),
            "bank": str(row.get("bank", "")).strip(),
            "card_name": str(row.get("card_name", "")).strip(),
            "platform": str(row.get("platform", "")).strip(),
            "category": str(row.get("category", "flight_domestic")).strip(),
            "payment_method": str(row.get("payment_method", "CREDIT")).strip().upper(),
            "discount_type": str(row.get("discount_type", "FLAT")).strip().upper(),
            "discount_value": float(row.get("discount_value", 0) or 0),
            "max_discount": float(row.get("max_discount", 0) or 0),
            "min_txn": float(row.get("min_txn", 0) or 0),
            "coupon_code": str(row.get("coupon_code", "")).strip(),
            "valid_from": _parse_date(row.get("valid_from", "")),
            "valid_to": _parse_date(row.get("valid_to", "")),
            "channels": str(row.get("channels", "web+app")).strip(),
            "eligibility_notes": str(row.get("eligibility_notes", "")).strip(),
            "terms_url": str(row.get("terms_url", "")).strip(),
            "priority_score": int(row.get("priority_score", 0) or 0),
            "login_required": _parse_bool(row.get("login_required", False)),
        }
        if offer["offer_id"]:
            offers.append(offer)
    
    return offers


def _load_airports_from_json() -> List[Dict[str, Any]]:
    """Load airports from JSON file, fallback to Excel if not found"""
    # Try JSON first
    if os.path.exists(AIRPORTS_JSON):
        with open(AIRPORTS_JSON, "r") as f:
            airports = json.load(f)
            if airports:
                return airports
    
    # Fallback to Excel
    logger.info("airports.json not found or empty, loading from Excel")
    return _load_airports_from_excel()


def _load_airports_from_excel() -> List[Dict[str, Any]]:
    """Load airports from Excel file"""
    if not os.path.exists(AIRPORTS_EXCEL):
        logger.warning(f"Airport Excel not found at {AIRPORTS_EXCEL}")
        return []
    
    try:
        df = pd.read_excel(AIRPORTS_EXCEL)
        df = df.fillna("")
        
        airports = []
        for _, row in df.iterrows():
            code = str(row.get("iata_code", row.get("code", ""))).strip().upper()
            if not code or len(code) != 3:
                continue
            
            airport = {
                "code": code,
                "city": str(row.get("city", "")).strip(),
                "name": str(row.get("airport_name", row.get("name", ""))).strip(),
                "country": str(row.get("country", "IN")).strip(),
                "is_domestic_default": True,
            }
            airports.append(airport)
        
        logger.info(f"Loaded {len(airports)} airports from Excel")
        return airports
        
    except Exception as e:
        logger.error(f"Error loading airports from Excel: {e}")
        return []


def _load_feature_flags_from_json() -> Dict[str, Any]:
    """Load feature flags from JSON file"""
    defaults = {
        "authEnabled": False,
        "offerLockingEnabled": False,
        "allOffers": True,
        "savedCards": False,
        "dailyVisitorsEnabled": True,
        "supported_banks": [],      # Empty = all banks supported
        "supported_platforms": [],  # Empty = all platforms supported
    }
    
    if not os.path.exists(FEATURE_FLAGS_JSON):
        logger.warning("feature_flags.json not found, using defaults")
        return defaults
    
    with open(FEATURE_FLAGS_JSON, "r") as f:
        flags = json.load(f)
    
    return {**defaults, **flags}


# Bank display names mapping (canonical code -> display name)
BANK_DISPLAY_NAMES = {
    "HDFC": "HDFC Bank",
    "ICICI": "ICICI Bank",
    "SBI": "SBI Card",
    "AXIS": "Axis Bank",
    "AMEX": "American Express",
    "KOTAK": "Kotak Mahindra",
    "YES": "Yes Bank",
    "INDUSIND": "IndusInd Bank",
    "RBL": "RBL Bank",
    "HSBC": "HSBC",
}


def _extract_banks(offers: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Extract unique banks from offers with proper display names"""
    seen = set()
    banks = []
    for offer in offers:
        bank = offer.get("bank", "").strip()
        if bank and bank.lower() != "any" and bank not in seen:
            seen.add(bank)
            # Use mapped display name or fallback to "{code} Bank"
            display_name = BANK_DISPLAY_NAMES.get(bank, f"{bank} Bank")
            banks.append({
                "id": bank,
                "name": display_name,
            })
    return sorted(banks, key=lambda x: x["id"])


def _extract_platforms(offers: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Extract unique platforms from offers"""
    seen = set()
    platforms = []
    for offer in offers:
        platform = offer.get("platform", "").strip()
        if platform and platform not in seen:
            seen.add(platform)
            platforms.append({"id": platform, "name": platform})
    return sorted(platforms, key=lambda x: x["id"])


# ────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────

def _parse_date(val: Any) -> str:
    """Convert date cell to YYYY-MM-DD string"""
    if pd.isna(val) or val == "":
        return ""
    if isinstance(val, str):
        return val.strip()
    if hasattr(val, "strftime"):
        return val.strftime("%Y-%m-%d")
    return str(val)


def _parse_bool(val: Any) -> bool:
    """Parse boolean values"""
    if isinstance(val, bool):
        return val
    if pd.isna(val):
        return False
    return str(val).strip().lower() in ("true", "1", "yes", "y", "on")


# ────────────────────────────────────────────────────────────────────
# Public API
# ────────────────────────────────────────────────────────────────────

def load_data(force: bool = False) -> None:
    """Load all data into cache"""
    global _cache
    
    if _cache["loaded"] and not force:
        return
    
    logger.info(f"Loading data from: {DATA_DIR}")
    
    # Load offers from Excel
    _cache["offers"] = _load_offers_from_excel()
    
    # Extract banks and platforms from offers
    _cache["banks"] = _extract_banks(_cache["offers"])
    _cache["platforms"] = _extract_platforms(_cache["offers"])
    
    # Load airports from JSON
    _cache["airports"] = _load_airports_from_json()
    
    # Load feature flags from JSON
    _cache["feature_flags"] = _load_feature_flags_from_json()
    
    _cache["loaded"] = True
    
    logger.info(
        f"Loaded: {len(_cache['offers'])} offers, "
        f"{len(_cache['banks'])} banks, "
        f"{len(_cache['platforms'])} platforms, "
        f"{len(_cache['airports'])} airports, "
        f"{len(_cache['feature_flags'])} flags"
    )


def reload_data() -> None:
    """Force reload data"""
    load_data(force=True)


def get_offers(filter_unsupported: bool = True) -> List[Dict[str, Any]]:
    """
    Get all offers, optionally filtering out unsupported banks/platforms.
    
    Args:
        filter_unsupported: If True, exclude offers from unsupported banks/platforms
    """
    if not _cache["loaded"]:
        load_data()
    
    offers = _cache["offers"]
    
    if not filter_unsupported:
        return offers
    
    # Get supported lists
    supported_banks = get_supported_banks()
    supported_platforms = get_supported_platforms()
    
    # Filter offers to only those from supported banks and platforms
    filtered = []
    for offer in offers:
        bank = offer.get("bank", "")
        platform = offer.get("platform", "")
        
        # If supported_banks is specified, filter by it
        if supported_banks and bank not in supported_banks:
            continue
        
        # If supported_platforms is specified, filter by it
        if supported_platforms and platform not in supported_platforms:
            continue
        
        filtered.append(offer)
    
    return filtered


def get_airports() -> List[Dict[str, Any]]:
    """Get all airports"""
    if not _cache["loaded"]:
        load_data()
    return _cache["airports"]


def get_banks() -> List[Dict[str, str]]:
    """Get all banks"""
    if not _cache["loaded"]:
        load_data()
    return _cache["banks"]


def get_platforms() -> List[Dict[str, str]]:
    """Get all platforms"""
    if not _cache["loaded"]:
        load_data()
    return _cache["platforms"]


def get_feature_flags() -> Dict[str, Any]:
    """Get feature flags"""
    if not _cache["loaded"]:
        load_data()
    return _cache["feature_flags"]


def get_supported_banks() -> List[str]:
    """Get list of supported bank IDs from feature flags"""
    flags = get_feature_flags()
    return flags.get("supported_banks", [])


def get_supported_platforms() -> List[str]:
    """Get list of supported platform IDs from feature flags"""
    flags = get_feature_flags()
    return flags.get("supported_platforms", [])


def get_meta() -> Dict[str, Any]:
    """Get all meta data with supported banks/platforms info"""
    if not _cache["loaded"]:
        load_data()
    
    # Get supported lists from feature flags
    supported_banks = get_supported_banks()
    supported_platforms = get_supported_platforms()
    
    # Filter banks to only supported ones (if specified)
    all_banks = _cache["banks"]
    if supported_banks:
        filtered_banks = [b for b in all_banks if b["id"] in supported_banks]
    else:
        filtered_banks = all_banks
    
    # Filter platforms to only supported ones (if specified)
    all_platforms = _cache["platforms"]
    if supported_platforms:
        filtered_platforms = [p for p in all_platforms if p["id"] in supported_platforms]
    else:
        filtered_platforms = all_platforms
    
    return {
        "banks": filtered_banks,
        "platforms": filtered_platforms,
        "payment_methods": ["CREDIT", "DEBIT", "NO_CARD"],
        "categories": ["flight_domestic", "flight_international", "hotel_domestic", "hotel_international"],
        "airports": _cache["airports"],
        "supported_banks": supported_banks,
        "supported_platforms": supported_platforms,
    }


def get_platform_base_prices() -> Dict[str, int]:
    """Get base prices per platform for price strip"""
    # Add any additional platforms from offers
    platforms = get_platforms()
    prices = DEFAULT_PLATFORM_PRICES.copy()
    
    for p in platforms:
        pid = p["id"]
        if f"{pid}_web" not in prices:
            prices[f"{pid}_web"] = 1550 + (sum(ord(c) for c in pid) % 100)
            prices[f"{pid}_app"] = prices[f"{pid}_web"] - 30
    
    return prices
