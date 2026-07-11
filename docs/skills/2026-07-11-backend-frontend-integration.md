# Backend/frontend integration skill

**Date:** 2026-07-11
**Purpose:** Keep `cwo_backend` and `cardwiseoffer` aligned without modifying the frontend's active PR.

## Previous behavior

The frontend API adapter consumes legacy fields and a synthetic seven-day strip. Local mode already has a canonical view-model boundary.

## New architecture

The backend owns API ranking and exposes canonical `platform_id`, `bank_id`, `min_transaction`, estimates, and `booking_url`. API mode must map this response directly and must hide the date strip when absent.

## Files changed

Backend-only contract artifacts were added under `contracts/` and `docs/contracts/`. No `cardwiseoffer` file was modified.

## Configuration

After frontend adapter synchronization: `VITE_DATA_MODE=api` and `VITE_API_BASE_URL=<backend origin>`. The existing frontend uses `VITE_DATA_MODE`, not the brief's older `VITE_DATA_SOURCE` name.

## Test procedure

Generate TypeScript types from `contracts/openapi.json`, validate fixtures, run frontend unit tests/build, then smoke-test local and API modes against the same UI components.

## Deployment notes

Add the exact frontend preview and production origins to backend `ALLOWED_ORIGINS`.

## Known limitations

The current frontend checkout is not contract-compatible without adapter/type updates; those changes belong to its existing PR and were intentionally not made here.

## Future migration path

Automate copying or publishing OpenAPI and generate frontend types in CI instead of maintaining handwritten backend interfaces.
