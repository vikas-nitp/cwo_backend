# Backend readiness audit

**Date:** 2026-07-12

| Area | Current status | Evidence | Gap | Required action |
| --- | --- | --- | --- | --- |
| Lifespan/startup | IMPLEMENTED | `app/main.py`; route tests | Docker startup unverified locally | Verify in CI/container |
| File repository | IMPLEMENTED | `file_offer_repository.py`; repository tests | Database deliberately absent | Keep protocol boundary |
| Multi-source builder | IMPLEMENTED | source adapters; ingestion tests | Production catalogue has six records | Replace seeds with verified research |
| Facet snapshot/dynamic facets | IMPLEMENTED | generated snapshot; facet tests | None for current scope | Keep generated-only |
| Domain calculations/ranking | IMPLEMENTED | calculation/ranking tests | Real fares unavailable | Accept booking amount only |
| Feature flags | IMPLEMENTED | typed loader and flag tests | Unsupported capabilities deferred | Keep safe validation |
| Health/readiness | IMPLEMENTED | readiness tests | Container probe unverified locally | Verify Docker/host |
| Errors/middleware | IMPLEMENTED | route tests | In-memory rate limiting only | Defer distributed limits |
| OpenAPI/examples | IMPLEMENTED | contract tests | Frontend generator must be rerun on changes | Enforce CI |
| Legacy modules | IMPLEMENTED | deleted from active packages; negative import test | Git history retains old code | No action |
| GitHub CI | IMPLEMENTED_BUT_UNVERIFIED | workflow definition | This branch has no run yet | Confirm PR check |
| Docker | IMPLEMENTED_BUT_UNVERIFIED | Dockerfile | Docker CLI absent locally | Use GitHub runner |
| Frontend synchronization | PARTIALLY_IMPLEMENTED | integration checklist and OpenAPI | UI behavior requires frontend PR verification | Generate/build/test frontend |

## Baseline before changes

- Snapshot build: passed, six offers.
- Ruff format: failed; six superseded legacy files required formatting.
- Ruff lint: failed with 11 legacy import/export findings.
- Mypy: failed with eight legacy-service import errors.
- Pytest: 27 passed.
- OpenAPI export: passed.
- Docker: not run; `docker` command unavailable.

## Architecture after readiness work

Catalogue-driven source adapters normalize into one Pydantic model, generate five immutable snapshots, and load once with validated feature configuration. Catalogue facets and search ranking remain separate domain behaviors.

## Test and deployment procedure

Run the commands in README and CI. Deploy the Dockerfile with `/health/ready` as the readiness probe and explicit production origins.

## Known limitations and future path

Real authentication, saved cards, locking, visitor analytics, scraping, database persistence, distributed rate limiting, and admin workflows are deferred. The current offer catalogue remains a small seed set.
