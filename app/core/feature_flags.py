from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, model_validator


class FeatureFlagConfigError(ValueError):
    """Raised when feature configuration is missing, malformed, or unsafe."""


class FeatureFlags(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    authEnabled: bool = False
    offerLockingEnabled: bool = False
    allOffers: bool = True
    savedCards: bool = False
    dailyVisitorsEnabled: bool = False
    couponCodeEnabled: bool = False

    @model_validator(mode="after")
    def validate_supported_capabilities(self) -> "FeatureFlags":
        if self.offerLockingEnabled and not self.authEnabled:
            raise ValueError("offerLockingEnabled=true requires authEnabled=true")
        unsupported = {
            "authEnabled": self.authEnabled,
            "offerLockingEnabled": self.offerLockingEnabled,
            "savedCards": self.savedCards,
            "dailyVisitorsEnabled": self.dailyVisitorsEnabled,
        }
        enabled = [name for name, value in unsupported.items() if value]
        if enabled:
            raise ValueError(
                f"unsupported features must remain disabled: {', '.join(enabled)}"
            )
        return self

    def version(self) -> str:
        payload = json.dumps(self.model_dump(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()[:8]


class FeatureFlagsResponse(FeatureFlags):
    config_version: str


def load_feature_flags(path: Path) -> FeatureFlags:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FeatureFlagConfigError(f"feature flag file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise FeatureFlagConfigError(
            f"feature flag file is malformed: {exc.msg}"
        ) from exc
    try:
        return FeatureFlags.model_validate(payload)
    except Exception as exc:
        raise FeatureFlagConfigError(
            f"feature flag configuration is invalid: {exc}"
        ) from exc
