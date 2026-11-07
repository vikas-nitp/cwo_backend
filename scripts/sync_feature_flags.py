#!/usr/bin/env python3
"""Sync derived feature-flag files from the Python model (single source of truth).

Generates:
  - cardwiseoffer/src/config/featureCapabilities.ts   (TS capability mapping)
  - cardwiseoffer/src/data/generated/featureFlags.json (runtime values for frontend)

Run after any edit to app/core/feature_flags.py:
    python3 scripts/sync_feature_flags.py

Called automatically by add_feature_flag.py and build_data_bundle.py.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).parent.parent
FRONTEND_ROOT = BACKEND_ROOT.parent / "cardwiseoffer"
FF_JSON_BE = BACKEND_ROOT / "data/config/feature_flags.json"
CAPS_TS = FRONTEND_ROOT / "src/config/featureCapabilities.ts"
FF_JSON_FE = FRONTEND_ROOT / "src/data/generated/featureFlags.json"

sys.path.insert(0, str(BACKEND_ROOT))
from app.core.feature_flags import FeatureFlags, load_feature_flags


def to_capability_key(flag_name: str) -> str:
    """splashScreenEnabled → splashScreen"""
    return flag_name[: -len("Enabled")] if flag_name.endswith("Enabled") else flag_name


def generate_capabilities_ts(flags_model: type[FeatureFlags]) -> str:
    field_names = list(flags_model.model_fields.keys())
    lines = [f"    {to_capability_key(n)}: flags.{n}," for n in field_names]
    return (
        'import type { FeatureFlags } from "@/contexts/FeatureFlagContext";\n\n'
        "export function resolveFeatureCapabilities(flags: FeatureFlags) {\n"
        "  return {\n"
        + "\n".join(lines)
        + "\n  };\n}\n"
    )


def sync(*, verbose: bool = True) -> None:
    runtime_flags = load_feature_flags(FF_JSON_BE)
    runtime_dict = runtime_flags.model_dump()

    new_caps = generate_capabilities_ts(FeatureFlags)
    old_caps = CAPS_TS.read_text() if CAPS_TS.exists() else ""
    if new_caps != old_caps:
        CAPS_TS.write_text(new_caps)
        if verbose:
            print("  ✓ featureCapabilities.ts   regenerated")
    elif verbose:
        print("  · featureCapabilities.ts   unchanged")

    new_fe_json = json.dumps(runtime_dict, indent=2) + "\n"
    old_fe_json = FF_JSON_FE.read_text() if FF_JSON_FE.exists() else ""
    if new_fe_json != old_fe_json:
        FF_JSON_FE.parent.mkdir(parents=True, exist_ok=True)
        FF_JSON_FE.write_text(new_fe_json)
        if verbose:
            print("  ✓ featureFlags.json        regenerated")
    elif verbose:
        print("  · featureFlags.json        unchanged")


if __name__ == "__main__":
    sync()
