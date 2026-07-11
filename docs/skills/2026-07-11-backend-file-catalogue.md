# Backend file catalogue

**Date:** 2026-07-11
**Purpose:** Record the incremental migration from Excel and synthetic pricing to immutable validated snapshots.

## Previous behavior

`data_service.py` attempted to load Excel into a mutable global cache. `offer_engine.py` generated fares, platform variations, final prices, savings, and authentication locks.

## New architecture

`data/source/offers.csv` is validated by `scripts/build_offer_snapshot.py`. Generated JSON is loaded once by `FileOfferRepository`; services own catalog/search use cases and domain modules own calculations and ranking.

## Files changed

Added `app/api`, `app/domain`, `app/repositories`, canonical `app/schemas`, focused services, source/generated data, scripts, contracts, tests, Docker/CI configuration, and dated docs. `app/main.py` and `app/core/config.py` now use the snapshot runtime. Legacy modules remain for history but are not registered or imported by production routes.

## Configuration

Snapshot paths, booking window, supported platforms, CORS, environment, and rate limits are environment-controlled.

## Test procedure

Run the builder, OpenAPI exporter, `python -m pytest`, lint/type checks, and Docker build.

## Deployment notes

Snapshots are build artifacts committed into the image. Runtime filesystem access is read-only.

## Known limitations

The seed catalogue contains six records, not the eventual 50–100 production records. Offer facts require editorial verification.

## Future migration path

Implement `PostgresOfferRepository` behind the same protocol only when a database is required; API and domain services should remain unchanged.
