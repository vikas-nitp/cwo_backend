#!/usr/bin/env python3
"""Add a feature flag across every touch point in one command.

Usage:
    python3 scripts/add_feature_flag.py <flagName> <true|false>

Examples:
    python3 scripts/add_feature_flag.py splashScreenEnabled true
    python3 scripts/add_feature_flag.py myNewFeatureEnabled false

Touch points updated automatically:
    Backend  : app/core/feature_flags.py  (Pydantic model)
    Backend  : data/config/feature_flags.json
    Backend  : contracts/openapi.json     (regenerated)
    Backend  : tests/test_routes.py       (flag assertion)
    Frontend : contracts/openapi.json     (synced copy)
    Frontend : src/types/generated-api.d.ts  (regenerated)
    Frontend : src/data/generated/featureFlags.json
    Frontend : src/config/featureCapabilities.ts
"""
import json
import re
import subprocess
import sys
from pathlib import Path

BACKEND_ROOT  = Path(__file__).parent.parent
FRONTEND_ROOT = BACKEND_ROOT.parent / "cardwiseoffer"

FF_PY        = BACKEND_ROOT / "app/core/feature_flags.py"
FF_JSON_BE   = BACKEND_ROOT / "data/config/feature_flags.json"
FF_JSON_FE   = FRONTEND_ROOT / "src/data/generated/featureFlags.json"
CAPS_TS      = FRONTEND_ROOT / "src/config/featureCapabilities.ts"
OPENAPI_BE   = BACKEND_ROOT / "contracts/openapi.json"
OPENAPI_FE   = FRONTEND_ROOT / "contracts/openapi.json"
TEST_ROUTES  = BACKEND_ROOT / "tests/test_routes.py"


# ── helpers ──────────────────────────────────────────────────────────

def to_capability_key(flag_name: str) -> str:
    """splashScreenEnabled → splashScreen"""
    if flag_name.endswith("Enabled"):
        return flag_name[: -len("Enabled")]
    return flag_name


def py_bool(value: bool) -> str:
    return "True" if value else "False"


def run(cmd: list[str], cwd: Path) -> None:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr.strip() or result.stdout.strip()}")
        sys.exit(1)


# ── 1. Pydantic model ─────────────────────────────────────────────────

def update_pydantic_model(flag_name: str, default: bool) -> None:
    src = FF_PY.read_text()
    if flag_name in src:
        # update existing default
        src = re.sub(
            rf"(\s+{re.escape(flag_name)}: bool = )(True|False)",
            lambda m: m.group(1) + py_bool(default),
            src,
        )
    else:
        # insert before `def version`
        line = f"    {flag_name}: bool = {py_bool(default)}\n"
        src = src.replace("    def version(", line + "\n    def version(")
    FF_PY.write_text(src)
    print(f"  ✓ feature_flags.py        {flag_name} = {py_bool(default)}")


# ── 2. Backend JSON config ────────────────────────────────────────────

def update_json(path: Path, flag_name: str, value: bool) -> None:
    data = json.loads(path.read_text())
    data[flag_name] = value
    path.write_text(json.dumps(data, indent=2) + "\n")
    print(f"  ✓ {path.name:<35} {flag_name} = {str(value).lower()}")


# ── 3. test_routes.py ─────────────────────────────────────────────────

def update_test(flag_name: str, value: bool) -> None:
    src = TEST_ROUTES.read_text()
    py_val = py_bool(value)
    existing = re.search(rf'"{re.escape(flag_name)}":\s*(True|False)', src)
    if existing:
        src = re.sub(
            rf'("{re.escape(flag_name)}":\s*)(True|False)',
            lambda m: m.group(1) + py_val,
            src,
        )
    else:
        # insert before config_version line
        line = f'        "{flag_name}": {py_val},\n'
        src = src.replace('        "config_version":', line + '        "config_version":')
    TEST_ROUTES.write_text(src)
    print(f"  ✓ test_routes.py           {flag_name} = {py_val}")


# ── 4. featureCapabilities.ts ─────────────────────────────────────────

def update_capabilities(flag_name: str) -> None:
    src = CAPS_TS.read_text()
    cap_key = to_capability_key(flag_name)
    line = f"    {cap_key}: flags.{flag_name},"
    if cap_key in src:
        print(f"  ✓ featureCapabilities.ts   {cap_key} already present")
        return
    # insert before closing brace of the return object
    src = src.replace("\n  };\n}", f"\n{line}\n  }};\n}}")
    CAPS_TS.write_text(src)
    print(f"  ✓ featureCapabilities.ts   {cap_key}: flags.{flag_name}")


# ── 5. Regenerate OpenAPI + TS types ──────────────────────────────────

def regenerate_openapi() -> None:
    run(["python3", "scripts/export_openapi.py"], cwd=BACKEND_ROOT)
    import shutil
    shutil.copy(OPENAPI_BE, OPENAPI_FE)
    print("  ✓ contracts/openapi.json   regenerated + synced to frontend")


def regenerate_ts_types() -> None:
    run(["npm", "run", "generate:api"], cwd=FRONTEND_ROOT)
    print("  ✓ generated-api.d.ts       regenerated")


# ── main ──────────────────────────────────────────────────────────────

def main() -> None:
    if len(sys.argv) != 3 or sys.argv[2] not in ("true", "false"):
        print(__doc__)
        sys.exit(1)

    flag_name = sys.argv[1]
    value     = sys.argv[2] == "true"

    if not re.match(r"^[a-z][a-zA-Z0-9]+$", flag_name):
        print(f"ERROR: flag name must be camelCase, got: {flag_name}")
        sys.exit(1)

    print(f"\nAdding flag: {flag_name} = {str(value).lower()}\n")

    update_pydantic_model(flag_name, value)
    update_json(FF_JSON_BE, flag_name, value)
    update_test(flag_name, value)
    regenerate_openapi()
    regenerate_ts_types()
    update_json(FF_JSON_FE, flag_name, value)
    update_capabilities(flag_name)

    print("\nDone. Run: python3 -m pytest -q   (backend)")
    print(       "       npm run build              (frontend)")


if __name__ == "__main__":
    main()
