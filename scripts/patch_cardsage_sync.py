"""
Run immediately after `python3 -m cardsage sync` to fix the three known
issues that cardsage sync leaves in cwo_backend/data/generated/:

  1. manifest.json  — missing rejected_row_count, supported_platforms,
                       dataset_last_updated_at
  2. facets.snapshot.json — platforms/banks are lists; missing active_on
  3. offers.snapshot.json — NO_CARD offers that specify bank_id should be CREDIT

Usage:
    python3 scripts/patch_cardsage_sync.py
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT    = Path(__file__).parent.parent
GEN     = ROOT / "data" / "generated"
TODAY   = date.today()


def patch_manifest(snap: list[dict]) -> None:
    path = GEN / "manifest.json"
    m    = json.loads(path.read_text())

    platforms = sorted({o["platform_id"] for o in snap if o.get("platform_id")})
    rejected  = m.get("source_row_count", 0) - m.get("accepted_row_count", 0)

    m.setdefault("rejected_row_count", rejected)
    m.setdefault("supported_platforms", platforms)
    m.setdefault("dataset_last_updated_at", str(TODAY))

    # Overwrite regardless — cardsage may have left stale values
    m["rejected_row_count"]     = rejected
    m["supported_platforms"]    = platforms
    m["dataset_last_updated_at"] = str(TODAY)

    path.write_text(json.dumps(m, indent=2, ensure_ascii=False))
    print(f"  manifest  — rejected={rejected}, platforms={platforms}")


def patch_facets(snap: list[dict], data_version: str) -> None:
    path = GEN / "facets.snapshot.json"

    platform_counts: dict[str, int] = defaultdict(int)
    bank_counts:     dict[str, int] = defaultdict(int)
    for o in snap:
        if o.get("platform_id"):
            platform_counts[o["platform_id"]] += 1
        if o.get("bank_id"):
            bank_counts[o["bank_id"]] += 1

    facets = {
        "data_version": data_version,
        "active_on":    str(TODAY),
        "platforms":    {k: {"count": v} for k, v in sorted(platform_counts.items())},
        "banks":        {k: {"count": v} for k, v in sorted(bank_counts.items(), key=lambda x: -x[1])},
    }
    path.write_text(json.dumps(facets, indent=2, ensure_ascii=False))
    print(f"  facets    — {len(facets['platforms'])} platforms, {len(facets['banks'])} banks")


def patch_offers(snap: list[dict]) -> int:
    path  = GEN / "offers.snapshot.json"
    fixed = 0
    for o in snap:
        if o.get("payment_method") == "NO_CARD" and o.get("bank_id"):
            o["payment_method"] = "CREDIT"
            fixed += 1
            print(f"  offer fix — {o['offer_id']}  NO_CARD→CREDIT")
    if fixed:
        path.write_text(json.dumps(snap, indent=2, ensure_ascii=False))
    return fixed


def main() -> None:
    snap_path = GEN / "offers.snapshot.json"
    snap      = json.loads(snap_path.read_text())

    manifest  = json.loads((GEN / "manifest.json").read_text())
    dv        = manifest.get("data_version", "unknown")

    print(f"Patching cardsage sync output  (data_version={dv}, offers={len(snap)})")

    patch_manifest(snap)

    fixed = patch_offers(snap)
    if not fixed:
        print("  offers    — no NO_CARD+bank_id fixes needed")

    # Re-read snap in case patch_offers rewrote it
    snap = json.loads(snap_path.read_text())
    patch_facets(snap, dv)

    print("Done.")


if __name__ == "__main__":
    main()
