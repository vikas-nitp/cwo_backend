import json
from pathlib import Path

from app.domain.models import OfferMetadata
from app.schemas.common import ErrorResponse
from app.schemas.offers import CatalogueFacets, OffersResponse
from app.schemas.search import SearchResponse
from app.schemas.search import SearchOffer
from app.domain.models import Offer
from app.core.feature_flags import FeatureFlagsResponse

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT / "contracts/examples" / name).read_text())


def test_examples_validate_against_schemas():
    OfferMetadata.model_validate(load("meta-response.json"))
    OffersResponse.model_validate(load("offers-response.json"))
    SearchResponse.model_validate(load("search-response.json"))
    ErrorResponse.model_validate(load("error-response.json"))
    FeatureFlagsResponse.model_validate(load("feature-flags-response.json"))
    CatalogueFacets.model_validate(load("facets-response.json"))


def test_openapi_is_current():
    from app.main import app

    committed = json.loads((ROOT / "contracts/openapi.json").read_text())
    assert committed == app.openapi()


def test_search_and_catalogue_share_canonical_offer_fields():
    assert set(Offer.model_fields) <= set(SearchOffer.model_fields)
