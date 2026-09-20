"""Tests for bank_matches eligibility helper."""

from datetime import date

from app.domain.eligibility import bank_matches
from app.domain.models import Offer

BASE = dict(
    offer_id="E-001",
    platform_id="MAKEMYTRIP",
    platform_name="MakeMyTrip",
    offer_title="Test offer",
    payment_method="CREDIT",
    category="FLIGHT_DOMESTIC",
    booking_channel="WEB_AND_APP",
    discount_type="FLAT",
    discount_value=500,
    valid_from=date(2026, 1, 1),
    expiry_date=date(2030, 12, 31),
    updated_at=date(2026, 1, 1),
    source_url="https://example.com",
    evidence_status="VERIFIED",
    publish_status="READY",
)


def make_offer(**kw) -> Offer:
    return Offer(**{**BASE, **kw})


class TestBankMatches:
    def test_none_filter_always_matches_any_offer(self):
        assert bank_matches(make_offer(bank_id="HDFC"), None)
        assert bank_matches(make_offer(bank_id=None), None)

    def test_matching_bank_id_returns_true(self):
        assert bank_matches(make_offer(bank_id="HDFC"), ["HDFC"])

    def test_non_matching_bank_id_returns_false(self):
        assert not bank_matches(make_offer(bank_id="HDFC"), ["SBI"])

    def test_match_is_case_insensitive(self):
        assert bank_matches(make_offer(bank_id="HDFC"), ["hdfc"])
        assert bank_matches(make_offer(bank_id="HDFC"), ["Hdfc"])

    def test_no_card_offer_excluded_by_non_null_filter(self):
        assert not bank_matches(make_offer(bank_id=None), ["HDFC"])

    def test_matches_any_bank_in_multi_bank_filter(self):
        assert bank_matches(make_offer(bank_id="SBI"), ["HDFC", "SBI"])
        assert not bank_matches(make_offer(bank_id="AXIS"), ["HDFC", "SBI"])

    def test_empty_filter_list_is_treated_as_no_filter(self):
        # bank_matches uses `not bank_ids` short-circuit — [] is falsy → all offers pass
        assert bank_matches(make_offer(bank_id="HDFC"), [])
