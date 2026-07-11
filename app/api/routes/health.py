from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["Health"])


@router.get("/health/live")
def live() -> dict[str, bool]:
    return {"ok": True}


@router.get("/health/ready")
def ready(request: Request):
    repository = request.app.state.offer_repository
    if not repository.loaded:
        return JSONResponse(
            status_code=503,
            content={
                "ready": False,
                "data_loaded": False,
                "offer_count": 0,
                "data_version": None,
            },
        )
    manifest = repository.get_manifest()
    count = len(repository.list_offers(active_on=__import__("datetime").date.today()))
    if count == 0:
        return JSONResponse(
            status_code=503,
            content={
                "ready": False,
                "data_loaded": True,
                "offer_count": 0,
                "data_version": manifest.data_version,
            },
        )
    return {
        "ready": True,
        "data_loaded": True,
        "offer_count": count,
        "data_version": manifest.data_version,
    }
