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
    assert {bank.id for bank in repo.get_metadata().banks} == {"HDFC", "ICICI", "SBI"}


def test_filters():
    repo = repository()
    offers = repo.list_offers(
        active_on=date(2026, 7, 12),
        platform_ids=["CLEARTRIP"],
        bank_ids=["HDFC"],
        payment_methods=["DEBIT"],
    )
    assert [offer.offer_id for offer in offers] == ["CT-HDFC-DEBIT-001"]


def test_expired_excluded():
    assert repository().list_offers(active_on=date(2030, 1, 1)) == []
