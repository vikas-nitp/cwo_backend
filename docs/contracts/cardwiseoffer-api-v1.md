# CardwiseOffer API contract 1.1

Base path: `/api/v1`. Machine-readable source: `contracts/openapi.json`. Successful data responses expose `X-Contract-Version: 1.1`, `X-Data-Version`, and an `ETag`; `POST /search` is `no-store`.

## Data and feature configuration

`data/source/catalogue.yml` compiles platform-specific CSV, XLSX, and JSON sources into immutable offer, metadata, facet, manifest, and validation snapshots. Runtime loads every snapshot and `data/config/feature_flags.json` once during lifespan startup. Supported banks and platforms are derived only from publishable offers.

Unsupported capabilities (`authEnabled`, `offerLockingEnabled`, `savedCards`, and `dailyVisitorsEnabled`) must remain false. `allOffers=false` returns HTTP 403 with `FEATURE_DISABLED`; metadata and search remain available.

## Endpoints

- `GET /health/live`: process liveness.
- `GET /health/ready`: snapshot/config state, total publishable and currently active counts, data/config/contract versions.
- `GET /api/v1/meta`: derived metadata.
- `GET /api/v1/offers`: repeated `bank`, `platform`, `payment_method`, `booking_channel`, and `category` values use OR within a group and AND across groups. Pagination happens after filtering. The response contains self-excluding facet counts.
- `POST /api/v1/search`: selected banks are ranking preferences, not strict filters. An outside-bank alternative and no-card default may be returned.
- `GET /api/v1/feature-flags`: validated configuration plus stable `config_version`.

Catalogue and search offers share the canonical `Offer` fields, including `booking_url` and `extra`; search adds display/ranking and optional calculation fields. Exact savings exist only when `booking_amount` is supplied and eligible. No synthetic fare or price strip exists.

Errors use `{ "error": { "code", "message", "field", "request_id" } }` and are `no-store`. Contract examples under `contracts/examples/` are validated by the actual Pydantic models.

## Frontend synchronization

Generate TypeScript DTOs from `contracts/openapi.json`. API mode uses `VITE_DATA_SOURCE=api` (with temporary compatibility for `VITE_DATA_MODE`) and `VITE_API_BASE_URL`. UI behavior must follow all five flags and must not send client-auth assertions or rerank API search results.
