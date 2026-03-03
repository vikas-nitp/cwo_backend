"""
Auth routes
"""

from fastapi import APIRouter, Request

from app.models.schemas import AuthInfo

router = APIRouter(tags=["Auth"])


def _is_authenticated(request: Request) -> bool:
    """Check auth via x-user-auth header"""
    auth_header = request.headers.get("x-user-auth", "").lower().strip()
    return auth_header in ("1", "true", "yes", "on")


@router.get("/auth-info", response_model=AuthInfo)
def get_auth_info(request: Request):
    """Get authentication info for current user"""
    is_auth = _is_authenticated(request)
    return AuthInfo(
        is_authenticated=is_auth,
        user_type="authenticated" if is_auth else "guest",
    )
