from fastapi import APIRouter, Request, Response

from app.api.errors import error_response
from app.schemas.search import SearchRequest, SearchResponse
from app.services.offer_search_service import OfferSearchService, SearchDateError

router = APIRouter(tags=["Search"])


@router.post(
    "/search",
    response_model=SearchResponse,
    response_model_exclude_none=True,
)
def search(payload: SearchRequest, request: Request, response: Response):
    try:
        repository = request.app.state.offer_repository
        if not repository.loaded:
            return error_response(
                request, 503, "DATA_NOT_READY", "Offer data is not ready."
            )
        flags = request.app.state.feature_flags
        if payload.booking_amount is not None and not flags.bookingAmountComparisonEnabled:
            return error_response(
                request,
                400,
                "BOOKING_COMPARISON_DISABLED",
                "Booking amount comparison is currently unavailable.",
                "booking_amount",
            )
        result = OfferSearchService(repository).search(payload)
        if not flags.couponCodeEnabled:
            result = result.model_copy(
                update={
                    "offers": [
                        offer.model_copy(update={"coupon_code": None})
                        for offer in result.offers
                    ]
                }
            )
        response.headers["X-Data-Version"] = repository.get_manifest().data_version
        response.headers["X-Contract-Version"] = "1.1"
        response.headers["Cache-Control"] = "no-store"
        return result
    except SearchDateError as exc:
        return error_response(request, 400, "INVALID_SEARCH_DATE", str(exc), "date")
