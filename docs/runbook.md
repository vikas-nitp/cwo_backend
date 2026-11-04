# Runbook — from scrape to production

Three repos live side by side:

```
WORKSPACE/
├── cardsage/        scraper/parser  → produces the offer CSV
├── cwo_backend/     FastAPI API     → validates the CSV, serves offers
└── cardwiseoffer/   React frontend  → consumes the API (or the bundled snapshot in local mode)
```

## 1. First-time setup

```bash
# cardsage (Python 3.11+)
pip install -e "cardsage/[llm,dev]" && playwright install webkit
cp cardsage/.env.example cardsage/.env        # optional: ANTHROPIC_API_KEY, platform cookies

# backend (Python 3.12 in CI, 3.11+ works)
pip install -r cwo_backend/requirements-dev.txt

# frontend (Node 20)
( cd cardwiseoffer && npm ci )
```

## 2. Refresh the data (daily or on demand)

```bash
python3 -m cardsage run --source all           # scrape + normalise + validate  (~minutes)
python3 -m cardsage backend-feed               # → cwo_backend/data/source/offers.csv
( cd cwo_backend && python3 scripts/build_data_bundle.py )   # validates EVERY row; non-zero exit on any bad row
( cd cardwiseoffer && npm run data:build )     # copy bundle + OpenAPI contract, validate
```

Check `cwo_backend/data/generated/validation-report.json` — `accepted_row_count` should equal the CSV row count.
Only rows with `evidence_status=VERIFIED` **and** `publish_status=READY` are shown to users, so also compare
`accepted_row_count` with the number of offers visible on `/api/v1/offers`.

One command for the last three steps: `python3 -m cardsage run --source all --sync-frontend`.

## 3. Run locally

```bash
( cd cwo_backend && uvicorn app.main:app --port 8001 --reload )            # http://localhost:8001/docs
( cd cardwiseoffer && VITE_DATA_SOURCE=api VITE_API_BASE_URL=http://localhost:8001 npm run dev )
# or, no backend at all (bundled snapshot):  npm run dev
```

## 4. Checks before every push

| Repo | Command |
|------|---------|
| cardsage | `python3 -m pytest cardsage/tests -q` |
| backend | `ruff format --check app scripts tests && ruff check app scripts tests && python -m mypy app && python -m pytest && python scripts/export_openapi.py && git diff --exit-code contracts/openapi.json` |
| frontend | `npm run data:build && npm run lint && npm run typecheck && npm test && npm run build` |

Changing an API route or model: backend → `python scripts/export_openapi.py` → frontend → `npm run data:build && npm run generate:api`.
Both CIs fail if the two repos' `contracts/` differ.

## 5. Deploy

1. Commit `cwo_backend/data/source/offers.csv` (and nothing under `data/generated`, it is gitignored).
2. Build the backend image — `Dockerfile` runs `build_data_bundle.py` itself; a bad CSV row fails the build (intended).
3. Backend env: `APP_ENV=production`, `ALLOWED_ORIGINS=https://<frontend>`, `TRUST_PROXY_HEADERS=true`, `IP_HASH_SALT=<random>`,
   optional `USER_DATA_DIR` on a mounted volume. Health check: `/health/ready`. Single worker/instance only.
4. Frontend env (build time): `VITE_DATA_SOURCE=api`, `VITE_API_BASE_URL=https://<api>`. The Vite build imports
   `src/data/generated/*`, so the build machine needs the synced bundle (`npm run data:build` with the backend checked out, or committed output).
5. Smoke test: `curl https://<api>/health/ready`, open the site, run one search.

## 6. Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| Vite: `Failed to resolve import "@/data/generated/…"` | Bundle not synced → `npm run data:build` (dev/test/typecheck do this automatically) |
| `build_data_bundle.py` exits 1 | Bad CSV row; read `data/generated/validation-report.json` `errors[]` (row number + message) |
| API `/health/ready` 503 `DATA_NOT_READY` | No snapshot in the image/volume, or **every** offer has expired |
| Offers missing in the app though present in the CSV | `evidence_status` not `VERIFIED` (validator `WARNING` → `PARTIAL`), or `publish_status` `DRAFT` (confidence < 0.55), or `is_active=false` |
| Everyone gets 429 in production | `TRUST_PROXY_HEADERS` not `true` behind the host's proxy (all users share one IP bucket) |
| Saved cards vanish after deploy | `USER_DATA_DIR` is not on a persistent volume |
| `--sync-frontend` says repo not found | Repos must be siblings named `cwo_backend` and `cardwiseoffer` |
