from datetime import date
from decimal import Decimal

from app.domain.calculations import estimate_savings
from app.domain.models import Offer
from app.domain.ranking import rank_offers


def offer(identifier, bank, method, value, priority=1):
    return Offer.model_validate(
        {
            "offer_id": identifier,
            "platform_id": "MAKEMYTRIP",
            "platform_name": "MakeMyTrip",
            "offer_title": identifier,
            "bank_id": bank,
            "bank_name": bank,
            "payment_method": method,
            "category": "FLIGHT_DOMESTIC",
            "booking_channel": "WEB",
            "discount_type": "FLAT",
            "discount_value": value,
            "valid_from": "2026-01-01",
            "valid_to": "2027-12-31",
            "source_url": "https://www.makemytrip.com/",
            "evidence_status": "VERIFIED",
            "priority_score": priority,
            "publish_status": "READY",
        }
    )


def ranked(selected):
    offers = [
        offer("H", "HDFC", "CREDIT", 500),
        offer("S", "SBI", "CREDIT", 700),
        offer("I", "ICICI", "CREDIT", 1000),
        offer("D", None, "NO_CARD", 300),
    ]
    return rank_offers(
        [(item, estimate_savings(item, Decimal("5000"))) for item in offers],
        selected,
        date(2026, 7, 12),
    )


def test_no_selection_returns_general_best_without_duplicates():
    result = ranked([])
    assert [item.display_kind for item in result] == ["GENERAL_BEST", "DEFAULT_OFFER"]
    assert len({item.offer.offer_id for item in result}) == len(result)


def test_one_selection_includes_better_alternative_and_default():
    assert [item.display_kind for item in ranked(["HDFC"])] == [
        "SELECTED_CARD",
        "BETTER_ALTERNATIVE",
        "DEFAULT_OFFER",
    ]


def test_two_selections_get_distinct_selected_kinds():
    kinds = [item.display_kind for item in ranked(["HDFC", "SBI"])]
    assert kinds[:2] == ["SELECTED_CARD", "SECOND_SELECTED_CARD"]
