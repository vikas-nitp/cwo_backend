from datetime import date
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as value:
        yield value


@pytest.fixture
def valid_search():
    return {
        "from": "DEL",
        "to": "BLR",
        "date": date.today().isoformat(),
        "banks": ["HDFC"],
        "booking_amount": 6500,
    }
