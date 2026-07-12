#!/usr/bin/env python3
from __future__ import annotations

import argparse
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
from app.ingestion.sources import (  # noqa: E402
    SourceRecord,
    SourceSpec,
    load_catalogue,
    read_source,
)

ALIASES = {
    "bank": "bank_id",
    "platform": "platform_id",
    "min_txn": "min_transaction",
    "valid_till": "valid_to",
    "coupon": "coupon_code",
    "active": "is_active",
    "channels": "booking_channel",
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


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "y"}:
        return True
    if normalized in {"0", "false", "no", "n"}:
        return False
    raise ValueError(f"invalid boolean: {value}")


def normalize_row(
    row: dict[str, Any], spec: SourceSpec | None = None
) -> dict[str, Any]:
    aliased: dict[str, Any] = {}
    for raw_key, raw_value in row.items():
        key = str(raw_key).strip()
        target = ALIASES.get(key, key)
        value = raw_value.strip() if isinstance(raw_value, str) else raw_value
        if target not in aliased or aliased[target] in (None, ""):
            aliased[target] = value

    if spec:
        for field, default in (
            ("platform_id", spec.platform_id),
            ("platform_name", spec.platform_name),
        ):
            explicit = aliased.get(field)
            if explicit not in (None, "") and str(explicit).upper().replace(
                " ", ""
            ) != default.upper().replace(" ", ""):
                raise ValueError(f"{field} conflicts with catalogue default {default}")
            aliased[field] = default

    missing = sorted(name for name in REQUIRED if aliased.get(name) in (None, ""))
    if missing:
        raise ValueError(f"missing required field(s): {', '.join(missing)}")

    output: dict[str, Any] = {}
    extra: dict[str, Any] = {}
    for key, value in aliased.items():
        if key not in CANONICAL_FIELDS:
            if value not in (None, ""):
                extra[key] = value
            continue
        if value in (None, "") and key in NULLABLE:
            output[key] = None
        elif key in BOOL_FIELDS:
            output[key] = parse_bool(value)
        elif key == "eligibility_notes":
            output[key] = (
                value
                if isinstance(value, list)
                else [item.strip() for item in str(value).split("|") if item.strip()]
            )
        else:
            output[key] = value
    for field in (
        "platform_id",
        "bank_id",
        "payment_method",
        "category",
        "booking_channel",
        "discount_type",
        "evidence_status",
        "publish_status",
    ):
        if output.get(field):
            output[field] = str(output[field]).upper().replace(" ", "")
    if output.get("booking_channel"):
        output["booking_channel"] = output["booking_channel"].replace("+", "_AND_")
    output["extra"] = extra
    return output


def _facets(offers: list[Offer], active_on, data_version: str) -> dict[str, Any]:
    active = [
        o
        for o in offers
        if o.is_active
        and o.publish_status == "READY"
        and o.evidence_status == "VERIFIED"
        and o.valid_from <= active_on <= o.valid_to
    ]
    platforms: dict[str, dict[str, Any]] = {}
    banks: dict[str, dict[str, Any]] = {}
    for offer in active:
        platform = platforms.setdefault(
            offer.platform_id,
            {
                "offer_count": 0,
                "banks": set(),
                "payment_methods": set(),
                "booking_channels": set(),
            },
        )
        platform["offer_count"] += 1
        if offer.bank_id:
            platform["banks"].add(offer.bank_id)
        platform["payment_methods"].add(offer.payment_method)
        platform["booking_channels"].add(offer.booking_channel)
        if offer.bank_id:
            bank = banks.setdefault(
                offer.bank_id,
                {
                    "offer_count": 0,
                    "platforms": set(),
                    "payment_methods": set(),
                    "booking_channels": set(),
                },
            )
            bank["offer_count"] += 1
            bank["platforms"].add(offer.platform_id)
            bank["payment_methods"].add(offer.payment_method)
            bank["booking_channels"].add(offer.booking_channel)

    def serializable(mapping):
        return {
            key: {
                field: sorted(value) if isinstance(value, set) else value
                for field, value in item.items()
            }
            for key, item in sorted(mapping.items())
        }

    return {
        "data_version": data_version,
        "active_on": active_on.isoformat(),
        "platforms": serializable(platforms),
        "banks": serializable(banks),
    }


def build_records(
    records: list[tuple[SourceRecord, SourceSpec]], output_dir: Path, source_count: int
) -> int:
    accepted: list[Offer] = []
    errors: list[dict[str, Any]] = []
    seen: dict[str, str] = {}
    source_summaries: dict[str, dict[str, Any]] = {}
    if not records:
        errors.append(
            {
                "source": None,
                "sheet": None,
                "location": None,
                "offer_id": None,
                "code": "SOURCE_VALIDATION_FAILED",
                "message": "no offer rows were found in configured sources",
            }
        )
    for record, spec in records:
        summary = source_summaries.setdefault(
            record.source,
            {
                "path": record.source,
                "format": spec.format,
                "row_count": 0,
                "accepted_count": 0,
                "rejected_count": 0,
            },
        )
        summary["row_count"] += 1
        try:
            data = normalize_row(record.data, spec)
            offer_id = str(data["offer_id"])
            if offer_id in seen:
                raise ValueError(
                    f"duplicate offer_id {offer_id}; first seen in {seen[offer_id]}"
                )
            offer = Offer.model_validate(data)
            seen[offer.offer_id] = record.source
            accepted.append(offer)
            summary["accepted_count"] += 1
        except (ValueError, ValidationError) as exc:
            summary["rejected_count"] += 1
            message = str(exc)
            errors.append(
                {
                    "source": record.source,
                    "sheet": record.sheet,
                    "location": record.location,
                    "offer_id": record.data.get("offer_id"),
                    "code": "DUPLICATE_OFFER_ID"
                    if "duplicate offer_id" in message
                    else "SOURCE_VALIDATION_FAILED",
                    "message": message,
                }
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
        "schema_version": "1.1",
        "data_version": data_version,
        "generated_at": generated_at,
        "source_count": source_count,
        "source_row_count": len(records),
        "accepted_row_count": len(accepted),
        "rejected_row_count": len(errors),
        "supported_platforms": ["MAKEMYTRIP", "CLEARTRIP"],
    }
    report = {
        "valid": not errors,
        "source_count": source_count,
        "source_row_count": len(records),
        "accepted_row_count": len(accepted),
        "rejected_row_count": len(errors),
        "warning_count": 0,
        "generated_at": generated_at,
        "sources": list(source_summaries.values()),
        "errors": errors,
        "warnings": [],
    }
    outputs = {
        "offers.snapshot.json": canonical,
        "metadata.snapshot.json": metadata,
        "facets.snapshot.json": _facets(accepted, version_date, data_version),
        "manifest.json": manifest,
        "validation-report.json": report,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, value in outputs.items():
        (output_dir / name).write_text(
            json.dumps(value, indent=2, ensure_ascii=False) + "\n"
        )
    if errors:
        print(
            f"Rejected {len(errors)} of {len(records)} rows; see validation-report.json",
            file=sys.stderr,
        )
        return 1
    print(f"Built {len(accepted)} offers from {source_count} sources ({data_version})")
    return 0


def build_catalogue(catalogue: Path, output_dir: Path) -> int:
    specs = load_catalogue(catalogue)
    records: list[tuple[SourceRecord, SourceSpec]] = []
    adapter_errors: list[str] = []
    for spec in specs:
        try:
            records.extend(
                (record, spec) for record in read_source(spec, catalogue.parent)
            )
        except Exception as exc:
            adapter_errors.append(f"{spec.path.name}: {exc}")
    if adapter_errors:
        output_dir.mkdir(parents=True, exist_ok=True)
        report = {
            "valid": False,
            "source_count": len(specs),
            "source_row_count": len(records),
            "accepted_row_count": 0,
            "rejected_row_count": len(adapter_errors),
            "warning_count": 0,
            "sources": [],
            "errors": [
                {"code": "SOURCE_VALIDATION_FAILED", "message": message}
                for message in adapter_errors
            ],
            "warnings": [],
        }
        (output_dir / "validation-report.json").write_text(
            json.dumps(report, indent=2) + "\n"
        )
        return 1
    return build_records(records, output_dir, len(specs))


def build(source: Path, output_dir: Path) -> int:
    spec = SourceSpec(source.resolve(), "csv", "", "")
    records = [
        (
            record,
            SourceSpec(
                spec.path,
                "csv",
                str(record.data.get("platform_id", "")),
                str(record.data.get("platform_name", "")),
            ),
        )
        for record in read_source(spec, source.parent)
    ]
    return build_records(records, output_dir, 1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--catalogue", type=Path, default=ROOT / "data/source/catalogue.yml"
    )
    parser.add_argument("--source", type=Path)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/generated")
    args = parser.parse_args()
    raise SystemExit(
        build(args.source, args.output_dir)
        if args.source
        else build_catalogue(args.catalogue, args.output_dir)
    )
