import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import FEATURE_FLAGS_JSON

router = APIRouter(tags=["Feature flags"])


class FeatureFlagsResponse(BaseModel):
    phase2UserFeaturesEnabled: bool
    publicAllOffersEnabled: bool
    couponCodeEnabled: bool
    analyticsEnabled: bool
    bookingAmountComparisonEnabled: bool


@router.get("/feature-flags", response_model=FeatureFlagsResponse)
def feature_flags() -> FeatureFlagsResponse:
    try:
        with open(FEATURE_FLAGS_JSON) as f:
            data = json.load(f)
        return FeatureFlagsResponse(**data)
    except (FileNotFoundError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=503, detail="Feature flags unavailable") from exc
