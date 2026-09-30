from datetime import date


def test_startup_and_metadata_derivation(repository):
    assert repository.loaded
    assert len(repository.get_metadata().banks) == 14
    assert repository.get_metadata().availability_start == date(2026, 7, 1)
    assert repository.get_metadata().availability_end == date(2027, 12, 31)


def test_filters(repository):
    offers = repository.list_offers(
        active_on=date(2026, 7, 12),
        platform_ids=["MAKEMYTRIP"],
        bank_ids=["ICICI"],
        payment_methods=["CREDIT"],
    )
    assert [offer.offer_id for offer in offers] == ["MMT-ICICI-001"]


def test_expired_excluded(repository):
    # The latest-expiring offers end 2027-12-31; nothing is active after that
    assert repository.list_offers(active_on=date(2028, 1, 1)) == []
