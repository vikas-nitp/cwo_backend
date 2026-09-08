from fastapi import APIRouter, Request, Response

from app.api.errors import error_response
from app.core.config import CONTRACT_VERSION, SETTINGS
from app.core.feature_flags import FeatureFlagsResponse

router = APIRouter(tags=["Feature flags"])


@router.get("/feature-flags", response_model=FeatureFlagsResponse)
def feature_flags(request: Request, response: Response):
    flags = request.app.state.feature_flags
    if flags is None:
        return error_response(
            request,
            503,
            "FEATURE_CONFIG_INVALID",
            "Feature configuration is not ready.",
        )
    etag = f'"flags-{flags.version()}"'
    response.headers["X-Contract-Version"] = CONTRACT_VERSION
    repository = request.app.state.offer_repository
    if repository.loaded:
        response.headers["X-Data-Version"] = repository.get_manifest().data_version
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = f"public, max-age={SETTINGS.flags_cache_ttl}"
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers=dict(response.headers))
    return FeatureFlagsResponse(**flags.model_dump(), config_version=flags.version())
