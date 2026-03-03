"""
Search routes - handles offer search with card selection
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request

from app.models.schemas import Offer, SearchRequest, SearchResponse
from app.services import get_offers, get_platform_base_prices, get_feature_flags, OfferEngine
from app.core.config import MAX_CARD_SELECTION
from app.core.logging import get_logger

router = APIRouter(tags=["Search"])
offer_engine = OfferEngine()
logger = get_logger("app.routes.search")


def _parse_date(d: str):
    """Parse date string to date object"""
    try:
        return datetime.strptime(d, "%Y-%m-%d").date()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")


def _is_authenticated(request: Request) -> bool:
    """Check auth via x-user-auth header"""
    auth_header = request.headers.get("x-user-auth", "").lower().strip()
    return auth_header in ("1", "true", "yes", "on")


def _filter_offers(
    offers: List[Offer],
    travel_date,  # datetime.date object
    category: Optional[str] = None,
    platforms: Optional[List[str]] = None,
    payment_method: Optional[str] = None,
) -> List[Offer]:
    """
    Filter offers by eligibility (date, category, platform, payment).
    
    NOTE: Bank filtering is NOT done here - TileLabeler handles card selection logic
    to show "Best Offer" from other banks.
    
    ELIGIBILITY FILTERING:
    - Date: valid_from <= travel_date <= valid_to (strict)
    - Category: exact match (case-sensitive per backend canonical)
    - Payment: STRICT equality match (CREDIT/DEBIT/NO_CARD only)
    - Platform: if specified, include only those platforms (case-sensitive per backend)
    """
    filtered = []
    
    # Platforms: keep original case (backend canonical)
    platforms_set = set(platforms) if platforms else None
    
    # Payment method: normalize to uppercase for matching
    payment_upper = payment_method.upper() if payment_method else None
    
    for offer in offers:
        # ────────────────────────────────────────────────────────────
        # 1. DATE VALIDITY FILTER (strict: valid_from <= date <= valid_to)
        # ────────────────────────────────────────────────────────────
        try:
            valid_from = datetime.strptime(offer.valid_from, "%Y-%m-%d").date() if offer.valid_from else None
            valid_to = datetime.strptime(offer.valid_to, "%Y-%m-%d").date() if offer.valid_to else None
            
            if valid_from and travel_date < valid_from:
                continue  # Offer not yet active
            if valid_to and travel_date > valid_to:
                continue  # Offer expired
        except Exception:
            # Skip offers with invalid date format
            continue
        
        # ────────────────────────────────────────────────────────────
        # 2. CATEGORY FILTER (exact match, backend canonical case)
        # ────────────────────────────────────────────────────────────
        if category and offer.category != category:
            continue
        
        # ────────────────────────────────────────────────────────────
        # 3. PLATFORM FILTER (exact match, backend canonical case)
        # ────────────────────────────────────────────────────────────
        if platforms_set and offer.platform not in platforms_set:
            continue
        
        # ────────────────────────────────────────────────────────────
        # 4. PAYMENT METHOD FILTER (strict equality: CREDIT/DEBIT/NO_CARD)
        # ────────────────────────────────────────────────────────────
        if payment_upper:
            if offer.payment_method.upper() != payment_upper:
                continue
        
        filtered.append(offer)
    
    # Sort by priority score (descending), then valid_to (descending)
    filtered.sort(key=lambda x: (x.priority_score, x.valid_to), reverse=True)
    return filtered


@router.post("/search", response_model=SearchResponse)
def search(req: SearchRequest, request: Request):
    """
    Search for offers on a route.
    
    Card Selection Rules:
    - cards=[] → include all bank offers + default (Any)
    - cards=[X] → include X offers + default (Any)
    - cards=[X,Y] → include X,Y offers + default (Any)
    - Max 2 cards enforced (400 error if >2)
    
    Feature Flag Logic:
    - authEnabled=false → All offers visible (no concept of guest/locked)
    - authEnabled=true + offerLockingEnabled=false → All offers visible (no locking)
    - authEnabled=true + offerLockingEnabled=true + authenticated → All offers visible
    - authEnabled=true + offerLockingEnabled=true + guest → Lock offers beyond limit
    """
    # Validate card selection limit
    banks = req.banks or []
    # Remove duplicates while preserving order
    banks = list(dict.fromkeys(banks))
    if len(banks) > MAX_CARD_SELECTION:
        raise HTTPException(
            status_code=400, 
            detail=f"Maximum {MAX_CARD_SELECTION} cards can be selected. You selected {len(banks)}."
        )
    
    from_code = req.from_airport.upper()
    to_code = req.to_airport.upper()
    travel_date = _parse_date(req.depart_date)
    is_authenticated = _is_authenticated(request)
    
    # Get feature flags
    flags = get_feature_flags()
    auth_enabled = flags.get("authEnabled", True)
    offer_locking_enabled = flags.get("offerLockingEnabled", False)
    
    # If auth is disabled, locking is also disabled (no concept of guest)
    effective_locking = offer_locking_enabled and auth_enabled
    
    logger.debug(
        f"Search: {from_code}->{to_code} on {travel_date}, "
        f"auth={is_authenticated}, authEnabled={auth_enabled}, locking={effective_locking}"
    )
    
    raw_offers = get_offers()
    offers = [Offer(**o) for o in raw_offers]
    
    candidates = _filter_offers(
        offers=offers,
        travel_date=travel_date,
        category=req.category,
        platforms=req.platforms,
        payment_method=req.payment_method,
    )
    
    platform_prices = get_platform_base_prices()
    
    summary, price_strip, offer_cards = offer_engine.process_search(
        from_code=from_code,
        to_code=to_code,
        travel_date=travel_date,
        candidates=candidates,
        is_authenticated=is_authenticated,
        platform_prices=platform_prices,
        offer_locking_enabled=effective_locking,
        selected_banks=banks,  # Pass deduplicated banks for tile labeling
    )
    
    logger.debug(f"Found {len(offer_cards)} offers, base_fare={summary.base_fare}")
    
    return SearchResponse(
        summary=summary,
        strip7days=price_strip,
        offers=offer_cards,
    )
