import json
from pathlib import Path

from app.core.feature_flags import FeatureFlagsResponse
from app.domain.models import OfferMetadata
from app.schemas.common import ErrorResponse
from app.schemas.offers import CatalogueFacets, OffersResponse, PublicOffer
from app.schemas.search import SearchOffer, SearchResponse

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
    assert set(PublicOffer.model_fields) <= set(SearchOffer.model_fields)


def test_public_offer_new_fields_default_to_none():
    """valid_days, evidence_status, source_url must all default to None."""
    from datetime import date

    offer = PublicOffer(
        offer_id="X1",
        platform_id="MAKEMYTRIP",
        platform_name="MakeMyTrip",
        offer_title="Test",
        payment_method="CREDIT",
        category="FLIGHT_DOMESTIC",
        booking_channel="WEB_AND_APP",
        discount_type="FLAT",
        discount_value=500,
        valid_from=date(2026, 1, 1),
        expiry_date=date(2026, 12, 31),
        updated_at=date(2026, 9, 1),
        new_user_only=False,
        eligibility_notes=[],
    )
    assert offer.valid_days is None
    assert offer.evidence_status is None
    assert offer.source_url is None


def test_public_offer_new_fields_roundtrip():
    """valid_days, evidence_status, source_url survive a model_validate cycle."""
    data = {
        "offer_id": "X2",
        "platform_id": "CLEARTRIP",
        "platform_name": "Cleartrip",
        "offer_title": "HDFC offer",
        "payment_method": "CREDIT",
        "category": "FLIGHT_DOMESTIC",
        "booking_channel": "WEB_AND_APP",
        "discount_type": "PERCENT",
        "discount_value": 15,
        "max_discount": 1200,
        "valid_from": "2026-01-01",
        "expiry_date": "2026-12-31",
        "updated_at": "2026-09-01",
        "new_user_only": False,
        "eligibility_notes": [],
        "valid_days": [1, 2, 3, 4, 5],
        "evidence_status": "VERIFIED",
        "source_url": "https://example.com/offer",
    }
    offer = PublicOffer.model_validate(data)
    assert offer.valid_days == [1, 2, 3, 4, 5]
    assert offer.evidence_status == "VERIFIED"
    assert offer.source_url == "https://example.com/offer"


def test_search_offer_inherits_new_fields():
    """SearchOffer also carries valid_days, evidence_status, source_url."""
    assert "valid_days" in SearchOffer.model_fields
    assert "evidence_status" in SearchOffer.model_fields
    assert "source_url" in SearchOffer.model_fields
