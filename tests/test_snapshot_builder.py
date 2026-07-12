import csv
import json

import pytest
from pydantic import ValidationError

from app.domain.models import Offer
from scripts.build_offer_snapshot import build, normalize_row


def rows():
    return [
        {
            "offer_id": "X",
            "platform_id": "MAKEMYTRIP",
            "platform_name": "MakeMyTrip",
            "offer_title": "Offer",
            "payment_method": "CREDIT",
            "category": "FLIGHT_DOMESTIC",
            "booking_channel": "WEB",
            "discount_type": "FLAT",
            "discount_value": "100",
            "max_discount": "",
            "min_transaction": "0",
            "valid_from": "2026-01-01",
            "valid_to": "2027-01-01",
            "new_user_only": "false",
            "login_required": "false",
            "eligibility_notes": "One|Two",
            "source_url": "https://www.makemytrip.com/",
            "evidence_status": "VERIFIED",
            "priority_score": "1",
            "is_active": "true",
            "publish_status": "READY",
            "custom": "kept",
        }
    ]


def write_csv(path, items):
    fields = list(items[0])
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(items)


def test_valid_csv_preserves_blank_zero_and_extra(tmp_path):
    source, output = tmp_path / "offers.csv", tmp_path / "out"
    write_csv(source, rows())
    assert build(source, output) == 0
    offer = json.loads((output / "offers.snapshot.json").read_text())[0]
    assert offer["max_discount"] is None
    assert offer["min_transaction"] == 0
    assert offer["extra"] == {"custom": "kept"}
    report = json.loads((output / "validation-report.json").read_text())
    assert report["sources"][0]["path"] == "offers.csv"


def test_duplicate_and_invalid_platform_fail_with_report(tmp_path):
    source, output = tmp_path / "offers.csv", tmp_path / "out"
    items = rows() * 2
    items[0] = {**items[0], "platform_id": "GOIBIBO"}
    write_csv(source, items)
    assert build(source, output) == 1
    report = json.loads((output / "validation-report.json").read_text())
    assert report["valid"] is False
    assert report["errors"]


def test_aliases_are_resolved():
    row = rows()[0]
    row["bank"] = "hdfc"
    row["platform"] = row.pop("platform_id")
    row["min_txn"] = row.pop("min_transaction")
    data = normalize_row(row)
    assert data["bank_id"] == "HDFC"
    assert data["platform_id"] == "MAKEMYTRIP"
    assert data["min_transaction"] == "0"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("payment_method", "CASH"),
        ("discount_type", "BOGO"),
        ("source_url", "not-a-url"),
        ("discount_value", "-1"),
    ],
)
def test_invalid_canonical_values_are_rejected(field, value):
    row = {**rows()[0], field: value}
    with pytest.raises((ValidationError, ValueError)):
        Offer.model_validate(normalize_row(row))


def test_invalid_date_range_and_missing_required_are_rejected():
    with pytest.raises(ValidationError):
        Offer.model_validate(normalize_row({**rows()[0], "valid_from": "2028-01-01"}))
    with pytest.raises(ValueError, match="missing required"):
        normalize_row({**rows()[0], "offer_title": ""})
