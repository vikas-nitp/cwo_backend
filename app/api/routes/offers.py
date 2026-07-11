from datetime import date
from typing import Literal

from fastapi import APIRouter, Query, Request

from app.schemas.offers import OffersResponse
from app.services.offer_catalog_service import OfferCatalogService

router = APIRouter(tags=["Offers"])


@router.get("/offers", response_model=OffersResponse)
def offers(
    request: Request,
    bank: str | None = None,
    platform: str | None = None,
    payment_method: Literal["CREDIT", "DEBIT", "NO_CARD"] | None = None,
    booking_channel: Literal["WEB", "APP", "WEB_AND_APP"] | None = None,
    category: Literal["FLIGHT_DOMESTIC"] | None = None,
    active_on: date = Query(default_factory=date.today),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
) -> OffersResponse:
    return OfferCatalogService(request.app.state.offer_repository).list(
        active_on=active_on,
        bank=bank,
        platform=platform,
        payment_method=payment_method,
        booking_channel=booking_channel,
        category=category,
        page=page,
        limit=limit,
    )
