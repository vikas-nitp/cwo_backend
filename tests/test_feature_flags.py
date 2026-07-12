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
        "phase2UserFeaturesEnabled": False,
        "publicAllOffersEnabled": True,
        "couponCodeEnabled": False,
        "analyticsEnabled": True,
        "bookingAmountComparisonEnabled": False,
    }
    payload.update(changes)
    return payload


def test_valid_loading_and_stable_version(tmp_path):
    path = tmp_path / "flags.json"
    write(path, valid())
    first = load_feature_flags(path)
    second = load_feature_flags(path)
    assert first.publicAllOffersEnabled is True
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
    for payload in (valid(unknown=True), valid(publicAllOffersEnabled="true")):
        path = tmp_path / "invalid.json"
        write(path, payload)
        with pytest.raises(FeatureFlagConfigError, match="invalid"):
            load_feature_flags(path)


@pytest.mark.parametrize("value", [False, True])
def test_all_flags_accept_true_and_false_states(value):
    flags = FeatureFlags(**{name: value for name in FeatureFlags.model_fields})
    assert all(flag is value for flag in flags.model_dump().values())


def test_all_offers_toggle_and_readiness(client):
    original = client.app.state.feature_flags
    try:
        client.app.state.feature_flags = FeatureFlags(publicAllOffersEnabled=False)
        disabled = client.get("/api/v1/offers")
        assert disabled.status_code == 403
        assert disabled.json()["error"]["code"] == "FEATURE_DISABLED"
        assert (
            client.post(
                "/api/v1/search",
                json={
                    "from": "DEL",
                    "to": "BLR",
                    "date": "2026-07-13",
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
