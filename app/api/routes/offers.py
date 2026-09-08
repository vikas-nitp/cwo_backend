from datetime import date

from fastapi import APIRouter, Query, Request, Response

from app.api.errors import error_response
from app.api.headers import not_modified, version_headers
from app.schemas.offers import OffersResponse
from app.services.offer_catalog_service import (
    OfferCatalogService,
    UnsupportedFilterError,
)
from app.core.config import SETTINGS
from app.core.dates import today_ist

router = APIRouter(tags=["Offers"])


@router.get(
    "/offers",
    response_model=OffersResponse,
    response_model_exclude_none=True,
)
def offers(
    request: Request,
    response: Response,
    bank: list[str] = Query(default=[]),
    platform: list[str] = Query(default=[]),
    payment_method: list[str] = Query(default=[]),
    booking_channel: list[str] = Query(default=[]),
    category: list[str] = Query(default=[]),
    active_on: date = Query(default_factory=today_ist),
    page: int = Query(1, ge=1),
    limit: int = Query(SETTINGS.default_page_limit, ge=1, le=SETTINGS.max_page_limit),
):
    flags = request.app.state.feature_flags
    if flags is None:
        return error_response(
            request,
            503,
            "FEATURE_CONFIG_INVALID",
            "Feature configuration is not ready.",
        )
    if not flags.publicAllOffersEnabled:
        return error_response(
            request,
            403,
            "FEATURE_DISABLED",
            "The All Offers catalogue is currently unavailable.",
        )
    repository = request.app.state.offer_repository
    if not repository.loaded:
        return error_response(
            request, 503, "DATA_NOT_READY", "Offer data is not ready."
        )
    version = repository.get_manifest().data_version
    etag = version_headers(
        response,
        version=version,
        cache_key=str(request.url),
        cache_control=f"public, max-age={SETTINGS.offers_cache_ttl}",
    )
    if not_modified(request, etag):
        return Response(status_code=304, headers=dict(response.headers))
    try:
        result = OfferCatalogService(repository).list(
            active_on=active_on,
            banks=bank,
            platforms=platform,
            payment_methods=payment_method,
            booking_channels=booking_channel,
            categories=category,
            page=page,
            limit=limit,
        )
        if not flags.couponCodeEnabled:
            result = result.model_copy(
                update={
                    "offers": [
                        offer.model_copy(update={"coupon_code": None})
                        for offer in result.offers
                    ]
                }
            )
        return result
    except UnsupportedFilterError as exc:
        code = (
            "UNSUPPORTED_PLATFORM"
            if str(exc).startswith("Unsupported platform")
            else "UNSUPPORTED_FILTER"
        )
        return error_response(request, 400, code, str(exc))
