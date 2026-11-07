#!/usr/bin/env python3
"""Add or update a feature flag in one command.

Usage:
    python3 scripts/add_feature_flag.py <flagName> <true|false>

Examples:
    python3 scripts/add_feature_flag.py splashScreenEnabled true
    python3 scripts/add_feature_flag.py myNewFeatureEnabled false

Touch points updated automatically:
    Backend  : app/core/feature_flags.py     (Pydantic model -- source of truth)
    Backend  : data/config/feature_flags.json (runtime overrides, if flag present)
    Backend  : contracts/openapi.json         (regenerated)
    Frontend : contracts/openapi.json         (synced copy)
    Frontend : src/types/generated-api.d.ts   (regenerated)
    Frontend : src/config/featureCapabilities.ts  <- via sync_feature_flags.py
    Frontend : src/data/generated/featureFlags.json <- via sync_feature_flags.py
"""

import json
import re
import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).parent.parent
FRONTEND_ROOT = BACKEND_ROOT.parent / "cardwiseoffer"

FF_PY = BACKEND_ROOT / "app/core/feature_flags.py"
FF_JSON_BE = BACKEND_ROOT / "data/config/feature_flags.json"
OPENAPI_BE = BACKEND_ROOT / "contracts/openapi.json"
OPENAPI_FE = FRONTEND_ROOT / "contracts/openapi.json"


# -- helpers ------------------------------------------------------------------


def py_bool(value: bool) -> str:
    return "True" if value else "False"


def run(cmd: list[str], cwd: Path) -> None:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr.strip() or result.stdout.strip()}")
        sys.exit(1)


# -- 1. Pydantic model (source of truth) --------------------------------------


def update_pydantic_model(flag_name: str, default: bool) -> None:
    src = FF_PY.read_text()
    if flag_name in src:
        src = re.sub(
            rf"(\s+{re.escape(flag_name)}: bool = )(True|False)",
            lambda m: m.group(1) + py_bool(default),
            src,
        )
    else:
        line = f"    {flag_name}: bool = {py_bool(default)}\n"
        src = src.replace("    def version(", line + "\n    def version(")
    FF_PY.write_text(src)
    print(f"  ok feature_flags.py        {flag_name} = {py_bool(default)}")


# -- 2. Backend JSON config (update if already present) -----------------------


def update_json_if_present(flag_name: str, value: bool) -> None:
    data = json.loads(FF_JSON_BE.read_text())
    if flag_name in data:
        data[flag_name] = value
        FF_JSON_BE.write_text(json.dumps(data, indent=2) + "\n")
        print(f"  ok feature_flags.json       {flag_name} = {str(value).lower()} (override updated)")
    else:
        print(f"  -- feature_flags.json       {flag_name} not in overrides (using model default)")


# -- 3. Regenerate derived files via sync_feature_flags.py -------------------


def sync_derived() -> None:
    run(["python3", "scripts/sync_feature_flags.py"], cwd=BACKEND_ROOT)


# -- 4. Regenerate OpenAPI + TS types ----------------------------------------


def regenerate_openapi() -> None:
    run(["python3", "scripts/export_openapi.py"], cwd=BACKEND_ROOT)
    import shutil

    shutil.copy(OPENAPI_BE, OPENAPI_FE)
    print("  ok contracts/openapi.json   regenerated + synced to frontend")


def regenerate_ts_types() -> None:
    run(["npm", "run", "generate:api"], cwd=FRONTEND_ROOT)
    print("  ok generated-api.d.ts       regenerated")


# -- main ---------------------------------------------------------------------


def main() -> None:
    if len(sys.argv) != 3 or sys.argv[2] not in ("true", "false"):
        print(__doc__)
        sys.exit(1)

    flag_name = sys.argv[1]
    value = sys.argv[2] == "true"

    if not re.match(r"^[a-z][a-zA-Z0-9]+$", flag_name):
        print(f"ERROR: flag name must be camelCase, got: {flag_name}")
        sys.exit(1)

    print(f"\nAdding flag: {flag_name} = {str(value).lower()}\n")

    update_pydantic_model(flag_name, value)
    update_json_if_present(flag_name, value)
    sync_derived()
    regenerate_openapi()
    regenerate_ts_types()

    print("\nDone. Run: python3 -m pytest -q   (backend)")
    print("       npm run build              (frontend)")


if __name__ == "__main__":
    main()
