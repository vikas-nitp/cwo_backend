"""
Pydantic models for CardwiseOffer API
"""

import re
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


# ────────────────────────────────────────────────────────────────────
# Validation Constants
# ────────────────────────────────────────────────────────────────────

AIRPORT_CODE_PATTERN = re.compile(r"^[A-Z]{3}$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MAX_BANKS = 2        # Max cards user can select (strict limit)
MAX_PLATFORMS = 5
MAX_STRING_LENGTH = 100


# ────────────────────────────────────────────────────────────────────
# Offer Models
# ────────────────────────────────────────────────────────────────────

class Offer(BaseModel):
    """Core offer model from Excel/DB"""
    offer_id: str
    bank: str
    card_name: str = ""
    platform: str
    category: str
    payment_method: Literal["CREDIT", "DEBIT", "NO_CARD"]
    discount_type: Literal["FLAT", "PERCENT"]
    discount_value: float = 0
    max_discount: float = 0
    min_txn: float = 0
    coupon_code: str = ""
    valid_from: str
    valid_to: str
    channels: str = "web+app"
    eligibility_notes: str = ""
    terms_url: str = ""
    priority_score: int = 0
    login_required: bool = False


class OfferCard(BaseModel):
    """Processed offer card for display"""
    offer_id: str
    label: str
    bank: str
    card_name: str = ""
    platform: str
    payment_method: str = ""
    category: str = ""
    coupon_code: str = ""
    discount_type: str = ""
    discount_value: float = 0
    max_discount: float = 0
    min_txn: float = 0
    final_price: int
    savings: int
    locked: bool = False
    reasons: List[str] = []
    cta_url: str = ""


# ────────────────────────────────────────────────────────────────────
# Search Models
# ────────────────────────────────────────────────────────────────────

class PriceStripItem(BaseModel):
    """Single day in 7-day price strip"""
    date: str
    price: int  # Best/lowest price
    prices: Optional[Dict[str, int]] = None  # All source prices


class SearchSummary(BaseModel):
    """Search result summary"""
    from_airport: str
    to_airport: str
    date: str
    base_fare: int


class SearchRequest(BaseModel):
    """Search request body with validation"""
    from_airport: str = Field(..., alias="from", min_length=3, max_length=3)
    to_airport: str = Field(..., alias="to", min_length=3, max_length=3)
    depart_date: str = Field(..., alias="date")
    banks: Optional[List[str]] = Field(default=None, max_length=MAX_BANKS)
    platforms: Optional[List[str]] = Field(default=None, max_length=MAX_PLATFORMS)
    payment_method: Optional[Literal["CREDIT", "DEBIT", "NO_CARD"]] = None
    category: Optional[str] = Field(default="flight_domestic", max_length=MAX_STRING_LENGTH)

    model_config = {"populate_by_name": True}

    @field_validator("from_airport", "to_airport", mode="before")
    @classmethod
    def validate_airport_code(cls, v: str) -> str:
        """Validate airport code is 3 uppercase letters."""
        if not isinstance(v, str):
            raise ValueError("Airport code must be a string")
        v = v.strip().upper()
        if not AIRPORT_CODE_PATTERN.match(v):
            raise ValueError("Airport code must be exactly 3 letters (e.g., DEL, BOM)")
        return v

    @field_validator("depart_date", mode="before")
    @classmethod
    def validate_date(cls, v: str) -> str:
        """Validate date is YYYY-MM-DD format."""
        if not isinstance(v, str):
            raise ValueError("Date must be a string")
        v = v.strip()
        if not DATE_PATTERN.match(v):
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v

    @field_validator("banks", mode="before")
    @classmethod
    def validate_banks(cls, v):
        """Validate banks list."""
        if v is None:
            return None
        if not isinstance(v, list):
            raise ValueError("Banks must be a list")
        if len(v) > MAX_BANKS:
            raise ValueError(f"Maximum {MAX_BANKS} banks allowed")
        return [str(b).strip()[:MAX_STRING_LENGTH] for b in v if b]

    @field_validator("platforms", mode="before")
    @classmethod
    def validate_platforms(cls, v):
        """Validate platforms list."""
        if v is None:
            return None
        if not isinstance(v, list):
            raise ValueError("Platforms must be a list")
        if len(v) > MAX_PLATFORMS:
            raise ValueError(f"Maximum {MAX_PLATFORMS} platforms allowed")
        return [str(p).strip()[:MAX_STRING_LENGTH] for p in v if p]


class SearchResponse(BaseModel):
    """Search response"""
    summary: SearchSummary
    strip7days: List[PriceStripItem]
    offers: List[OfferCard]


# ────────────────────────────────────────────────────────────────────
# Meta Models
# ────────────────────────────────────────────────────────────────────

class MetaResponse(BaseModel):
    """Meta data response"""
    banks: List[Dict[str, Any]]
    platforms: List[Dict[str, Any]]
    payment_methods: List[str]
    categories: List[str]
    airports: List[Dict[str, Any]]
    supported_banks: List[str] = []      # IDs of currently supported banks
    supported_platforms: List[str] = []  # IDs of currently supported platforms


# ────────────────────────────────────────────────────────────────────
# Auth Models
# ────────────────────────────────────────────────────────────────────

class AuthInfo(BaseModel):
    """Auth info response"""
    is_authenticated: bool
    user_type: str  # "authenticated" or "guest"
