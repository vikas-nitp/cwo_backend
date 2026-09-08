# Feature flags

**Date:** 2026-07-12

## Purpose and previous behavior

Replace a hardcoded endpoint and unused JSON file with one validated startup configuration.

## Architecture and files changed

`app/core/feature_flags.py` strictly validates `data/config/feature_flags.json`, rejects unknown fields/types and unsupported enabled capabilities, computes a stable hash, and stores the model on `app.state`. The catalogue route enforces `allOffers`; readiness includes the configuration version.

## Configuration

Set `FEATURE_FLAGS_PATH`. Authentication, locking, saved cards, and visitor analytics must remain false. Locking also requires authentication.

## Test procedure and deployment

Feature tests cover missing/malformed files, invalid types/dependencies, hash stability, endpoint/ETag, catalogue toggle, and readiness. Configuration changes take effect only after restart.

## Known limitations and future migration

Only `allOffers` has implemented behavior. Add real dependency-backed services before permitting any other flag to become true.
