import os
import sys
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROOT = Path(__file__).resolve().parents[1]

# Point tests at the committed fixture data in data/snapshots/ rather than the
# gitignored cardsage-generated output in data/generated/.
os.environ.setdefault("OFFERS_SNAPSHOT_PATH", str(ROOT / "data/snapshots/offers.snapshot.json"))
os.environ.setdefault("METADATA_SNAPSHOT_PATH", str(ROOT / "data/snapshots/metadata.snapshot.json"))
os.environ.setdefault("FACETS_SNAPSHOT_PATH", str(ROOT / "data/snapshots/facets.snapshot.json"))
os.environ.setdefault("MANIFEST_PATH", str(ROOT / "data/snapshots/manifest.json"))

from app.main import app  # noqa: E402  (must come after env vars are set)


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr("app.services.offer_search_service.today_ist", lambda: date(2026, 10, 19))
    monkeypatch.setattr("app.api.routes.offers.today_ist", lambda: date(2026, 10, 19))
    monkeypatch.setattr("app.api.routes.health.today_ist", lambda: date(2026, 10, 19))
    with TestClient(app) as value:
        yield value


@pytest.fixture
def valid_search():
    return {
        "from": "DEL",
        "to": "BLR",
        "date": date(2026, 10, 19).isoformat(),
        "banks": ["HDFC"],
    }
