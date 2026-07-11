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
