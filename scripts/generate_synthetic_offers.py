#!/usr/bin/env python3
"""Generate the deterministic cross-repository 1,000-offer test dataset."""

from __future__ import annotations

import csv
import json
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_TARGET = ROOT / "tests/fixtures/synthetic/offers.synthetic.1000.csv"
FRONTEND_TARGET = ROOT.parent / "cardwiseoffer/src/test/fixtures/synthetic/offers.synthetic.1000.json"
PLATFORMS = [(f"TEST_PLATFORM_{letter}", f"Test Platform {letter}") for letter in "ABCDE"]
BANKS = [(f"TEST_BANK_{index:02d}", f"Test Bank {index:02d}") for index in range(1, 11)]
CARDS = ["Test Regalia", "Test Diners Club", "Test Platinum", "Test Rewards", "Test Travel Card"]
DISCOUNTS = [("PERCENT", 5, 300), ("PERCENT", 7, 700), ("PERCENT", 10, 1500), ("PERCENT", 12, 900), ("PERCENT", 15, 2000), ("FLAT", 250, 250), ("FLAT", 500, 500), ("FLAT", 750, 750), ("FLAT", 1000, 1000), ("PERCENT", 20, None)]
MINIMUMS = [0, 1000, 2500, 5000, 7500, 10000, 15000, 20000]
CONDITIONS = ["New users only", "Monday only", "Weekend only", "App only", "Website only", "Credit card only", "Debit card only", "No card required"]
FIELDS = ["offer_id", "platform_id", "platform_name", "offer_title", "bank_id", "bank_name", "supported_cards", "payment_method", "category", "booking_channel", "discount_type", "discount_value", "max_discount", "min_transaction", "coupon_code", "valid_from", "valid_to", "usage_limit", "new_user_only", "login_required", "eligibility_notes", "terms_url", "source_url", "booking_url", "source_type", "evidence_status", "last_verified_at", "priority_score", "is_active", "publish_status", "data_classification", "is_test_data"]


def rows() -> list[dict[str, object]]:
    today = date(2026, 7, 12)
    result = []
    for index in range(1000):
        platform_id, platform_name = PLATFORMS[index % 5]
        no_card = index % 3 == 2
        bank_id, bank_name = ("", "") if no_card else BANKS[index % 10]
        payment = ("CREDIT", "DEBIT", "NO_CARD")[index % 3]
        discount_type, discount_value, cap = DISCOUNTS[index % len(DISCOUNTS)]
        state = index % 10
        valid_from = today - timedelta(days=30)
        valid_to = today + timedelta(days=30)
        active, publish, evidence = True, "READY", "VERIFIED"
        if state == 0:
            valid_to = today - timedelta(days=1)
        elif state == 1:
            valid_from = today + timedelta(days=1)
        elif state == 2:
            valid_to = today
        elif state == 3:
            publish = "DRAFT"
        elif state == 4:
            publish = "HIDDEN"
        elif state == 5:
            active = False
        elif state == 6:
            evidence = "UNVERIFIED"
        condition = CONDITIONS[index % len(CONDITIONS)]
        cards = "" if no_card else "|".join({CARDS[index % 5], CARDS[(index + 1) % 5]})
        result.append({"offer_id": f"SYNTH-{index + 1:04d}", "platform_id": platform_id, "platform_name": platform_name, "offer_title": f"Synthetic scenario offer {index + 1}", "bank_id": bank_id, "bank_name": bank_name, "supported_cards": cards, "payment_method": payment, "category": "FLIGHT_DOMESTIC", "booking_channel": ("WEB", "APP", "WEB_AND_APP")[index % 3], "discount_type": discount_type, "discount_value": discount_value, "max_discount": "" if cap is None else cap, "min_transaction": MINIMUMS[index % len(MINIMUMS)], "coupon_code": f"SYN{index + 1:04d}", "valid_from": valid_from.isoformat(), "valid_to": valid_to.isoformat(), "usage_limit": "Once per synthetic user", "new_user_only": condition == "New users only", "login_required": False, "eligibility_notes": condition, "terms_url": "https://example.test/terms", "source_url": "https://example.test/source", "booking_url": "https://example.test/book", "source_type": "synthetic_fixture", "evidence_status": evidence, "last_verified_at": today.isoformat(), "priority_score": (index * 17) % 101, "is_active": active, "publish_status": publish, "data_classification": "SYNTHETIC_TEST", "is_test_data": True})
    return result


if __name__ == "__main__":
    generated = rows()
    CSV_TARGET.parent.mkdir(parents=True, exist_ok=True)
    with CSV_TARGET.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(generated)
    FRONTEND_TARGET.parent.mkdir(parents=True, exist_ok=True)
    FRONTEND_TARGET.write_text(json.dumps(generated, indent=2) + "\n")
    print(f"Generated {len(generated)} synthetic offers across {len(PLATFORMS)} platforms and {len(BANKS)} banks")
