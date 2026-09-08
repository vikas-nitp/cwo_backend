import csv
import json

import pytest
from openpyxl import Workbook

from app.ingestion.sources import SourceSpec, read_source
from scripts.build_offer_snapshot import build_catalogue, normalize_row


def canonical(identifier="X"):
    return {
        "offer_id": identifier,
        "offer_title": "Offer",
        "payment_method": "CREDIT",
        "category": "FLIGHT_DOMESTIC",
        "booking_channel": "WEB",
        "discount_type": "FLAT",
        "discount_value": 100,
        "valid_from": "2026-01-01",
        "valid_to": "2027-01-01",
        "source_url": "https://www.makemytrip.com/",
        "evidence_status": "VERIFIED",
        "publish_status": "READY",
        "is_active": True,
        "custom_field": "preserved",
    }


def test_csv_and_utf8_bom(tmp_path):
    path = tmp_path / "offers.csv"
    fields = list(canonical())
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow(canonical())
    spec = SourceSpec(path, "csv", "MAKEMYTRIP", "MakeMyTrip")
    records = read_source(spec, tmp_path)
    normalized = normalize_row(records[0].data, spec)
    assert normalized["platform_id"] == "MAKEMYTRIP"
    assert normalized["extra"]["custom_field"] == "preserved"


def test_json_array_and_offers_object(tmp_path):
    for index, payload in enumerate(([canonical()], {"offers": [canonical()]})):
        path = tmp_path / f"offers-{index}.json"
        path.write_text(json.dumps(payload))
        records = read_source(
            SourceSpec(path, "json", "MAKEMYTRIP", "MakeMyTrip"), tmp_path
        )
        assert records[0].data["offer_id"] == "X"


def test_invalid_json_shape(tmp_path):
    path = tmp_path / "offers.json"
    path.write_text(json.dumps({"wrong": []}))
    with pytest.raises(ValueError, match="unsupported JSON shape"):
        read_source(SourceSpec(path, "json", "MAKEMYTRIP", "MakeMyTrip"), tmp_path)


def test_excel_and_missing_sheet(tmp_path):
    path = tmp_path / "offers.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "offers"
    sheet.append(list(canonical()))
    sheet.append(list(canonical().values()))
    workbook.save(path)
    records = read_source(
        SourceSpec(path, "xlsx", "MAKEMYTRIP", "MakeMyTrip", "offers"), tmp_path
    )
    assert records[0].sheet == "offers"
    with pytest.raises(ValueError, match="not found"):
        read_source(
            SourceSpec(path, "xlsx", "MAKEMYTRIP", "MakeMyTrip", "missing"), tmp_path
        )


def test_platform_conflict():
    with pytest.raises(ValueError, match="conflicts"):
        normalize_row(
            {**canonical(), "platform_id": "CLEARTRIP"},
            SourceSpec(
                __import__("pathlib").Path("x"), "json", "MAKEMYTRIP", "MakeMyTrip"
            ),
        )


def test_duplicate_ids_across_formats_fail_with_locations(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    csv_path = source / "a.csv"
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(canonical()))
        writer.writeheader()
        writer.writerow(canonical())
    (source / "b.json").write_text(json.dumps([canonical()]))
    (source / "catalogue.yml").write_text(
        """sources:\n  - {path: a.csv, format: csv, platform_id: MAKEMYTRIP, platform_name: MakeMyTrip}\n  - {path: b.json, format: json, platform_id: MAKEMYTRIP, platform_name: MakeMyTrip}\n"""
    )
    output = tmp_path / "generated"
    assert build_catalogue(source / "catalogue.yml", output) == 1
    report = json.loads((output / "validation-report.json").read_text())
    error = report["errors"][0]
    assert error["source"] == "b.json"
    assert error["location"] == 0
    assert error["code"] == "DUPLICATE_OFFER_ID"
    assert "duplicate offer_id" in error["message"]
