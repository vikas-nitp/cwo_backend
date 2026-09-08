from fastapi import APIRouter, Request, Response

from app.api.headers import not_modified, version_headers
from app.api.errors import error_response
from app.core.config import SETTINGS
from app.domain.models import OfferMetadata

router = APIRouter(tags=["Meta"])


@router.get("/meta", response_model=OfferMetadata)
def meta(request: Request, response: Response):
    repository = request.app.state.offer_repository
    if not repository.loaded:
        return error_response(
            request, 503, "DATA_NOT_READY", "Offer data is not ready."
        )
    metadata = repository.get_metadata()
    etag = version_headers(
        response,
        version=metadata.data_version,
        cache_key="meta",
        cache_control=f"public, max-age={SETTINGS.meta_cache_ttl}",
    )
    if not_modified(request, etag):
        return Response(status_code=304, headers=dict(response.headers))
    return metadata
