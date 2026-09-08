#!/usr/bin/env python3
"""Export validated backend snapshots as the standalone frontend bundle."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "data/generated"
DISTRIBUTION = ROOT / "data/distribution/frontend"

FILES = {
    "offers.snapshot.json": "offers.json",
    "metadata.snapshot.json": "metadata.json",
    "facets.snapshot.json": "facets.json",
    "manifest.json": "manifest.json",
    "validation-report.json": "validation-report.json",
}


def export_bundle() -> None:
    manifest = json.loads((GENERATED / "manifest.json").read_text())
    if manifest.get("contract_version") != "1.1" or not manifest.get("source_hash"):
        raise ValueError(
            "generated manifest is missing contract/source synchronization metadata"
        )
    DISTRIBUTION.mkdir(parents=True, exist_ok=True)
    for source_name, destination_name in FILES.items():
        value = json.loads((GENERATED / source_name).read_text())
        (DISTRIBUTION / destination_name).write_text(
            json.dumps(value, indent=2, ensure_ascii=False) + "\n"
        )
    (DISTRIBUTION / "airports.json").write_text(
        json.dumps(json.loads((ROOT / "data/airports.json").read_text()), indent=2)
        + "\n"
    )
    (DISTRIBUTION / "featureFlags.json").write_text(
        json.dumps(
            json.loads((ROOT / "data/config/feature_flags.json").read_text()), indent=2
        )
        + "\n"
    )
    print(f"Exported frontend bundle to {DISTRIBUTION}")


if __name__ == "__main__":
    export_bundle()
