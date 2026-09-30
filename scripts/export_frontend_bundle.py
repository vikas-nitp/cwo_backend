#!/usr/bin/env python3
"""Export validated backend snapshots as the standalone frontend bundle."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
GENERATED = ROOT / "data/generated"
DISTRIBUTION = ROOT / "data/distribution/frontend"

# Frontend static data directory — kept in sync with the backend distribution.
# The React app reads from this path at build/dev time (no backend API call needed).
FRONTEND_STATIC = WORKSPACE / "cardwiseoffer/src/data/generated"

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
        raise ValueError("generated manifest is missing contract/source synchronization metadata")
    DISTRIBUTION.mkdir(parents=True, exist_ok=True)
    for source_name, destination_name in FILES.items():
        value = json.loads((GENERATED / source_name).read_text())
        (DISTRIBUTION / destination_name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    (DISTRIBUTION / "airports.json").write_text(
        json.dumps(json.loads((ROOT / "data/airports.json").read_text()), indent=2) + "\n"
    )
    (DISTRIBUTION / "featureFlags.json").write_text(
        json.dumps(json.loads((ROOT / "data/config/feature_flags.json").read_text()), indent=2) + "\n"
    )
    print(f"Exported frontend bundle to {DISTRIBUTION}")

    # Auto-sync to the frontend static directory so the React dev server
    # picks up the latest offers without a manual copy step.
    if FRONTEND_STATIC.is_dir():
        _sync_to_frontend()
    else:
        print(f"[warn] frontend static dir not found, skipping auto-sync: {FRONTEND_STATIC}")


def _sync_to_frontend() -> None:
    """Copy distribution files to the React frontend's static data directory."""
    FRONTEND_STATIC.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for fname in DISTRIBUTION.iterdir():
        if fname.suffix in (".json",):
            dest = FRONTEND_STATIC / fname.name
            shutil.copy2(fname, dest)
            copied.append(fname.name)
    if copied:
        print(f"Auto-synced {len(copied)} file(s) to frontend: {', '.join(sorted(copied))}")


if __name__ == "__main__":
    export_bundle()
