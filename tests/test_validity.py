"""Tests for offer validity helpers, including valid_days day-of-week filter."""
from datetime import date

import pytest

from app.domain.models import Offer
from app.domain.validity import is_active_on_day, is_publishable

BASE = dict(
    offer_id="TEST-001",
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


def make_offer(**kwargs) -> Offer:
    return Offer(**{**BASE, **kwargs})


# ── is_active_on_day ─────────────────────────────────────────────────────────

class TestIsActiveOnDay:
    def test_none_means_every_day(self):
        offer = make_offer(valid_days=None)
        for weekday in range(7):
            # 2026-01-05 is Monday (0); offset each day
            day = date(2026, 1, 5 + weekday)
            assert is_active_on_day(offer, day), f"Expected valid on weekday {weekday}"

    def test_monday_only(self):
        offer = make_offer(valid_days=[0])  # Monday
        assert is_active_on_day(offer, date(2026, 1, 5))   # Monday ✓
        assert not is_active_on_day(offer, date(2026, 1, 6))  # Tuesday ✗
        assert not is_active_on_day(offer, date(2026, 1, 11))  # Sunday ✗

    def test_weekend_offer(self):
        offer = make_offer(valid_days=[5, 6])  # Sat=5, Sun=6
        assert is_active_on_day(offer, date(2026, 1, 10))   # Saturday ✓
        assert is_active_on_day(offer, date(2026, 1, 11))   # Sunday ✓
        assert not is_active_on_day(offer, date(2026, 1, 9))   # Friday ✗

    def test_midweek_offer(self):
        offer = make_offer(valid_days=[1, 2, 3])  # Tue, Wed, Thu
        assert is_active_on_day(offer, date(2026, 1, 6))    # Tuesday ✓
        assert not is_active_on_day(offer, date(2026, 1, 5))  # Monday ✗

    def test_empty_list_never_valid(self):
        # An empty list means no valid days — should never be active.
        offer = make_offer(valid_days=[])
        for weekday in range(7):
            day = date(2026, 1, 5 + weekday)
            assert not is_active_on_day(offer, day)


# ── is_publishable integrates valid_days ─────────────────────────────────────

class TestIsPublishableWithValidDays:
    def test_publishable_on_correct_weekday(self):
        offer = make_offer(valid_days=[0])  # Monday only
        assert is_publishable(offer, date(2026, 1, 5))   # Monday ✓

    def test_not_publishable_on_wrong_weekday(self):
        offer = make_offer(valid_days=[0])  # Monday only
        assert not is_publishable(offer, date(2026, 1, 6))  # Tuesday ✗

    def test_publishable_without_valid_days(self):
        offer = make_offer(valid_days=None)
        assert is_publishable(offer, date(2026, 6, 15))

    def test_not_publishable_if_expired_even_on_valid_day(self):
        offer = make_offer(valid_days=[0], expiry_date=date(2026, 1, 4))  # expires before Monday
        assert not is_publishable(offer, date(2026, 1, 5))

    def test_not_publishable_if_inactive(self):
        offer = make_offer(valid_days=None, is_active=False)
        assert not is_publishable(offer, date(2026, 1, 5))


# ── Model field validation ────────────────────────────────────────────────────

class TestValidDaysModelField:
    def test_defaults_to_none(self):
        offer = make_offer()
        assert offer.valid_days is None

    def test_accepts_valid_list(self):
        offer = make_offer(valid_days=[0, 1, 2, 3, 4])
        assert offer.valid_days == [0, 1, 2, 3, 4]

    def test_accepts_empty_list(self):
        offer = make_offer(valid_days=[])
        assert offer.valid_days == []
