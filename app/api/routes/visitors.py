import time
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["Visitors"])

_WINDOW_SECONDS = 120  # active = seen in last 2 minutes


def _evict(sessions: dict[str, float]) -> None:
    cutoff = time.monotonic() - _WINDOW_SECONDS
    stale = [k for k, t in sessions.items() if t < cutoff]
    for k in stale:
        del sessions[k]


@router.get("/visitors/count")
def visitor_count(request: Request):
    flags = request.app.state.feature_flags
    if flags is None or not flags.visitorCountEnabled:
        return JSONResponse(status_code=404, content={"error": {"code": "NOT_FOUND"}})

    sessions: dict[str, float] = request.app.state.visitor_sessions
    vid = request.query_params.get("v", "")
    if vid:
        sessions[vid[:64]] = time.monotonic()
    _evict(sessions)
    return {"count": len(sessions)}
