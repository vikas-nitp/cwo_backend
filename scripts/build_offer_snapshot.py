#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pydantic import ValidationError  # noqa: E402
from app.domain.models import Offer  # noqa: E402

ALIASES = {
    "bank": "bank_id",
    "platform": "platform_id",
    "min_txn": "min_transaction",
    "valid_till": "valid_to",
    "coupon": "coupon_code",
    "active": "is_active",
}
CANONICAL_FIELDS = set(Offer.model_fields) - {"extra"}
REQUIRED = {
    "offer_id",
    "platform_id",
    "platform_name",
    "offer_title",
    "payment_method",
    "category",
    "booking_channel",
    "discount_type",
    "discount_value",
    "valid_from",
    "valid_to",
    "source_url",
    "evidence_status",
    "publish_status",
}
BOOL_FIELDS = {"new_user_only", "login_required", "is_active"}
NUMBER_FIELDS = {"discount_value", "max_discount", "min_transaction", "priority_score"}
NULLABLE = {
    name for name, field in Offer.model_fields.items() if not field.is_required()
}


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y"}:
        return True
    if normalized in {"0", "false", "no", "n"}:
        return False
    raise ValueError(f"invalid boolean: {value}")


def normalize_row(row: dict[str, str]) -> dict[str, Any]:
    aliased: dict[str, str] = {}
    for key, value in row.items():
        target = ALIASES.get(key.strip(), key.strip())
        if target not in aliased or not aliased[target].strip():
            aliased[target] = value.strip() if isinstance(value, str) else value
    missing = sorted(name for name in REQUIRED if not aliased.get(name, ""))
    if missing:
        raise ValueError(f"missing required field(s): {', '.join(missing)}")
    output: dict[str, Any] = {}
    extra: dict[str, Any] = {}
    for key, value in aliased.items():
        if key not in CANONICAL_FIELDS:
            if value != "":
                extra[key] = value
            continue
        if value == "" and key in NULLABLE:
            output[key] = None
        elif key in BOOL_FIELDS:
            output[key] = parse_bool(value)
        elif key in NUMBER_FIELDS:
            output[key] = value
        elif key == "eligibility_notes":
            output[key] = [item.strip() for item in value.split("|") if item.strip()]
        else:
            output[key] = value
    output["platform_id"] = output["platform_id"].upper().replace(" ", "")
    output["bank_id"] = output.get("bank_id").upper() if output.get("bank_id") else None
    output["payment_method"] = output["payment_method"].upper()
    output["category"] = output["category"].upper()
    output["booking_channel"] = output["booking_channel"].upper()
    output["discount_type"] = output["discount_type"].upper()
    output["evidence_status"] = output["evidence_status"].upper()
    output["publish_status"] = output["publish_status"].upper()
    output["extra"] = extra
    return output


def build(source: Path, output_dir: Path) -> int:
    rows = list(csv.DictReader(source.open(newline="", encoding="utf-8-sig")))
    accepted: list[Offer] = []
    errors: list[dict[str, Any]] = []
    seen: set[str] = set()
    for number, row in enumerate(rows, 2):
        try:
            data = normalize_row(row)
            if data["offer_id"] in seen:
                raise ValueError(f"duplicate offer_id: {data['offer_id']}")
            offer = Offer.model_validate(data)
            seen.add(offer.offer_id)
            accepted.append(offer)
        except (ValueError, ValidationError) as exc:
            errors.append(
                {"row": number, "offer_id": row.get("offer_id"), "error": str(exc)}
            )
    canonical = [offer.model_dump(mode="json") for offer in accepted]
    digest = hashlib.sha256(
        json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()[:12]
    version_date = max(
        (o.last_verified_at or o.valid_from for o in accepted),
        default=datetime.now(timezone.utc).date(),
    )
    generated_at = datetime.combine(
        version_date, datetime.min.time(), tzinfo=timezone.utc
    ).isoformat()
    data_version = f"{version_date.isoformat()}-{digest}"
    publishable = [
        o
        for o in accepted
        if o.is_active
        and o.publish_status == "READY"
        and o.evidence_status == "VERIFIED"
    ]
    banks = sorted(
        {(o.bank_id, o.bank_name or o.bank_id) for o in publishable if o.bank_id}
    )
    platforms = sorted({(o.platform_id, o.platform_name) for o in publishable})
    metadata = {
        "data_version": data_version,
        "banks": [{"id": i, "name": n} for i, n in banks],
        "platforms": [{"id": i, "name": n} for i, n in platforms],
        "payment_methods": sorted({o.payment_method for o in publishable}),
        "categories": sorted({o.category for o in publishable}),
        "booking_channels": sorted({o.booking_channel for o in publishable}),
        "airports": json.loads((ROOT / "data/airports.json").read_text()),
    }
    manifest = {
        "schema_version": "1.0",
        "data_version": data_version,
        "generated_at": generated_at,
        "source_row_count": len(rows),
        "accepted_row_count": len(accepted),
        "rejected_row_count": len(errors),
        "supported_platforms": ["MAKEMYTRIP", "CLEARTRIP"],
    }
    try:
        report_source = source.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        # Temporary/external catalogues still need deterministic reports.
        report_source = source.name
    report = {
        "valid": not errors,
        "generated_at": generated_at,
        "source": report_source,
        "errors": errors,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, value in (
        ("offers.snapshot.json", canonical),
        ("metadata.snapshot.json", metadata),
        ("manifest.json", manifest),
        ("validation-report.json", report),
    ):
        (output_dir / name).write_text(
            json.dumps(value, indent=2, ensure_ascii=False) + "\n"
        )
    if errors:
        print(
            f"Rejected {len(errors)} of {len(rows)} rows; see validation-report.json",
            file=sys.stderr,
        )
        return 1
    print(f"Built {len(accepted)} offers ({data_version})")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=ROOT / "data/source/offers.csv")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/generated")
    args = parser.parse_args()
    raise SystemExit(build(args.source, args.output_dir))
