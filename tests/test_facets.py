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
    # MakeMyTrip banks are a superset of the core banks (new pipeline data)
    assert {"BOB", "HDFC", "ICICI", "INDUSIND", "KOTAK"} <= set(facets.platforms["MAKEMYTRIP"]["banks"])
    assert facets.platforms["CLEARTRIP"]["payment_methods"] == ["CREDIT", "NO_CARD"]
    assert "MAKEMYTRIP" in facets.banks["HDFC"]["platforms"]
    assert "CREDIT" in facets.banks["HDFC"]["payment_methods"]


def test_or_within_and_and_across_groups():
    result = catalogue(
        platforms=["MAKEMYTRIP"],
        banks=["ICICI", "BOB"],
        payment_methods=["CREDIT"],
    )
    assert {offer.offer_id for offer in result.offers} == {
        "MAK-ICICI-9DD070",
        "MAK-BOB-FC049E",
    }
    assert all(offer.bank_id in {"ICICI", "BOB"} for offer in result.offers)


def test_strict_catalogue_bank_filter_excludes_other_and_no_card():
    result = catalogue(banks=["ICICI"])
    assert {offer.bank_id for offer in result.offers} == {"ICICI"}


def test_self_excluding_counts_and_zero_disabled_options():
    # On 2026-07-12, MAKEMYTRIP+ICICI has 1 active offer; HDFC not yet active (starts 2026-09-01)
    result = catalogue(platforms=["MAKEMYTRIP"], banks=["ICICI"])
    platforms = by_id(result.facets.platforms)
    banks = by_id(result.facets.banks)
    assert platforms["MAKEMYTRIP"].count == 1
    assert platforms["CLEARTRIP"].count == 1  # CLE-ICICI-6CD8C2 (intl) is active
    assert banks["BOB"].count == 1  # MAK-BOB-FC049E active on MMT
    assert banks["HDFC"].count == 0  # MAK-HDFC-9D4C28 starts 2026-09-01
    assert banks["HDFC"].disabled is True
    assert banks["ICICI"].selected is True


def test_date_sensitive_counts():
    # IXI-AUBANK-A64E9C expires 2030-12-31 — no offers active after that
    result = catalogue(active_on=date(2031, 1, 1))
    assert result.pagination.total == 0
    assert all(option.disabled for option in result.facets.platforms)
