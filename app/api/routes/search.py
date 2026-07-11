from fastapi import APIRouter, Request

from app.api.errors import error_response
from app.schemas.search import SearchRequest, SearchResponse
from app.services.offer_search_service import OfferSearchService, SearchDateError

router = APIRouter(tags=["Search"])


@router.post("/search", response_model=SearchResponse)
def search(payload: SearchRequest, request: Request):
    try:
        return OfferSearchService(request.app.state.offer_repository).search(payload)
    except SearchDateError as exc:
        return error_response(request, 400, "INVALID_SEARCH_DATE", str(exc), "date")
