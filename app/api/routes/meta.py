from fastapi import APIRouter, Request

from app.domain.models import OfferMetadata

router = APIRouter(tags=["Meta"])


@router.get("/meta", response_model=OfferMetadata)
def meta(request: Request) -> OfferMetadata:
    return request.app.state.offer_repository.get_metadata()
