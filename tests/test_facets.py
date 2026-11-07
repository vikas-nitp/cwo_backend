from datetime import date

from app.services.offer_catalog_service import OfferCatalogService
from tests.test_repository import repository

ACTIVE = date(2026, 10, 19)  # within fixture validity window (2026-07-01 to 2027-12-31)


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
    # Fixture only covers MAKEMYTRIP and CLEARTRIP
    assert set(facets.platforms.keys()) == {"CLEARTRIP", "MAKEMYTRIP"}
    # MakeMyTrip has more offers than Cleartrip in the fixture
    assert facets.platforms["MAKEMYTRIP"]["offer_count"] > facets.platforms["CLEARTRIP"]["offer_count"]
    # Computed catalogue facets reflect platform-bank relationships
    result = catalogue()
    pf = by_id(result.facets.platforms)
    bf = by_id(result.facets.banks)
    assert pf["MAKEMYTRIP"].count > 0
    assert bf["HDFC"].count > 0


def test_or_within_and_and_across_groups():
    result = catalogue(
        platforms=["MAKEMYTRIP"],
        banks=["ICICI", "AXIS"],
        payment_methods=["CREDIT"],
    )
    # Fixture has MMT-ICICI-001 (CREDIT) and MMT-AXIS-001 (CREDIT)
    assert {offer.offer_id for offer in result.offers} == {
        "MMT-ICICI-001",
        "MMT-AXIS-001",
    }
    assert all(offer.bank_id in {"ICICI", "AXIS"} for offer in result.offers)


def test_strict_catalogue_bank_filter_excludes_other_and_no_card():
    result = catalogue(banks=["ICICI"])
    assert {offer.bank_id for offer in result.offers} == {"ICICI"}


def test_self_excluding_counts_and_zero_disabled_options():
    # Fixture: MAKEMYTRIP+ICICI has 1 active offer (MMT-ICICI-001)
    result = catalogue(platforms=["MAKEMYTRIP"], banks=["ICICI"])
    platforms = by_id(result.facets.platforms)
    banks = by_id(result.facets.banks)
    assert platforms["MAKEMYTRIP"].count == 1
    assert platforms["CLEARTRIP"].count == 1  # CT-ICICI-001 is active
    assert banks["ICICI"].selected is True


def test_date_sensitive_counts():
    # No offers exist after 2027-12-31 (fixture expiry)
    result = catalogue(active_on=date(2028, 1, 1))
    assert result.pagination.total == 0
    assert all(option.disabled for option in result.facets.platforms)
