from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_legacy_synthetic_and_fake_auth_are_not_in_active_packages():
    removed = [
        "app/services/offer_engine.py",
        "app/services/data_service.py",
        "app/routes/auth.py",
        "app/routes/stats.py",
        "app/models/schemas.py",
    ]
    assert all(not (ROOT / path).exists() for path in removed)
    active = "\n".join(path.read_text() for path in (ROOT / "app").rglob("*.py"))
    for forbidden in (
        "x-user-auth",
        "BaseFareGenerator",
        "PriceStripGenerator",
        "AuthGatekeeper",
    ):
        assert forbidden not in active
