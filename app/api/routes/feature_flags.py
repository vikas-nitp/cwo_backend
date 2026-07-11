from fastapi import APIRouter

router = APIRouter(tags=["Feature flags"])


@router.get("/feature-flags")
def feature_flags() -> dict[str, bool]:
    return {
        "authEnabled": False,
        "offerLockingEnabled": False,
        "savedCards": False,
        "allOffers": True,
        "dailyVisitorsEnabled": False,
    }
