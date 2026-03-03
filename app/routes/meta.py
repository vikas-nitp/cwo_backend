"""
Meta routes - Banks, Platforms, Airports, etc.
"""

from fastapi import APIRouter

from app.models.schemas import MetaResponse
from app.services import get_meta, get_feature_flags

router = APIRouter(tags=["Meta"])


@router.get("/meta", response_model=MetaResponse)
def api_get_meta():
    """Get all meta data (banks, platforms, airports, etc.)"""
    return get_meta()


@router.get("/feature-flags")
def api_get_feature_flags():
    """Get feature flags"""
    return get_feature_flags()
