# Backend Readiness To-Do

## P0 — Required before frontend API integration

- [x] Typed feature flags and working `allOffers`
  - Evidence: loader, lifespan, route tests.
  - Files: `app/core/feature_flags.py`, `app/api/routes/offers.py`.
  - Test: `tests/test_feature_flags.py`.
  - Definition of done: configuration controls catalogue and unsafe flags fail readiness.
- [x] Multi-source ingestion and generated facets
  - Evidence: catalogue, adapters, five generated snapshots.
  - Files: `app/ingestion`, `scripts/build_offer_snapshot.py`.
  - Test: ingestion and facet suites.
  - Definition of done: CSV/XLSX/JSON compile through one validation path.
- [x] Multi-select filters and compatible canonical DTOs
  - Evidence: repeated query params and `SearchOffer(Offer)`.
  - Test: route/facet/search tests.
  - Definition of done: strict catalogue banks; preference-based search banks.
- [ ] Replace seed catalogue with 50–100 independently verified offers
  - Evidence: manifest currently reports six accepted rows.
  - Files: platform source files.
  - Test: snapshot build and editorial evidence review.
  - Definition of done: source URLs and offer terms are current and verified.
- [x] Complete frontend API integration verification
  - Evidence: generated contract/types and integration checklist.
  - Files: frontend adapter, contexts, navigation.
  - Test: frontend lint/test/build and API smoke test.
  - Definition of done: generated DTOs compile; API mode needs no `as any`, legacy strip, or UI reranking.

## P1 — Required before deployment

- [ ] Verify Docker startup and readiness
  - Evidence: Dockerfile exists; local CLI unavailable.
  - Files: Dockerfile, deployment environment.
  - Test: build/run image and query both health endpoints.
  - Definition of done: container is healthy with read-only snapshots/config.
- [ ] Confirm successful GitHub workflow for this branch
  - Evidence: workflow covers build, generated diffs, quality, tests, contracts, Docker.
  - Test: visible successful PR workflow.
  - Definition of done: all required checks are green.
- [ ] Configure real production/preview CORS origins and deployment observability
  - Evidence: environment-based allow-list and structured logging exist.
  - Test: browser preflight and platform logs.
  - Definition of done: only authorized origins work; startup failures are diagnosable.

## P2 — Deferred product capabilities

- [ ] Real authentication and offer locking
- [ ] Saved cards
- [ ] Daily visitor/analytics service
- [ ] Admin offer-management UI
- [ ] Automated offer collection
- [ ] Database migration
- [ ] Distributed rate limiting and background infrastructure
