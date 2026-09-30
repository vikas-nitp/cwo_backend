import shutil
import sys
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.main import app  # noqa: E402
from app.repositories.file_offer_repository import FileOfferRepository  # noqa: E402
from scripts.build_offer_snapshot import build_catalogue  # noqa: E402

FIXTURE_CSV = ROOT / "tests/fixtures/offers.fixture.csv"
FROZEN_TODAY = date(2026, 7, 13)


@pytest.fixture(scope="session")
def snapshot_dir(tmp_path_factory) -> Path:
    """Build snapshots from the committed fixture CSV so tests never depend on pipeline output."""
    source = tmp_path_factory.mktemp("source")
    shutil.copy(FIXTURE_CSV, source / "offers.fixture.csv")
    catalogue = source / "catalogue.yml"
    catalogue.write_text("sources:\n  - path: offers.fixture.csv\n    format: csv\n")
    output = tmp_path_factory.mktemp("generated")
    assert build_catalogue(catalogue, output) == 0
    return output


@pytest.fixture
def repository(snapshot_dir) -> FileOfferRepository:
    repo = FileOfferRepository(
        snapshot_dir / "offers.snapshot.json",
        snapshot_dir / "metadata.snapshot.json",
        snapshot_dir / "manifest.json",
        snapshot_dir / "facets.snapshot.json",
    )
    repo.load()
    return repo


@pytest.fixture
def client(monkeypatch, snapshot_dir, tmp_path):
    monkeypatch.setattr("app.main.OFFERS_SNAPSHOT_PATH", str(snapshot_dir / "offers.snapshot.json"))
    monkeypatch.setattr("app.main.METADATA_SNAPSHOT_PATH", str(snapshot_dir / "metadata.snapshot.json"))
    monkeypatch.setattr("app.main.MANIFEST_PATH", str(snapshot_dir / "manifest.json"))
    monkeypatch.setattr("app.main.FACETS_SNAPSHOT_PATH", str(snapshot_dir / "facets.snapshot.json"))
    monkeypatch.setattr("app.core.config.USER_DATA_DIR", tmp_path)
    monkeypatch.setattr("app.services.offer_search_service.today_ist", lambda: FROZEN_TODAY)
    monkeypatch.setattr("app.api.routes.offers.today_ist", lambda: FROZEN_TODAY)
    monkeypatch.setattr("app.api.routes.health.today_ist", lambda: FROZEN_TODAY)
    with TestClient(app) as value:
        yield value


@pytest.fixture
def valid_search():
    return {
        "from": "DEL",
        "to": "BLR",
        "date": FROZEN_TODAY.isoformat(),
        "banks": ["HDFC"],
    }
