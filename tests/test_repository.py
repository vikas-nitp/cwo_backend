from datetime import date
from pathlib import Path

from app.repositories.file_offer_repository import FileOfferRepository

ROOT = Path(__file__).resolve().parents[1]


def repository():
    repo = FileOfferRepository(
        ROOT / "data/generated/offers.snapshot.json",
        ROOT / "data/generated/metadata.snapshot.json",
        ROOT / "data/generated/manifest.json",
        ROOT / "data/generated/facets.snapshot.json",
    )
    repo.load()
    return repo


def test_startup_and_metadata_derivation():
    repo = repository()
    assert repo.loaded
    assert len(repo.get_metadata().banks) == 12
    assert repo.get_metadata().availability_end == date(2027, 3, 31)


def test_filters():
    repo = repository()
    offers = repo.list_offers(
        active_on=date(2026, 7, 12),
        platform_ids=["MAKEMYTRIP"],
        bank_ids=["ICICI"],
        payment_methods=["CREDIT"],
    )
    assert [offer.offer_id for offer in offers] == ["MAK-ICICI-9DD070"]


def test_expired_excluded():
    # MAK-KOTAK-919B61 is the last offer, expiring 2027-03-31; no offers exist after that date
    assert repository().list_offers(active_on=date(2031, 1, 1)) == []
