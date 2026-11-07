"""
Tests for app/core/config.py — environment variable loading and
production safety validation.
"""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.core.config import RuntimeSettings, load_runtime_settings


# ── RuntimeSettings validation ─────────────────────────────────────────────────

class TestRuntimeSettingsValidation:
    def test_defaults_are_dev_mode(self) -> None:
        s = RuntimeSettings()
        assert s.app_env == "dev"
        assert any("localhost" in o for o in s.allowed_origins)

    def test_production_rejects_localhost_origin(self) -> None:
        with pytest.raises(ValidationError, match="non-local allowlist"):
            RuntimeSettings(
                app_env="production",
                allowed_origins=["http://localhost:8080"],
            )

    def test_production_rejects_wildcard_origin(self) -> None:
        with pytest.raises(ValidationError, match="non-local allowlist"):
            RuntimeSettings(
                app_env="production",
                allowed_origins=["*"],
            )

    def test_production_accepts_real_domain(self) -> None:
        s = RuntimeSettings(
            app_env="production",
            allowed_origins=["https://cardoptimal.in", "https://www.cardoptimal.in"],
        )
        assert s.app_env == "production"
        assert "https://cardoptimal.in" in s.allowed_origins

    def test_production_rejects_empty_origins(self) -> None:
        with pytest.raises(ValidationError, match="non-local allowlist"):
            RuntimeSettings(app_env="production", allowed_origins=[])

    def test_max_page_limit_must_be_gte_default(self) -> None:
        with pytest.raises(ValidationError, match="max_page_limit"):
            RuntimeSettings(default_page_limit=50, max_page_limit=10)

    def test_blank_contract_version_rejected(self) -> None:
        with pytest.raises(ValidationError, match="contract_version"):
            RuntimeSettings(contract_version="   ")

    def test_trust_proxy_default_is_false(self) -> None:
        s = RuntimeSettings()
        assert s.trust_proxy_headers is False


# ── load_runtime_settings env var parsing ──────────────────────────────────────

class TestLoadRuntimeSettings:
    def test_reads_app_env(self) -> None:
        with patch.dict(os.environ, {"APP_ENV": "test"}, clear=False):
            s = load_runtime_settings()
        assert s.app_env == "test"

    def test_production_requires_allowed_origins_env_var(self) -> None:
        env = {"APP_ENV": "production", "ALLOWED_ORIGINS": "https://cardoptimal.in"}
        with patch.dict(os.environ, env, clear=False):
            s = load_runtime_settings()
        assert s.app_env == "production"
        assert "https://cardoptimal.in" in s.allowed_origins

    def test_production_without_allowed_origins_raises(self) -> None:
        env = {"APP_ENV": "production"}
        # Remove ALLOWED_ORIGINS if set
        clean_env = {k: v for k, v in os.environ.items() if k != "ALLOWED_ORIGINS"}
        clean_env.update(env)
        with patch.dict(os.environ, clean_env, clear=True):
            with pytest.raises(ValidationError, match="non-local allowlist"):
                load_runtime_settings()

    def test_reads_pagination_limits(self) -> None:
        env = {"DEFAULT_PAGE_LIMIT": "15", "MAX_PAGE_LIMIT": "200"}
        with patch.dict(os.environ, env, clear=False):
            s = load_runtime_settings()
        assert s.default_page_limit == 15
        assert s.max_page_limit == 200

    def test_reads_rate_limits(self) -> None:
        env = {"RATE_LIMIT_SEARCH": "10", "RATE_LIMIT_SEARCH_WINDOW": "30"}
        with patch.dict(os.environ, env, clear=False):
            s = load_runtime_settings()
        assert s.rate_limit_search == 10
        assert s.rate_limit_search_window == 30

    def test_trust_proxy_headers_true(self) -> None:
        with patch.dict(os.environ, {"TRUST_PROXY_HEADERS": "true"}, clear=False):
            s = load_runtime_settings()
        assert s.trust_proxy_headers is True

    def test_trust_proxy_headers_false(self) -> None:
        with patch.dict(os.environ, {"TRUST_PROXY_HEADERS": "false"}, clear=False):
            s = load_runtime_settings()
        assert s.trust_proxy_headers is False

    def test_csv_origins_parsed_correctly(self) -> None:
        origins = "https://a.example.com, https://b.example.com"
        with patch.dict(os.environ, {"APP_ENV": "production", "ALLOWED_ORIGINS": origins}, clear=False):
            s = load_runtime_settings()
        assert "https://a.example.com" in s.allowed_origins
        assert "https://b.example.com" in s.allowed_origins
        assert len(s.allowed_origins) == 2


# ── Railway-specific: production env checklist ────────────────────────────────

class TestRailwayProductionChecklist:
    """Simulate the exact env vars set on Railway and verify the app accepts them."""

    RAILWAY_ENV = {
        "APP_ENV": "production",
        "ALLOWED_ORIGINS": "https://cardoptimal.in,https://www.cardoptimal.in",
        "TRUST_PROXY_HEADERS": "true",
        "CONTRACT_VERSION": "1.1",
        "DEFAULT_PAGE_LIMIT": "20",
        "MAX_PAGE_LIMIT": "100",
    }

    def test_railway_env_loads_without_error(self) -> None:
        with patch.dict(os.environ, self.RAILWAY_ENV, clear=False):
            s = load_runtime_settings()
        assert s.app_env == "production"
        assert s.trust_proxy_headers is True
        assert "https://cardoptimal.in" in s.allowed_origins

    def test_missing_allowed_origins_fails_fast(self) -> None:
        env = {k: v for k, v in self.RAILWAY_ENV.items() if k != "ALLOWED_ORIGINS"}
        clean = {k: v for k, v in os.environ.items() if k != "ALLOWED_ORIGINS"}
        clean.update(env)
        with patch.dict(os.environ, clean, clear=True):
            with pytest.raises(ValidationError):
                load_runtime_settings()
