from datetime import date

from app.services.offer_catalog_service import OfferCatalogService
from tests.test_repository import repository

ACTIVE = date(2026, 7, 12)


def catalogue(**filters):
    defaults = {
        "active_on": ACTIVE,
        "banks": [],
        "platforms": [],
        "payment_methods": [],
        "booking_channels": [],
        "categories": [],
        "page": 1,
        "limit": 50,
    }
    defaults.update(filters)
    return OfferCatalogService(repository()).list(**defaults)


def by_id(options):
    return {item.id: item for item in options}


def test_generated_platform_bank_payment_relationships():
    facets = repository().get_facets()
    assert facets.platforms["MAKEMYTRIP"]["banks"] == ["HDFC", "SBI"]
    assert facets.platforms["CLEARTRIP"]["payment_methods"] == [
        "CREDIT",
        "DEBIT",
        "NO_CARD",
    ]
    assert facets.banks["HDFC"]["platforms"] == ["CLEARTRIP", "MAKEMYTRIP"]
    assert facets.banks["HDFC"]["payment_methods"] == ["CREDIT", "DEBIT"]


def test_or_within_and_and_across_groups():
    result = catalogue(
        platforms=["MAKEMYTRIP", "CLEARTRIP"],
        banks=["HDFC", "SBI"],
        payment_methods=["CREDIT"],
    )
    assert {offer.offer_id for offer in result.offers} == {
        "MMT-HDFC-001",
        "MMT-SBI-001",
    }
    assert all(offer.bank_id in {"HDFC", "SBI"} for offer in result.offers)


def test_strict_catalogue_bank_filter_excludes_other_and_no_card():
    result = catalogue(banks=["HDFC"])
    assert {offer.bank_id for offer in result.offers} == {"HDFC"}


def test_self_excluding_counts_and_zero_disabled_options():
    result = catalogue(platforms=["MAKEMYTRIP"], banks=["HDFC"])
    platforms = by_id(result.facets.platforms)
    banks = by_id(result.facets.banks)
    assert platforms["MAKEMYTRIP"].count == 1
    assert platforms["CLEARTRIP"].count == 1
    assert banks["SBI"].count == 1
    assert banks["ICICI"].count == 0
    assert banks["ICICI"].disabled is True
    assert banks["HDFC"].selected is True


def test_date_sensitive_counts():
    result = catalogue(active_on=date(2030, 1, 1))
    assert result.pagination.total == 0
    assert all(option.disabled for option in result.facets.platforms)
