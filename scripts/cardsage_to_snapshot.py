#!/usr/bin/env python3
"""
Convert cardsage combined output into the backend CSV snapshot format.

Usage (from WORKSPACE root):
    python3 cwo_backend/scripts/cardsage_to_snapshot.py

Input:  cardsage/output/combined/YYYY-MM-DD/all_valid_offers.json
        (latest date directory is selected automatically)
        Override: CARDSAGE_COMBINED_DIR=cardsage/output/combined/2026-09-21

Output: cwo_backend/data/source/offers.csv  (full rewrite)

The combined file already contains only VALID + WARNING offers (NEEDS_REVIEW
and INVALID are excluded by the orchestrator), so evidence_status derivation
maps straightforwardly and publish_status relies on confidence_score.

evidence_status derivation:
    VALID        → VERIFIED
    WARNING      → PARTIAL
    NEEDS_REVIEW → PARTIAL   (kept for safety; excluded upstream in practice)
    INVALID      → UNVERIFIED
    (missing)    → PARTIAL

publish_status derivation:
    evidence_status != UNVERIFIED AND confidence_score >= 0.55 → READY
    (PARTIAL evidence is accepted at launch — the offer was found but not fully verified)
    evidence_status == UNVERIFIED OR confidence_score < 0.55  → DRAFT
"""

from __future__ import annotations

import csv
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

# ── Paths ─────────────────────────────────────────────────────────────────────

# Script lives at cwo_backend/scripts/; WORKSPACE root is two levels up.
WORKSPACE = Path(__file__).resolve().parents[2]

_COMBINED_ROOT = WORKSPACE / "cardsage" / "output" / "combined"
OFFERS_CSV = WORKSPACE / "cwo_backend" / "data" / "source" / "offers.csv"


def _resolve_combined_dir() -> Path:
    """
    Return the path to all_valid_offers.json's parent directory.

    Priority:
      1. CARDSAGE_COMBINED_DIR env var — an explicit date directory, e.g.
         cardsage/output/combined/2026-09-21
      2. Latest YYYY-MM-DD subdirectory under cardsage/output/combined/
    """
    env_override = os.environ.get("CARDSAGE_COMBINED_DIR", "").strip()
    if env_override:
        return Path(env_override)

    if not _COMBINED_ROOT.exists():
        return _COMBINED_ROOT  # will produce a clear error in main()

    date_dirs = sorted(
        (d for d in _COMBINED_ROOT.iterdir() if d.is_dir()),
        key=lambda d: d.name,
        reverse=True,
    )
    if not date_dirs:
        return _COMBINED_ROOT  # will produce a clear error in main()

    return date_dirs[0]


# ── Output CSV columns (must match cwo_backend/data/source/offers.csv schema) ─
# build_offer_snapshot.py accepts these aliases:
#   channels  → booking_channel
#   expiry_date / valid_to / valid_till → expiry_date
CSV_COLUMNS = [
    "offer_id",
    "platform_id",
    "platform_name",
    "offer_title",
    "bank_id",
    "bank_name",
    "card_name",
    "payment_method",
    "category",
    "channels",  # alias: booking_channel
    "discount_type",
    "discount_value",
    "max_discount",
    "min_transaction",
    "coupon_code",
    "valid_from",
    "expiry_date",  # alias: valid_to
    "usage_limit",
    "new_user_only",
    "login_required",
    "eligibility_notes",
    "terms_url",
    "source_url",
    "booking_url",
    "source_type",
    "evidence_status",
    "last_verified_at",
    "priority_score",
    "is_active",
    "publish_status",
]


# ── Helpers ───────────────────────────────────────────────────────────────────


def _evidence_status(validation_status: str | None) -> str:
    """Derive evidence_status from cardsage validation_status."""
    mapping = {
        "VALID": "VERIFIED",
        "WARNING": "PARTIAL",
        "NEEDS_REVIEW": "PARTIAL",
        "INVALID": "UNVERIFIED",
    }
    return mapping.get((validation_status or "").upper(), "PARTIAL")


def _publish_status(evidence_status: str, confidence: float) -> str:
    """Derive publish_status from evidence_status and confidence score.

    PARTIAL evidence is acceptable for launch — it means the offer was found
    but not all fields could be fully verified.  UNVERIFIED (scraper could not
    confirm the offer exists at all) always stays DRAFT regardless of confidence.
    """
    if evidence_status == "UNVERIFIED":
        return "DRAFT"
    if confidence >= 0.55:
        return "READY"
    return "DRAFT"


def _fmt_num(value: Any) -> str:
    """Format a numeric field; empty string when absent."""
    if value is None or value == "":
        return ""
    try:
        f = float(value)
        return str(int(f)) if f == int(f) else str(f)
    except (TypeError, ValueError):
        return str(value)


def _fmt_booking_limit(raw: str) -> str:
    """
    Convert cardsage booking_limit slug to a human-readable usage limit string.
    e.g. "1_per_card_per_category_per_month" → "1 per card per month"
         "2_per_card_per_week"               → "2 per card per week"
    """
    if not raw:
        return ""
    s = raw.replace("_", " ").strip()
    s = re.sub(r"\bper category\b\s*", "", s, flags=re.IGNORECASE).strip()
    s = re.sub(r"\s+", " ", s).strip()
    return s


# Patterns for post-processing combined JSON offers that were normalized before
# the booking-limit and eligibility-dedup fixes landed.

# "once per card, per product per month" / "1 per card per category per month"
_ONCE_PER_CARD_RE = re.compile(
    r"(?i)(?:once|\d+)\s+per\s+card[,\s]+per\s+(product|category|user|transaction)?[,\s]*per\s+(month|week|day|year)",
)
# "1 booking per card per category" (MMT-style: no frequency word at end)
_BOOKING_PER_CARD_CAT_RE = re.compile(
    r"(?i)(\d+)\s+booking(?:s)?\s+per\s+card\s+per\s+(category|product|user|transaction)",
)
_NOTE_MIN_BOOKING_RE = re.compile(
    r"(?i)min(?:imum)?\.?\s+booking(?:\s+(?:INR|Rs\.?|₹))?\s*[\d,]+",
)
_NOTE_ONCE_PER_CARD_RE = re.compile(
    r"(?i)(?:once|\d+)\s+per\s+card",
)

# Required fields for READY publish_status
_REQUIRED_CARD_FIELDS = ("discount_type", "discount_value", "valid_to")
_REQUIRED_CARD_SOFT = ("bank_id", "coupon_code")  # at least 1 needed for card offers


def _fix_offer(offer: dict[str, Any]) -> dict[str, Any]:
    """
    Post-process a combined-JSON offer to:
      1. Backfill booking_limit from eligibility notes (two regex strategies).
      2. Strip eligibility notes that duplicate structured fields.
      3. Derive effective_pct for FLAT offers with known min_transaction.
      4. Flag offers with too many missing required fields as needs_review.
    Mutates and returns the dict.
    """
    booking_limit = offer.get("booking_limit") or ""
    eligibility = list(offer.get("eligibility_notes") or [])
    min_txn = offer.get("min_transaction")

    # ── 1. Backfill booking_limit from eligibility notes ────────────────────────
    if not booking_limit:
        for note in eligibility:
            # Strategy A: "once per card, per product per month" (EaseMyTrip style)
            m = _ONCE_PER_CARD_RE.search(note)
            if m:
                scope = (m.group(1) or "").lower()
                freq = (m.group(2) or "").lower()
                parts = ["1_per_card"]
                if scope:
                    parts.append(f"per_{scope}")
                if freq:
                    parts.append(f"per_{freq}")
                booking_limit = "_".join(parts)
                offer["booking_limit"] = booking_limit
                break
            # Strategy B: "1 booking per card per category" (MMT T&C blob style)
            m2 = _BOOKING_PER_CARD_CAT_RE.search(note)
            if m2:
                n_times = m2.group(1)
                scope = m2.group(2).lower()
                booking_limit = f"{n_times}_per_card_per_{scope}"
                offer["booking_limit"] = booking_limit
                break

    # ── 2. Remove notes that duplicate structured fields ───────────────────────
    if min_txn or booking_limit:
        eligibility = [
            n
            for n in eligibility
            if not (min_txn and _NOTE_MIN_BOOKING_RE.search(n))
            and not (booking_limit and _NOTE_ONCE_PER_CARD_RE.search(n))
        ]
        offer["eligibility_notes"] = eligibility

    # ── 3. Derive effective_pct for FLAT offers with known min_transaction ─────
    dtype = (offer.get("discount_type") or "").upper()
    dval = float(offer.get("discount_value") or 0)
    min_t = float(offer.get("min_transaction") or 0)
    if dtype == "FLAT" and dval > 0 and min_t > 0:
        pct = round(dval / min_t * 100, 1)
        if 0 < pct <= 100:
            offer.setdefault("extra", {})
            if isinstance(offer.get("extra"), dict):
                offer["extra"]["effective_pct"] = pct

    # ── 4. Required fields check → downgrade confidence if too many missing ────
    # Required for any offer to be READY: discount_type, discount_value, valid_to
    # Soft-required for card offers: bank_id, coupon_code (at least one)
    missing_required = sum(
        1
        for f in _REQUIRED_CARD_FIELDS
        if not offer.get(f) or (f == "discount_value" and float(offer.get(f) or 0) == 0)
    )
    has_bank_or_coupon = bool(offer.get("bank_id")) or bool(offer.get("coupon_code"))
    if missing_required >= 2 or (missing_required >= 1 and not has_bank_or_coupon):
        # Too many required fields absent — cap confidence so publish_status → DRAFT
        offer["confidence"] = min(float(offer.get("confidence") or 0), 0.45)
        if not offer.get("validation_status"):
            offer["validation_status"] = "NEEDS_REVIEW"

    return offer


def _to_row(offer: dict[str, Any]) -> dict[str, str]:
    """Map a single cardsage Offer dict to a CSV row dict."""
    validation_status = offer.get("validation_status") or ""
    confidence = float(offer.get("confidence") or 0.0)

    evidence_st = _evidence_status(validation_status)
    publish_st = _publish_status(evidence_st, confidence)

    eligibility = offer.get("eligibility_notes") or []
    if isinstance(eligibility, list):
        eligibility_str = "; ".join(str(n) for n in eligibility if n)
    else:
        eligibility_str = str(eligibility)

    is_active = "false" if evidence_st == "UNVERIFIED" else "true"

    _lv_raw = offer.get("last_verified_at") or offer.get("scraped_at") or ""
    last_verified = _lv_raw[:10] if _lv_raw else ""

    return {
        "offer_id": offer.get("offer_id") or "",
        "platform_id": offer.get("platform_id") or "",
        "platform_name": offer.get("platform_name") or "",
        "offer_title": offer.get("offer_title") or "",
        "bank_id": offer.get("bank_id") or "",
        "bank_name": offer.get("bank_name") or "",
        "card_name": offer.get("card_name") or "",
        "payment_method": offer.get("payment_method") or "",
        "category": offer.get("category") or "FLIGHT_DOMESTIC",
        "channels": offer.get("booking_channel") or "WEB_AND_APP",
        "discount_type": offer.get("discount_type") or "",
        "discount_value": _fmt_num(offer.get("discount_value")),
        "max_discount": _fmt_num(offer.get("max_discount")),
        "min_transaction": _fmt_num(offer.get("min_transaction")),
        "coupon_code": offer.get("coupon_code") or "",
        "valid_from": (offer.get("valid_from") or "")[:10] or (offer.get("scraped_at") or "")[:10],
        "expiry_date": (offer.get("valid_to") or "")[:10],
        "usage_limit": _fmt_booking_limit(offer.get("booking_limit") or ""),
        "new_user_only": str(offer.get("new_user_only") or False).lower(),
        "login_required": str(bool(offer.get("login_required") or False)).lower(),
        "eligibility_notes": eligibility_str,
        "terms_url": offer.get("terms_url") or "",
        "source_url": offer.get("source_url") or "",
        "booking_url": offer.get("booking_url") or "",
        "source_type": "SCRAPED",
        "evidence_status": evidence_st,
        "last_verified_at": last_verified,
        "priority_score": str(int(confidence * 100)),
        "is_active": is_active,
        "publish_status": publish_st,
    }


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    combined_dir = _resolve_combined_dir()
    json_path = combined_dir / "all_valid_offers.json"

    if not json_path.exists():
        print(
            f"Combined offer file not found: {json_path}\nRun 'python -m cardsage run --source all' first.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Reading from: {json_path}")

    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Failed to read {json_path}: {exc}", file=sys.stderr)
        sys.exit(1)

    # all_valid_offers.json is a JSON array of offer objects.
    if isinstance(payload, list):
        raw_offers = payload
    elif isinstance(payload, dict):
        raw_offers = payload.get("offers") or []
    else:
        print(f"Unexpected JSON format in {json_path}", file=sys.stderr)
        sys.exit(1)

    # De-duplicate on offer_id (last-write wins, though combined should be clean).
    seen: dict[str, dict[str, Any]] = {}
    for offer in raw_offers:
        if not isinstance(offer, dict):
            continue
        offer_id = offer.get("offer_id")
        if not offer_id:
            continue
        seen[offer_id] = offer

    total_read = len(raw_offers)
    rows = [_to_row(_fix_offer(offer)) for offer in seen.values()]

    # Write CSV (full rewrite).
    OFFERS_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OFFERS_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"{total_read} offers read, {len(rows)} offers written")


if __name__ == "__main__":
    main()
