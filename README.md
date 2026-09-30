# CardOptimal Backend

FastAPI service that serves validated domestic-flight card offers. No database required — all data is file-based JSON/CSV.

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

cardsage (a separate project) produces the offer CSV and delivers it to
`data/source/offers.csv` in this repo (commit it on the branch you are building).
The backend does not scrape or convert anything itself. Column names follow
`demo_offers.csv`; `build_data_bundle.py` validates every row and writes a
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
