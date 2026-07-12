import re

import pytest
from pydantic import ValidationError

from app.core.config import RuntimeSettings


def test_production_configuration_rejects_unsafe_origins():
    for origins in ([], ["*"], ["http://localhost:5173"]):
        with pytest.raises(ValidationError):
            RuntimeSettings(app_env="production", allowed_origins=origins)
    settings = RuntimeSettings(
        app_env="production", allowed_origins=["https://cardwiseoffer.com"]
    )
    assert settings.allowed_origins == ["https://cardwiseoffer.com"]


def test_request_id_accepts_safe_value_and_rejects_log_injection(client):
    accepted = client.get("/health/live", headers={"X-Request-ID": "safe.request-123"})
    assert accepted.headers["x-request-id"] == "safe.request-123"
    unsafe = "x" * 100
    rejected = client.get("/health/live", headers={"X-Request-ID": unsafe})
    generated = rejected.headers["x-request-id"]
    assert generated != unsafe
    assert re.fullmatch(r"[0-9a-f-]{36}", generated)


def test_cors_allowlist_and_preflight(client):
    allowed = client.options(
        "/api/v1/offers",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    denied = client.options(
        "/api/v1/offers",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert "access-control-allow-origin" not in denied.headers


def test_gzip_large_response_but_not_small_health(client):
    large = client.get("/api/v1/offers?limit=100", headers={"Accept-Encoding": "gzip"})
    assert large.headers["content-encoding"] == "gzip"
    small = client.get("/health/live", headers={"Accept-Encoding": "gzip"})
    assert "content-encoding" not in small.headers


def test_search_rate_limit_uses_error_contract(client, monkeypatch, valid_search):
    import app.core.middleware as middleware

    monkeypatch.setattr(middleware, "APP_ENV", "production")
    monkeypatch.setattr(middleware.RateLimitConfig, "SEARCH_LIMIT", 1)
    middleware.rate_limiter._search_buckets.clear()
    assert client.post("/api/v1/search", json=valid_search).status_code == 200
    limited = client.post("/api/v1/search", json=valid_search)
    assert limited.status_code == 429
    assert limited.headers["retry-after"]
    assert limited.headers["cache-control"] == "no-store"
    assert limited.json()["error"]["code"] == "RATE_LIMITED"
