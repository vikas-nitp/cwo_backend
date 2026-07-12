from app.core.dates import today_ist

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.core.config import CONTRACT_VERSION

router = APIRouter(tags=["Health"])


@router.get("/health/live")
def live() -> dict[str, bool]:
    return {"ok": True}


@router.get("/health/ready")
def ready(request: Request):
    repository = request.app.state.offer_repository
    flags = request.app.state.feature_flags
    if not repository.loaded or flags is None:
        return JSONResponse(
            status_code=503,
            content={
                "ready": False,
                "data_loaded": repository.loaded,
                "offer_count": 0,
                "active_offer_count": 0,
                "data_version": None,
                "feature_config_version": None,
                "contract_version": CONTRACT_VERSION,
                "error": "FEATURE_CONFIG_INVALID"
                if flags is None
                else "DATA_NOT_READY",
            },
            headers={"Cache-Control": "no-store"},
        )
    publishable = repository.list_publishable()
    active = repository.list_offers(active_on=today_ist())
    if not publishable:
        return JSONResponse(
            status_code=503,
            content={
                "ready": False,
                "data_loaded": True,
                "offer_count": 0,
                "active_offer_count": 0,
                "data_version": repository.get_manifest().data_version,
                "feature_config_version": flags.version(),
                "contract_version": CONTRACT_VERSION,
                "error": "DATA_NOT_READY",
            },
            headers={"Cache-Control": "no-store"},
        )
    manifest = repository.get_manifest()
    return {
        "ready": True,
        "data_loaded": True,
        "offer_count": len(publishable),
        "active_offer_count": len(active),
        "data_version": manifest.data_version,
        "feature_config_version": flags.version(),
        "contract_version": CONTRACT_VERSION,
    }
