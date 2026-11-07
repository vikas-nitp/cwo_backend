from datetime import date
from decimal import Decimal

import pytest

from app.domain.calculations import estimate_savings
from app.domain.models import Offer


def offer(**changes):
    data = {
        "offer_id": "X",
        "platform_id": "MAKEMYTRIP",
        "platform_name": "MakeMyTrip",
        "offer_title": "Offer",
        "payment_method": "CREDIT",
        "category": "FLIGHT_DOMESTIC",
        "booking_channel": "WEB",
        "discount_type": "PERCENT",
        "discount_value": "10",
        "max_discount": "500",
        "min_transaction": "1000",
        "valid_from": date(2026, 1, 1),
        "valid_to": date(2027, 1, 1),
        "source_url": "https://www.makemytrip.com/",
        "evidence_status": "VERIFIED",
        "publish_status": "READY",
    }
    data.update(changes)
    return Offer.model_validate(data)


def test_percentage_cap_and_final_amount():
    result = estimate_savings(offer(), Decimal("10000"))
    assert result.estimated_savings == Decimal("500")
    assert result.estimated_final_amount == Decimal("9500")


def test_flat_never_makes_final_negative():
    result = estimate_savings(
        offer(
            discount_type="FLAT",
            discount_value="5000",
            max_discount=None,
            min_transaction=None,
        ),
        Decimal("100"),
    )
    assert result.estimated_savings == Decimal("100")
    assert result.estimated_final_amount == 0


def test_no_amount_has_no_estimate():
    result = estimate_savings(offer(), None)
    assert result.estimated_savings is None
    assert result.savings_label == "10% off, maximum ₹500"


def test_nonpositive_amount_rejected():
    with pytest.raises(ValueError):
        estimate_savings(offer(), Decimal("0"))


# ── ICICI EMI tiered offer fixture ────────────────────────────────────────────
# Tier 1: ₹5,000–₹24,999  → 12% off, cap ₹1,500
# Tier 2: ₹25,000–₹49,999 → Flat ₹1,500
# Tier 3: ₹50,000–₹74,999 → Flat ₹2,500
# Tier 4: ₹75,000+         → Flat ₹5,000

_ICICI_EMI_TIERS = [
    {"min_amount": 5000,  "max_amount": 24999, "discount_type": "PERCENT", "discount_value": 12, "max_discount": 1500},
    {"min_amount": 25000, "max_amount": 49999, "discount_type": "FLAT",    "discount_value": 1500, "max_discount": None},
    {"min_amount": 50000, "max_amount": 74999, "discount_type": "FLAT",    "discount_value": 2500, "max_discount": None},
    {"min_amount": 75000, "max_amount": None,  "discount_type": "FLAT",    "discount_value": 5000, "max_discount": None},
]


def tiered_offer(**changes):
    data = {
        "offer_id": "ICICI-EMI",
        "platform_id": "EASEMYTRIP",
        "platform_name": "EaseMyTrip",
        "offer_title": "ICICI EMI Offer",
        "payment_method": "CREDIT",
        "category": "FLIGHT_DOMESTIC",
        "booking_channel": "WEB",
        "discount_type": "PERCENT",
        "discount_value": "12",
        "max_discount": "1500",
        "min_transaction": "5000",
        "valid_from": date(2026, 1, 1),
        "valid_to": date(2027, 1, 1),
        "source_url": "https://www.easemytrip.com/",
        "evidence_status": "VERIFIED",
        "publish_status": "READY",
        "discount_tiers": _ICICI_EMI_TIERS,
    }
    data.update(changes)
    return Offer.model_validate(data)


def test_tiered_tier1_percent_below_cap():
    # ₹10,000 × 12% = ₹1,200 < ₹1,500 cap → ₹1,200
    result = estimate_savings(tiered_offer(), Decimal("10000"), tiered_discount_enabled=True)
    assert result.estimated_savings == Decimal("1200")
    assert result.estimated_final_amount == Decimal("8800")
    assert result.eligible is True


def test_tiered_tier1_percent_at_cap():
    # ₹20,000 × 12% = ₹2,400 > ₹1,500 cap → capped at ₹1,500
    result = estimate_savings(tiered_offer(), Decimal("20000"), tiered_discount_enabled=True)
    assert result.estimated_savings == Decimal("1500")
    assert result.estimated_final_amount == Decimal("18500")


def test_tiered_tier2_flat():
    # ₹30,000 → Tier 2 → Flat ₹1,500  (NOT ₹3,600 which the old percent formula gives)
    result = estimate_savings(tiered_offer(), Decimal("30000"), tiered_discount_enabled=True)
    assert result.estimated_savings == Decimal("1500")
    assert result.estimated_final_amount == Decimal("28500")


def test_tiered_tier3_flat():
    # ₹60,000 → Tier 3 → Flat ₹2,500
    result = estimate_savings(tiered_offer(), Decimal("60000"), tiered_discount_enabled=True)
    assert result.estimated_savings == Decimal("2500")
    assert result.estimated_final_amount == Decimal("57500")


def test_tiered_tier4_open_ended():
    # ₹100,000 → Tier 4 (open) → Flat ₹5,000
    result = estimate_savings(tiered_offer(), Decimal("100000"), tiered_discount_enabled=True)
    assert result.estimated_savings == Decimal("5000")
    assert result.estimated_final_amount == Decimal("95000")


def test_tiered_below_min_ineligible():
    # ₹4,000 → below Tier 1 → not eligible
    result = estimate_savings(tiered_offer(), Decimal("4000"), tiered_discount_enabled=True)
    assert result.estimated_savings == Decimal("0")
    assert result.eligible is False


def test_tiered_ff_disabled_uses_scalar():
    # When FF is off, falls back to old scalar logic: ₹30,000 × 12% = ₹3,600 (capped at ₹1,500 because max_discount=1500)
    result = estimate_savings(tiered_offer(), Decimal("30000"), tiered_discount_enabled=False)
    assert result.estimated_savings == Decimal("1500")
    assert result.estimated_final_amount == Decimal("28500")
