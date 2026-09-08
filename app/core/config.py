import os
from pathlib import Path
from typing import Literal, cast

from pydantic import BaseModel, Field, model_validator

ROOT = Path(__file__).resolve().parents[2]


class RuntimeSettings(BaseModel):
    app_env: Literal["dev", "test", "production"] = "dev"
    allowed_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:8080",
            "http://localhost:5173",
            "http://127.0.0.1:8080",
            "http://127.0.0.1:5173",
        ]
    )
    offers_snapshot_path: Path = ROOT / "data/generated/offers.snapshot.json"
    metadata_snapshot_path: Path = ROOT / "data/generated/metadata.snapshot.json"
    facets_snapshot_path: Path = ROOT / "data/generated/facets.snapshot.json"
    manifest_path: Path = ROOT / "data/generated/manifest.json"
    feature_flags_path: Path = ROOT / "data/config/feature_flags.json"
    supported_platforms: tuple[str, ...] = ("MAKEMYTRIP", "CLEARTRIP")
    contract_version: str = "1.1"
    default_page_limit: int = Field(20, ge=1, le=100)
    max_page_limit: int = Field(100, ge=1, le=500)
    meta_cache_ttl: int = Field(86400, ge=0)
    flags_cache_ttl: int = Field(300, ge=0)
    offers_cache_ttl: int = Field(600, ge=0)
    rate_limit_global: int = Field(30, ge=1)
    rate_limit_global_window: int = Field(60, ge=1)
    rate_limit_search: int = Field(5, ge=1)
    rate_limit_search_window: int = Field(10, ge=1)
    trust_proxy_headers: bool = False

    @model_validator(mode="after")
    def production_safety(self) -> "RuntimeSettings":
        if self.max_page_limit < self.default_page_limit:
            raise ValueError("max_page_limit must be >= default_page_limit")
        if not self.contract_version.strip():
            raise ValueError("contract_version cannot be blank")
        if self.app_env == "production":
            if not self.allowed_origins or any(
                origin == "*" or "localhost" in origin or "127.0.0.1" in origin
                for origin in self.allowed_origins
            ):
                raise ValueError(
                    "production ALLOWED_ORIGINS must be an explicit non-local allowlist"
                )
        return self


def _csv(name: str, default: str) -> list[str]:
    return [
        value.strip() for value in os.getenv(name, default).split(",") if value.strip()
    ]


def load_runtime_settings() -> RuntimeSettings:
    app_env = cast(Literal["dev", "test", "production"], os.getenv("APP_ENV", "dev"))
    origin_default = (
        ""
        if app_env == "production"
        else "http://localhost:8080,http://localhost:5173,http://127.0.0.1:8080,http://127.0.0.1:5173"
    )
    return RuntimeSettings(
        app_env=app_env,
        allowed_origins=_csv("ALLOWED_ORIGINS", origin_default),
        offers_snapshot_path=Path(
            os.getenv(
                "OFFERS_SNAPSHOT_PATH", ROOT / "data/generated/offers.snapshot.json"
            )
        ),
        metadata_snapshot_path=Path(
            os.getenv(
                "METADATA_SNAPSHOT_PATH", ROOT / "data/generated/metadata.snapshot.json"
            )
        ),
        facets_snapshot_path=Path(
            os.getenv(
                "FACETS_SNAPSHOT_PATH", ROOT / "data/generated/facets.snapshot.json"
            )
        ),
        manifest_path=Path(
            os.getenv("MANIFEST_PATH", ROOT / "data/generated/manifest.json")
        ),
        feature_flags_path=Path(
            os.getenv("FEATURE_FLAGS_PATH", ROOT / "data/config/feature_flags.json")
        ),
        supported_platforms=tuple(_csv("SUPPORTED_PLATFORMS", "MAKEMYTRIP,CLEARTRIP")),
        contract_version=os.getenv("CONTRACT_VERSION", "1.1"),
        default_page_limit=int(os.getenv("DEFAULT_PAGE_LIMIT", "20")),
        max_page_limit=int(os.getenv("MAX_PAGE_LIMIT", "100")),
        meta_cache_ttl=int(os.getenv("META_CACHE_TTL", "86400")),
        flags_cache_ttl=int(os.getenv("FLAGS_CACHE_TTL", "300")),
        offers_cache_ttl=int(os.getenv("OFFERS_CACHE_TTL", "600")),
        rate_limit_global=int(os.getenv("RATE_LIMIT_GLOBAL", "30")),
        rate_limit_global_window=int(os.getenv("RATE_LIMIT_GLOBAL_WINDOW", "60")),
        rate_limit_search=int(os.getenv("RATE_LIMIT_SEARCH", "5")),
        rate_limit_search_window=int(os.getenv("RATE_LIMIT_SEARCH_WINDOW", "10")),
        trust_proxy_headers=os.getenv("TRUST_PROXY_HEADERS", "false").lower() == "true",
    )


SETTINGS = load_runtime_settings()
APP_ENV = SETTINGS.app_env
API_PREFIX = "/api/v1"
CORS_ORIGINS = SETTINGS.allowed_origins
OFFERS_SNAPSHOT_PATH = str(SETTINGS.offers_snapshot_path)
METADATA_SNAPSHOT_PATH = str(SETTINGS.metadata_snapshot_path)
FACETS_SNAPSHOT_PATH = str(SETTINGS.facets_snapshot_path)
MANIFEST_PATH = str(SETTINGS.manifest_path)
FEATURE_FLAGS_PATH = str(SETTINGS.feature_flags_path)
SUPPORTED_PLATFORMS = SETTINGS.supported_platforms
CONTRACT_VERSION = SETTINGS.contract_version


class RateLimitConfig:
    GLOBAL_LIMIT = SETTINGS.rate_limit_global
    GLOBAL_WINDOW_SEC = SETTINGS.rate_limit_global_window
    SEARCH_LIMIT = SETTINGS.rate_limit_search
    SEARCH_WINDOW_SEC = SETTINGS.rate_limit_search_window
