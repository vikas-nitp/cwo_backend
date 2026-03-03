"""
Offers routes - All offers catalog with filtering
"""

from typing import List, Literal, Optional

from fastapi import APIRouter, Query, HTTPException

from app.models.schemas import Offer
from app.services import get_offers
from app.core.config import PaymentMethodConfig

router = APIRouter(tags=["Offers"])


def _filter_offers(
    offers: List[Offer],
    category: Optional[str] = None,
    banks: Optional[List[str]] = None,
    platforms: Optional[List[str]] = None,
    payment_method: Optional[str] = None,
) -> List[Offer]:
    """Filter offers using strict equality matching"""
    filtered = []

    banks_upper = [b.upper() for b in banks] if banks else None
    platforms_lower = [p.lower() for p in platforms] if platforms else None
    category_lower = category.lower() if category else None
    payment_upper = payment_method.upper() if payment_method else None

    for offer in offers:
        # Category filter
        if category_lower and offer.category.lower() != category_lower:
            continue
        # Bank filter — canonical code, "Any" bank matches all
        if banks_upper:
            if offer.bank.upper() != "ANY" and offer.bank.upper() not in banks_upper:
                continue
        # Platform filter
        if platforms_lower and offer.platform.lower() not in platforms_lower:
            continue
        # Payment method filter (strict equality: CREDIT/DEBIT/NO_CARD)
        if payment_upper:
            if offer.payment_method.upper() != payment_upper:
                continue
        filtered.append(offer)

    filtered.sort(key=lambda x: (x.priority_score, x.valid_to), reverse=True)
    return filtered


def _slim_offer(offer: Offer) -> dict:
    """Return minimal offer fields for list views (reduces payload size)"""
    return {
        "offer_id": offer.offer_id,
        "bank": offer.bank,
        "card_name": offer.card_name,
        "platform": offer.platform,
        "category": offer.category,
        "payment_method": offer.payment_method,
        "discount_type": offer.discount_type,
        "discount_value": offer.discount_value,
        "max_discount": offer.max_discount,
        "min_txn": offer.min_txn,
        "coupon_code": offer.coupon_code,
        "valid_from": offer.valid_from,
        "valid_to": offer.valid_to,
        "priority_score": offer.priority_score,
        # Excluded: eligibility_notes, terms_url, channels, login_required
    }


@router.get("/offers")
def api_get_offers(
    bank: Optional[str] = Query(default=None),
    platform: Optional[str] = Query(default=None),
    payment: Optional[Literal["CREDIT", "DEBIT", "NO_CARD"]] = Query(default=None),
    category: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(default=50, ge=1, le=100, description="Items per page (max 100)"),
    slim: bool = Query(default=False, description="Return minimal fields to reduce payload"),
):
    """Get all offers with optional filtering and pagination
    
    Payment method filter: CREDIT, DEBIT, or NO_CARD (strict equality)
    """
    # Validate payment method if provided
    if payment and payment.upper() not in PaymentMethodConfig.VALID_METHODS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid payment method. Must be one of: {', '.join(PaymentMethodConfig.VALID_METHODS)}"
        )
    
    raw = get_offers()
    offers = [Offer(**o) for o in raw]
    
    banks = [bank] if bank else None
    platforms = [platform] if platform else None
    
    filtered = _filter_offers(
        offers,
        category=category,
        banks=banks,
        platforms=platforms,
        payment_method=payment,
    )
    
    # Pagination
    total = len(filtered)
    start = (page - 1) * limit
    end = start + limit
    paginated = filtered[start:end]
    
    # Slim response if requested
    result = [_slim_offer(o) for o in paginated] if slim else paginated
    
    return {
        "offers": result,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit,
        },
    }
