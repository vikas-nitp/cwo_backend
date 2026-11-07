from datetime import date

from app.services.offer_catalog_service import OfferCatalogService
from tests.test_repository import repository

ACTIVE = date(2026, 10, 19)  # Monday — MAK-ICICI-5AFC813C (valid_days=[0]) is publishable


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
    # Snapshot covers all 7 platforms
    assert set(facets.platforms.keys()) == {"AIRINDIA", "CLEARTRIP", "EASEMYTRIP", "IXIGO", "MAKEMYTRIP", "PAYTM", "YATRA"}
    # MakeMyTrip has significantly more offers than Cleartrip
    assert facets.platforms["MAKEMYTRIP"]["count"] > facets.platforms["CLEARTRIP"]["count"]
    # ICICI is the top bank by offer count
    assert "ICICI" in facets.banks
    assert facets.banks["ICICI"]["count"] >= facets.banks["HDFC"]["count"]
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
    assert {offer.offer_id for offer in result.offers} == {
        "MAK-ICICI-5AFC813C",
        "MAK-AXIS-67A18B38",
    }
    assert all(offer.bank_id in {"ICICI", "AXIS"} for offer in result.offers)


def test_strict_catalogue_bank_filter_excludes_other_and_no_card():
    result = catalogue(banks=["ICICI"])
    assert {offer.bank_id for offer in result.offers} == {"ICICI"}


def test_self_excluding_counts_and_zero_disabled_options():
    # On 2026-10-19, MAKEMYTRIP+ICICI has 1 active offer; CLE has no ICICI offers
    result = catalogue(platforms=["MAKEMYTRIP"], banks=["ICICI"])
    platforms = by_id(result.facets.platforms)
    banks = by_id(result.facets.banks)
    assert platforms["MAKEMYTRIP"].count == 1
    assert platforms["CLEARTRIP"].count == 0  # CLE has no ICICI offers on this date
    assert banks["BOB"].count == 0  # MAK has no BOB offers on this date
    assert banks["BOB"].disabled is True
    assert banks["HDFC"].count == 1  # MAK-HDFC-095394FE is active on 2026-10-19
    assert banks["HDFC"].disabled is False
    assert banks["ICICI"].selected is True


def test_date_sensitive_counts():
    # No publishable offers exist after 2030-12-31
    result = catalogue(active_on=date(2031, 1, 1))
    assert result.pagination.total == 0
    assert all(option.disabled for option in result.facets.platforms)
