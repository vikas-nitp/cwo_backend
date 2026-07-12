#!/usr/bin/env python3
"""Build all runtime snapshots and the standalone frontend distribution."""

from build_offer_snapshot import ROOT, build_catalogue
from export_frontend_bundle import export_bundle


if __name__ == "__main__":
    status = build_catalogue(
        ROOT / "data/source/catalogue.yml", ROOT / "data/generated"
    )
    if status:
        raise SystemExit(status)
    export_bundle()
