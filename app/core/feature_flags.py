from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict


class FeatureFlagConfigError(ValueError):
    """Raised when feature configuration is missing, malformed, or unsafe."""


class FeatureFlags(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    phase2UserFeaturesEnabled: bool = False
    publicAllOffersEnabled: bool = True
    couponCodeEnabled: bool = False
    flightInternationalEnabled: bool = False
    cookieConsentEnabled: bool = False
    analyticsEnabled: bool = True
    bookingAmountComparisonEnabled: bool = False
    visitorCountEnabled: bool = False
    authEnabled: bool = False
    howItWorksEnabled: bool = True
    aboutEnabled: bool = True
    contactEnabled: bool = True
    privacyPolicyEnabled: bool = True
    termsOfServiceEnabled: bool = True
    splashScreenEnabled: bool = False
    homeEntranceAnimationEnabled: bool = True
    subscriptionsEnabled: bool = False
    userCardsEnabled: bool = False
    notificationsEnabled: bool = False
    tieredDiscountEnabled: bool = True

    def version(self) -> str:
        payload = json.dumps(self.model_dump(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()[:8]


class FeatureFlagsResponse(FeatureFlags):
    config_version: str


def load_feature_flags(path: Path | None = None) -> FeatureFlags:
    """Load feature flags from *path*, falling back to model defaults when absent.

    Pass path=None (or omit) to get pure defaults — useful in tests and scripts
    that don't need environment-specific overrides.
    """
    if path is None or not path.exists():
        return FeatureFlags()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise FeatureFlagConfigError(f"feature flag file is malformed: {exc.msg}") from exc
    try:
        return FeatureFlags.model_validate(payload)
    except Exception as exc:
        raise FeatureFlagConfigError(f"feature flag configuration is invalid: {exc}") from exc
