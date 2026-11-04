# CardOptimal Backend

FastAPI service that serves validated flight card offers (domestic by default). No database required — all data is file-based JSON/CSV.

Part of a three-repo pipeline: **cardsage** (scrape/parse → CSV) → **cwo_backend** (validate + serve) → **cardwiseoffer** (frontend).
End-to-end steps: [docs/runbook.md](docs/runbook.md) · Flags: [docs/feature-flags.md](docs/feature-flags.md) · Open items: [docs/review-status.md](docs/review-status.md) · API contract: [docs/contracts/cardwiseoffer-api-v1.md](docs/contracts/cardwiseoffer-api-v1.md)

---

## Setup

```bash
pip install -r requirements-dev.txt
```

---

## Running

```bash
uvicorn app.main:app --reload --port 8001
```

API docs available at `http://localhost:8001/docs`.

---

## Data pipeline

Run these whenever cardsage produces new output or offer data changes.

**Step 1 — Receive the CSV from cardsage**

cardsage (a separate repo) produces the offer CSV: run `python3 -m cardsage backend-feed` there (it writes
`data/source/offers.csv` here when the repos are siblings) and commit the file.
The backend does not scrape or convert anything itself. Columns are defined by
`cardsage/core/backend_feed.py` (`BACKEND_CSV_COLUMNS`) and match `demo_offers.csv`; `build_data_bundle.py` validates every row and writes a
rejection report to `data/generated/validation-report.json`.

**Publishing rules.** Only rows with `is_active=true`, `publish_status=READY` and `evidence_status=VERIFIED` are served; `PARTIAL`/`UNVERIFIED` rows are kept in the snapshot but never shown. Any row that fails validation makes the build exit non-zero (and fails the Docker build) so bad data never ships silently; fix the row named in `data/generated/validation-report.json`.

Falls back to `data/source/demo_offers.csv` automatically when `offers.csv` is absent or header-only.

**Step 2 — Rebuild distribution bundle**

```bash
# From cwo_backend/
python3 scripts/build_data_bundle.py
```

Reads `data/source/offers.csv` (or demo fallback) → writes `data/generated/` and `data/distribution/frontend/`.
If a frontend checkout is found (sibling `../cardwiseoffer`, or `CWO_FRONTEND_DIR`), the bundle is also copied into its `src/data/generated/`.

**Step 3 — Sync to frontend**

```bash
# From cardwiseoffer/
npm run data:sync-backend
```

Copies `data/generated/` snapshots into the frontend's `src/data/generated/`.

---

## Feature flags

```bash
# Add or update a flag across all touch points at once
python3 scripts/add_feature_flag.py <flagName> <true|false>

# Example
python3 scripts/add_feature_flag.py couponCodeEnabled true
```

Always re-run `python3 scripts/build_data_bundle.py` after changing `app/core/feature_flags.py`.

---

## OpenAPI contract

```bash
python3 scripts/export_openapi.py
```

Always run this after changing any route or Pydantic model. The CI check (`test_openapi_is_current`) fails if the committed contract is stale.

---

## CI checks (run locally before pushing)

```bash
ruff format app scripts tests
ruff check app scripts tests
mypy app
python3 scripts/build_data_bundle.py && git diff --exit-code -- data/generated data/distribution/frontend
python3 scripts/export_openapi.py && git diff --exit-code -- contracts/openapi.json
python -m pytest
```

---

## Routes

| File | Prefix | Purpose |
|------|--------|---------|
| `health.py` | `/health` | Liveness probe |
| `meta.py` | `/api/v1` | Dataset metadata and last-updated timestamp |
| `offers.py` | `/api/v1/offers` | Paginated offer catalogue |
| `search.py` | `/api/v1/search` | Offer search by route, date, bank |
| `feature_flags.py` | `/api/v1/feature-flags` | Feature flag values |
| `availability.py` | `/api/v1/availability` | Data availability window |
| `user_cards.py` | `/api/v1/user/cards`, `/user/notification-prefs` | Saved cards and notification prefs, stored per browser (`X-Session-Id` header required) |
| `subscriptions.py` | `/api/v1/subscriptions` | Email capture for offer alerts |
| `visitors.py` | `/api/v1/visitors/count` | Active session count (2-min TTL) |

---

## Data source layout

```
data/
├── source/
│   ├── offers.csv          ← supplied by cardsage (committed)
│   └── demo_offers.csv     ← hand-curated fallback (committed; used when offers.csv is absent)
├── generated/              ← built by build_data_bundle.py (gitignored; the Docker build runs it)
│   ├── offers.snapshot.json
│   ├── metadata.snapshot.json
│   ├── facets.snapshot.json
│   └── manifest.json
├── distribution/
│   └── frontend/           ← built by build_data_bundle.py (gitignored)
│       ├── offers.json
│       ├── metadata.json
│       ├── airports.json
│       └── featureFlags.json
└── config/
    └── feature_flags.json  ← canonical flag values (committed)
```

---

## Configuration (environment variables)

| Variable | Default | Purpose |
|----------|---------|---------|
| `APP_ENV` | `dev` | `dev` / `test` / `production`. Production requires an explicit non-local `ALLOWED_ORIGINS`; `/docs` is dev-only; rate limiting is skipped in dev |
| `ALLOWED_ORIGINS` | localhost dev ports | Comma-separated CORS origins |
| `TRUST_PROXY_HEADERS` | `false` | **Set `true` behind Render/Railway**, otherwise all users share the proxy IP's rate-limit bucket |
| `IP_HASH_SALT` | dev placeholder | Key for hashing subscriber IPs — set a random value in production |
| `USER_DATA_DIR` | `./data` | Where `user_cards/` and `subscriptions/` are written (mount a volume to persist) |
| `*_SNAPSHOT_PATH`, `MANIFEST_PATH`, `FEATURE_FLAGS_PATH` | `data/generated/…`, `data/config/feature_flags.json` | Override data locations |
| `CONTRACT_VERSION`, `DEFAULT_PAGE_LIMIT`, `MAX_PAGE_LIMIT` | `1.1`, 20, 100 | Contract and paging |
| `META_CACHE_TTL`, `FLAGS_CACHE_TTL`, `OFFERS_CACHE_TTL` | 86400, 300, 600 s | `Cache-Control` max-age |
| `RATE_LIMIT_GLOBAL[_WINDOW]`, `RATE_LIMIT_SEARCH[_WINDOW]` | 30/60 s, 5/10 s | Per-IP limits (in-memory, single instance) |

## Runtime storage and scaling

- Saved cards, notification prefs and email subscriptions are files under `USER_DATA_DIR` (default `data/`).
  Each browser sends a random UUID in `X-Session-Id`; it namespaces that browser's data and is **not** authentication.
  Mount a persistent volume at `USER_DATA_DIR` if this data must survive redeploys.
- Rate limiting, the visitor counter and the file-store locks are per-process. Run a **single worker/instance**
  (the Dockerfile and Procfile pass `--workers 1`) or move these to a shared store before scaling out.
- Platforms are not configured: the platform list comes from the `platform_id` values in the CSV.

## Keeping the frontend in sync

The backend is the source of truth for data and the API contract. CI in both repos checks that
`contracts/openapi.json` and `contracts/examples/` are byte-identical (`scripts/check_frontend_contract_sync.py`,
`CWO_FRONTEND_DIR` overrides the sibling-directory lookup). To refresh the frontend after a data or contract
change, run `python scripts/build_data_bundle.py && python scripts/export_openapi.py` here, then `npm run data:build` in the frontend.
