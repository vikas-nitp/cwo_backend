# CardwiseOffer backend

FastAPI service for validated, static domestic-flight card offers from MakeMyTrip and Cleartrip. It requires no database and does not generate flight fares.

## Local verification

```bash
python -m pip install -r requirements-dev.txt
python scripts/build_offer_snapshot.py
python scripts/export_openapi.py
ruff format --check app scripts tests
ruff check app scripts tests
mypy app
pytest
uvicorn app.main:app --reload --port 8001
```

The source catalogue is `data/source/catalogue.yml`; it can combine platform-specific CSV, XLSX, and JSON files. Runtime reads the committed JSON files under `data/generated/` and validated feature flags under `data/config/` once at startup. API documentation is available at `/docs` in development.

See [`docs/contracts/cardwiseoffer-api-v1.md`](docs/contracts/cardwiseoffer-api-v1.md) for the stable API contract and [`docs/skills/README.md`](docs/skills/README.md) for dated implementation records.

## Routes

| Router | Prefix | Purpose |
|--------|--------|---------|
| `health.py` | `/health` | Liveness probe |
| `meta.py` | `/api/v1` | Dataset metadata and last-updated timestamp |
| `offers.py` | `/api/v1` | Paginated offer catalog |
| `search.py` | `/api/v1` | Offer search by route, date, bank |
| `feature_flags.py` | `/api/v1` | Feature flag values |
| `availability.py` | `/api/v1` | Data availability window |
| `visitors.py` | `/api/v1` | `GET /visitors/count` — in-memory active session count (2-min TTL). Returns 404 when `visitorCountEnabled` FF is off. |
