import json

import pytest

from app.core.feature_flags import (
    FeatureFlagConfigError,
    FeatureFlags,
    load_feature_flags,
)


def write(path, payload):
    path.write_text(json.dumps(payload))


def valid(**changes):
    payload = {
        "authEnabled": False,
        "offerLockingEnabled": False,
        "allOffers": True,
        "savedCards": False,
        "dailyVisitorsEnabled": False,
        "couponCodeEnabled": False,
    }
    payload.update(changes)
    return payload


def test_valid_loading_and_stable_version(tmp_path):
    path = tmp_path / "flags.json"
    write(path, valid())
    first = load_feature_flags(path)
    second = load_feature_flags(path)
    assert first.allOffers is True
    assert first.couponCodeEnabled is False
    assert first.version() == second.version()
    assert len(first.version()) == 8


def test_missing_malformed_unknown_and_invalid_type(tmp_path):
    with pytest.raises(FeatureFlagConfigError, match="not found"):
        load_feature_flags(tmp_path / "missing.json")
    malformed = tmp_path / "malformed.json"
    malformed.write_text("{")
    with pytest.raises(FeatureFlagConfigError, match="malformed"):
        load_feature_flags(malformed)
    for payload in (valid(unknown=True), valid(allOffers="true")):
        path = tmp_path / "invalid.json"
        write(path, payload)
        with pytest.raises(FeatureFlagConfigError, match="invalid"):
            load_feature_flags(path)


def test_unsupported_and_dependent_features_are_rejected(tmp_path):
    path = tmp_path / "flags.json"
    write(path, valid(savedCards=True))
    with pytest.raises(FeatureFlagConfigError, match="unsupported"):
        load_feature_flags(path)
    write(path, valid(offerLockingEnabled=True))
    with pytest.raises(FeatureFlagConfigError, match="requires authEnabled"):
        load_feature_flags(path)
    for name in ("authEnabled", "dailyVisitorsEnabled"):
        write(path, valid(**{name: True}))
        with pytest.raises(FeatureFlagConfigError, match="unsupported"):
            load_feature_flags(path)


def test_supported_flags_accept_true_and_false_states():
    assert FeatureFlags(allOffers=False, couponCodeEnabled=False).allOffers is False
    enabled = FeatureFlags(allOffers=True, couponCodeEnabled=True)
    assert enabled.allOffers is True
    assert enabled.couponCodeEnabled is True


def test_all_offers_toggle_and_readiness(client):
    original = client.app.state.feature_flags
    try:
        client.app.state.feature_flags = FeatureFlags(allOffers=False)
        disabled = client.get("/api/v1/offers")
        assert disabled.status_code == 403
        assert disabled.json()["error"]["code"] == "FEATURE_DISABLED"
        assert (
            client.post(
                "/api/v1/search",
                json={
                    "from": "DEL",
                    "to": "BLR",
                    "date": __import__("datetime").date.today().isoformat(),
                },
            ).status_code
            == 200
        )
        client.app.state.feature_flags = None
        ready = client.get("/health/ready")
        assert ready.status_code == 503
        assert ready.json()["error"] == "FEATURE_CONFIG_INVALID"
    finally:
        client.app.state.feature_flags = original


def test_feature_endpoint_version_and_conditional_get(client):
    response = client.get("/api/v1/feature-flags")
    assert response.status_code == 200
    assert response.json()["config_version"]
    assert response.headers["x-contract-version"] == "1.1"
    cached = client.get(
        "/api/v1/feature-flags", headers={"If-None-Match": response.headers["etag"]}
    )
    assert cached.status_code == 304
