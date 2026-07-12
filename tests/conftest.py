from datetime import date
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(
        "app.services.offer_search_service.today_ist", lambda: date(2026, 7, 13)
    )
    monkeypatch.setattr("app.api.routes.offers.today_ist", lambda: date(2026, 7, 13))
    monkeypatch.setattr("app.api.routes.health.today_ist", lambda: date(2026, 7, 13))
    with TestClient(app) as value:
        yield value


@pytest.fixture
def valid_search():
    return {
        "from": "DEL",
        "to": "BLR",
        "date": date(2026, 7, 13).isoformat(),
        "banks": ["HDFC"],
    }
