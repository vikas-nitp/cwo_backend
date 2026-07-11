import json
from pathlib import Path

from app.domain.models import OfferMetadata
from app.schemas.common import ErrorResponse
from app.schemas.offers import OffersResponse
from app.schemas.search import SearchResponse

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT / "contracts/examples" / name).read_text())


def test_examples_validate_against_schemas():
    OfferMetadata.model_validate(load("meta-response.json"))
    OffersResponse.model_validate(load("offers-response.json"))
    SearchResponse.model_validate(load("search-response.json"))
    ErrorResponse.model_validate(load("error-response.json"))


def test_openapi_is_current():
    from app.main import app

    committed = json.loads((ROOT / "contracts/openapi.json").read_text())
    assert committed == app.openapi()
