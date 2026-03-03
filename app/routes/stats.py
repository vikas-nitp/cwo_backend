"""
Stats routes - Daily visitors and metrics
"""

from datetime import date
from fastapi import APIRouter

from app.core.middleware import visitor_tracker
from app.services import get_feature_flags

router = APIRouter(tags=["Stats"])


def _get_simulated_visitor_count() -> int:
    """
    Generate a realistic-looking visitor count for demo purposes.
    Uses date-based hash to return consistent number for the day.
    Returns ~1200-2000 visitors.
    """
    today = date.today().isoformat()
    hash_val = sum(ord(c) for c in today)
    return 1200 + (hash_val % 800)


@router.get("/stats/daily-visitors")
def get_daily_visitors():
    """
    Get daily visitor count (privacy-safe, no PII).
    Controlled by dailyVisitorsEnabled feature flag.
    Returns simulated count if real count is 0 (for demo).
    """
    flags = get_feature_flags()
    
    if not flags.get("dailyVisitorsEnabled", False):
        return {"date": None, "visitors": 0, "enabled": False}
    
    date_str, count = visitor_tracker.get_count()
    
    # Use simulated count if no real visitors yet (demo/dev mode)
    if count == 0:
        count = _get_simulated_visitor_count()
        date_str = date.today().isoformat()
    
    return {"date": date_str, "visitors": count, "enabled": True}
