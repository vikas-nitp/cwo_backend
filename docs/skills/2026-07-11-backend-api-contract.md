# Backend API contract skill

**Date:** 2026-07-11
**Purpose:** Define stable frontend-facing schemas and validation ownership.

## Previous behavior

Responses exposed legacy names, synthetic `strip7days`, fabricated final prices, locking flags, and unstructured FastAPI errors.

## New architecture

Versioned routes return canonical offers, metadata derived from publishable snapshots, optional estimates based only on a supplied booking amount, deterministic ranking fields, and request-ID error envelopes.

## Files changed

See `app/api`, `app/schemas`, `app/domain`, `contracts/openapi.json`, `contracts/examples`, and `docs/contracts/cardwiseoffer-api-v1.md`.

## Configuration

`BOOKING_WINDOW_DAYS=10`; supported platform and category values are typed in the schema.

## Test procedure

Contract fixtures are parsed by the actual Pydantic response schemas and committed OpenAPI is compared with `app.openapi()`.

## Deployment notes

Production hides interactive docs and internal traces. Readiness returns 503 when data is unavailable.

## Known limitations

Booking links are safe platform-level HTTPS pages rather than guaranteed route-aware deep links.

## Future migration path

Add authenticated dependencies and richer data sources as separate versioned capabilities; never restore client-asserted authentication.
