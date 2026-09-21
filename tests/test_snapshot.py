"""Tests for build_offer_snapshot.py demo data fallback and _has_rows helper."""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from scripts.build_offer_snapshot import _has_rows


# ── _has_rows ─────────────────────────────────────────────────────────────────

def test_has_rows_absent(tmp_path):
    """A file that does not exist is treated as having no rows."""
    assert _has_rows(tmp_path / "nonexistent.csv") is False


def test_has_rows_empty_file(tmp_path):
    """An empty file (no header, no data) has no rows."""
    f = tmp_path / "empty.csv"
    f.write_text("")
    assert _has_rows(f) is False


def test_has_rows_header_only(tmp_path):
    """A CSV with only a header line has no data rows."""
    f = tmp_path / "header_only.csv"
    f.write_text("offer_id,platform_id,platform_name\n")
    assert _has_rows(f) is False


def test_has_rows_with_data(tmp_path):
    """A CSV with at least one data row returns True."""
    f = tmp_path / "with_data.csv"
    with f.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["offer_id", "platform_id"])
        writer.writeheader()
        writer.writerow({"offer_id": "TEST-001", "platform_id": "MAKEMYTRIP"})
    assert _has_rows(f) is True


# ── build fallback via build_catalogue ────────────────────────────────────────

_MINIMAL_ROW = {
    "offer_id": "DEMO-001",
    "platform_id": "MAKEMYTRIP",
    "platform_name": "MakeMyTrip",
    "offer_title": "Demo Offer",
    "payment_method": "CREDIT",
    "category": "FLIGHT_DOMESTIC",
    "booking_channel": "WEB_AND_APP",
    "discount_type": "FLAT",
    "discount_value": "500",
    "max_discount": "500",
    "min_transaction": "3000",
    "coupon_code": "DEMO",
    "valid_from": "2026-01-01",
    "valid_to": "2027-12-31",
    "new_user_only": "false",
    "login_required": "false",
    "eligibility_notes": "Demo offer terms apply",
    "terms_url": "https://www.makemytrip.com/promos/flight-offers.html",
    "source_url": "https://www.makemytrip.com/promos/flight-offers.html",
    "source_type": "official",
    "evidence_status": "VERIFIED",
    "last_verified_at": "2026-09-01",
    "priority_score": "80",
    "is_active": "true",
    "publish_status": "READY",
}


def _write_csv(path: Path, rows: list[dict]) -> None:
    fields = list(rows[0])
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _write_catalogue(source_dir: Path, filename: str) -> Path:
    catalogue = source_dir / "catalogue.yml"
    catalogue.write_text(f"sources:\n  - path: {filename}\n    format: csv\n")
    return catalogue


def test_build_catalogue_uses_offers_csv_when_present(tmp_path):
    """When offers.csv has data, build_catalogue reads it (not demo_offers.csv)."""
    from scripts.build_offer_snapshot import build_catalogue

    source_dir = tmp_path / "source"
    source_dir.mkdir()
    output_dir = tmp_path / "out"

    offers_csv = source_dir / "offers.csv"
    _write_csv(offers_csv, [_MINIMAL_ROW])

    # demo_offers.csv also exists but with a different offer_id
    demo_row = {**_MINIMAL_ROW, "offer_id": "DEMO-FALLBACK"}
    _write_csv(source_dir / "demo_offers.csv", [demo_row])

    catalogue = _write_catalogue(source_dir, "offers.csv")

    rc = build_catalogue(catalogue, output_dir)
    assert rc == 0

    import json
    snapshot = json.loads((output_dir / "offers.snapshot.json").read_text())
    ids = [o["offer_id"] for o in snapshot]
    assert "DEMO-001" in ids
    assert "DEMO-FALLBACK" not in ids


def test_build_catalogue_falls_back_to_demo_when_offers_csv_empty(tmp_path):
    """When offers.csv exists but is header-only, fall back to demo_offers.csv."""
    from scripts.build_offer_snapshot import build_catalogue

    source_dir = tmp_path / "source"
    source_dir.mkdir()
    output_dir = tmp_path / "out"

    # offers.csv: header only — no data rows
    offers_csv = source_dir / "offers.csv"
    offers_csv.write_text(
        "offer_id,platform_id,platform_name,offer_title,payment_method,"
        "category,booking_channel,discount_type,discount_value,valid_from,"
        "valid_to,new_user_only,login_required,source_url,evidence_status,"
        "priority_score,is_active,publish_status\n"
    )

    demo_row = {**_MINIMAL_ROW, "offer_id": "DEMO-FALLBACK"}
    _write_csv(source_dir / "demo_offers.csv", [demo_row])

    catalogue = _write_catalogue(source_dir, "offers.csv")

    rc = build_catalogue(catalogue, output_dir)
    assert rc == 0

    import json
    snapshot = json.loads((output_dir / "offers.snapshot.json").read_text())
    ids = [o["offer_id"] for o in snapshot]
    assert "DEMO-FALLBACK" in ids


def test_build_catalogue_falls_back_to_demo_when_offers_csv_absent(tmp_path):
    """When offers.csv does not exist at all, fall back to demo_offers.csv."""
    from scripts.build_offer_snapshot import build_catalogue

    source_dir = tmp_path / "source"
    source_dir.mkdir()
    output_dir = tmp_path / "out"

    # No offers.csv; only demo_offers.csv
    demo_row = {**_MINIMAL_ROW, "offer_id": "DEMO-ABSENT-FALLBACK"}
    _write_csv(source_dir / "demo_offers.csv", [demo_row])

    catalogue = _write_catalogue(source_dir, "offers.csv")

    rc = build_catalogue(catalogue, output_dir)
    assert rc == 0

    import json
    snapshot = json.loads((output_dir / "offers.snapshot.json").read_text())
    ids = [o["offer_id"] for o in snapshot]
    assert "DEMO-ABSENT-FALLBACK" in ids
