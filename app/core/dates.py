from datetime import date, datetime
from zoneinfo import ZoneInfo

INDIA_TIMEZONE = ZoneInfo("Asia/Kolkata")


def today_ist() -> date:
    return datetime.now(INDIA_TIMEZONE).date()
