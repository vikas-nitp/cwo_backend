from datetime import date
from pathlib import Path

from app.repositories.file_offer_repository import FileOfferRepository

ROOT = Path(__file__).resolve().parents[1]


def repository():
    repo = FileOfferRepository(
        ROOT / "data/snapshots/offers.snapshot.json",
        ROOT / "data/snapshots/metadata.snapshot.json",
        ROOT / "data/snapshots/manifest.json",
        ROOT / "data/snapshots/facets.snapshot.json",
    )
    repo.load()
    return repo


def test_startup_and_metadata_derivation():
    repo = repository()
    assert repo.loaded
    assert len(repo.get_metadata().banks) == 14
    assert repo.get_metadata().availability_end == date(2027, 12, 31)


def test_filters():
    repo = repository()
    # Fixture has MMT-ICICI-001 as the only ICICI+MAKEMYTRIP+CREDIT offer
    offers = repo.list_offers(
        active_on=date(2026, 10, 19),
        platform_ids=["MAKEMYTRIP"],
        bank_ids=["ICICI"],
        payment_methods=["CREDIT"],
    )
    assert [offer.offer_id for offer in offers] == ["MMT-ICICI-001"]


def test_expired_excluded():
    # Fixture offers expire 2027-12-31; no offers exist after that date
    assert repository().list_offers(active_on=date(2028, 1, 1)) == []
