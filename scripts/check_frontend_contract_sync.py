#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT.parent / "cardwiseoffer" / "contracts"


def main() -> int:
    if not FRONTEND.exists():
        print("Frontend contracts not present; cross-repository comparison skipped.")
        return 0
    expected = [
        Path("openapi.json"),
        *[
            Path("examples") / path.name
            for path in (ROOT / "contracts/examples").glob("*.json")
        ],
    ]
    mismatches = [
        str(relative)
        for relative in expected
        if not (FRONTEND / relative).exists()
        or (FRONTEND / relative).read_bytes()
        != (ROOT / "contracts" / relative).read_bytes()
    ]
    if mismatches:
        print("Frontend contract artifacts are stale: " + ", ".join(mismatches))
        return 1
    print("Frontend contract artifacts match backend.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
