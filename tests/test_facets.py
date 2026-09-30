from datetime import date

from app.services.offer_catalog_service import OfferCatalogService

ACTIVE = date(2026, 7, 12)


def catalogue(repository, **filters):
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
    return OfferCatalogService(repository).list(**defaults)


def by_id(options):
    return {item.id: item for item in options}


def test_generated_platform_bank_payment_relationships(repository):
    facets = repository.get_facets()
    assert {"AXIS", "BOB", "HDFC", "ICICI", "INDUSIND", "KOTAK"} <= set(facets.platforms["MAKEMYTRIP"]["banks"])
    assert facets.platforms["CLEARTRIP"]["payment_methods"] == ["CREDIT", "DEBIT", "NO_CARD"]
    assert "MAKEMYTRIP" in facets.banks["HDFC"]["platforms"]
    assert "CREDIT" in facets.banks["HDFC"]["payment_methods"]


def test_or_within_and_and_across_groups(repository):
    # MMT-AXIS-DEBIT-001 (DEBIT) and CT-ICICI-001 (other platform) must be excluded
    result = catalogue(
        repository,
        active_on=date(2026, 8, 15),
        platforms=["MAKEMYTRIP"],
        banks=["ICICI", "AXIS"],
        payment_methods=["CREDIT"],
    )
    assert {offer.offer_id for offer in result.offers} == {"MMT-ICICI-001", "MMT-AXIS-001"}
    assert all(offer.bank_id in {"ICICI", "AXIS"} for offer in result.offers)


def test_strict_catalogue_bank_filter_excludes_other_and_no_card(repository):
    result = catalogue(repository, banks=["ICICI"])
    assert {offer.bank_id for offer in result.offers} == {"ICICI"}


def test_self_excluding_counts_and_zero_disabled_options(repository):
    # On 2026-07-12, MAKEMYTRIP+ICICI has 1 active offer; BOB is not yet active (starts 2026-08-01)
    result = catalogue(repository, platforms=["MAKEMYTRIP"], banks=["ICICI"])
    platforms = by_id(result.facets.platforms)
    banks = by_id(result.facets.banks)
    assert platforms["MAKEMYTRIP"].count == 1
    assert platforms["CLEARTRIP"].count == 1  # CT-ICICI-001 is active
    assert banks["HDFC"].count == 1  # MMT-HDFC-001 is active on MMT
    assert banks["BOB"].count == 0  # MMT-BOB-001 starts 2026-08-01
    assert banks["BOB"].disabled is True
    assert banks["ICICI"].selected is True


def test_date_sensitive_counts(repository):
    # No offers are active after 2027-12-31
    result = catalogue(repository, active_on=date(2028, 1, 1))
    assert result.pagination.total == 0
    assert all(option.disabled for option in result.facets.platforms)
