# Frontend/backend synchronization

**Date:** 2026-07-12

## Purpose and previous behavior

The frontend used handwritten legacy DTOs, `strip7days`, and `as any` mappings that no longer matched API contract 1.1.

## Integration checklist

- Generate DTOs from backend OpenAPI and never hand-copy API response models.
- Use canonical common offer fields for catalogue and search; preserve search-only ranking/calculation fields.
- Treat API search order as authoritative and hide the synthetic date strip in API mode.
- `authEnabled=false`: hide login/profile UI.
- `offerLockingEnabled=false`: never show locked offers.
- `allOffers=false`: hide navigation and do not call `/offers`.
- `savedCards=false`: hide saved-card UI.
- `dailyVisitorsEnabled=false`: hide visitor UI and do not call stats endpoints.
- Use `VITE_DATA_SOURCE=api` and `VITE_API_BASE_URL`; no fake auth header.

## Contract, test, and deployment

Synchronize `contracts/openapi.json`, examples, and generated types. Run frontend tests, lint, and build in both local and API modes. Production backend CORS must list the deployed frontend origin.

## Known limitations and future path

The backend contains only seed offer data. Real authentication-related UI remains intentionally disabled until a server-authenticated dependency exists.
