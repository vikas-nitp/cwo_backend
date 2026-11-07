"""
Full offer sync: run cardsage → patch output → (optionally) export frontend bundle.

Usage:
    python3 scripts/sync_offers.py            # sync + patch
    python3 scripts/sync_offers.py --export   # sync + patch + export frontend bundle
    python3 scripts/sync_offers.py --patch-only  # skip cardsage, just re-patch existing files

This wraps the two manual steps that must always run together:
  1. python3 -m cardsage sync
  2. python3 scripts/patch_cardsage_sync.py
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def run(cmd: list[str], label: str) -> None:
    print(f"\n── {label} ──")
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        print(f"\n✗ {label} failed (exit {result.returncode})", file=sys.stderr)
        sys.exit(result.returncode)
    print(f"✓ {label} done")


def main() -> None:
    parser = argparse.ArgumentParser(description="Full offer sync pipeline")
    parser.add_argument("--patch-only", action="store_true", help="Skip cardsage, re-patch existing files")
    parser.add_argument("--export", action="store_true", help="Also export frontend bundle after patching")
    args = parser.parse_args()

    python = sys.executable

    if not args.patch_only:
        run([python, "-m", "cardsage", "sync"], "cardsage sync")

    run([python, "scripts/patch_cardsage_sync.py"], "patch cardsage output")

    if args.export:
        run([python, "scripts/export_frontend_bundle.py"], "export frontend bundle")

    print("\n✓ Sync complete.")


if __name__ == "__main__":
    main()
