# CardwiseOffer API v1

Base path: `/api/v1`. Machine-readable source: `contracts/openapi.json`.

## Runtime and data

The service supports only `MAKEMYTRIP`, `CLEARTRIP`, and `FLIGHT_DOMESTIC`. Publishable offers are active, `READY`, `VERIFIED`, and valid on the requested date. Money is returned as JSON numbers; absent optional amounts are `null`.

## Endpoints

- `GET /health/live`: process liveness.
- `GET /health/ready`: snapshot state, offer count, and data version; 503 if unavailable or empty.
- `GET /api/v1/meta`: derived banks, platforms, methods, categories, channels, and airports.
- `GET /api/v1/offers`: filters `bank`, `platform`, `payment_method`, `booking_channel`, `category`, `active_on`; pagination uses `page` and `limit`.
- `POST /api/v1/search`: accepts `from`, `to`, `date`, up to two `banks`, supported `platforms`, category, and optional positive `booking_amount`.
- `GET /api/v1/feature-flags`: release capability flags; authentication and locking are false.

Search dates range from today through today plus ten days. Origin and destination must differ. Exact estimates exist only when `booking_amount` is present and eligibility permits calculation. No fare or price strip is returned.

Ranking kinds are `SELECTED_CARD`, `SECOND_SELECTED_CARD`, `BETTER_ALTERNATIVE`, `DEFAULT_OFFER`, and `GENERAL_BEST`. Backend order is authoritative.

Errors use `{ "error": { "code", "message", "field", "request_id" } }`. Examples under `contracts/examples/` are executable contract fixtures.

## Frontend synchronization

Copy this document, `contracts/openapi.json`, and `contracts/examples/*` into the frontend contract location or consume them from a published artifact. Generate TypeScript types from OpenAPI. Do not merge a contract change unless backend examples/tests pass and the frontend adapter/build accepts the regenerated types.
