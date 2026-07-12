# Production hardening audit

**Date:** 2026-07-12

## Findings and targeted changes

### Critical

No route-breaking or data-integrity critical issue remains in the implemented static-data scope. The production catalogue still contains only six seed offers and requires independent editorial verification before public claims are made.

### High

- Frontend handwritten legacy DTOs and `as any` mappings could misinterpret API 1.1. OpenAPI-generated types and a canonical mapper now compile the contract.
- Runtime configuration allowed unsafe production defaults. Typed settings now reject wildcard/local production origins and invalid limits.
- Snapshot components could load with mismatched versions. Repository startup now checks manifest, offer metadata, and facet versions, duplicates, and publishability.

### Medium

- Incoming request IDs were unconstrained; they now use a safe character/length policy.
- Proxy headers were trusted unconditionally; trust is now explicit configuration.
- API-mode UI repeated backend filtering/ranking; API mode now sends repeated filters and respects backend search order/labels.
- Rate-limit errors lacked no-store caching; all middleware errors now set it.

### Low

- Frontend z-index layers were undocumented; an explicit scale now constrains future overlays.
- Existing frontend lint errors in three utility/config files were corrected without component behavior changes.

## Verification evidence

Backend snapshot, OpenAPI, Ruff, mypy, and pytest pass. Live production-mode HTTP checks verified liveness/readiness, validation envelope, allowed and denied CORS, GZip, version headers, query-aware ETag/304, feature flags, and 429 with Retry-After. Frontend generated types, typecheck, tests, lint, and production build pass; remaining lint findings are non-blocking Fast Refresh warnings in existing shared component modules.

## Not verified locally

Docker is unavailable on the workstation. Docker build/startup must be proven by the GitHub Actions run. Dependency audit reports existing transitive vulnerabilities; remediation requires a separate compatibility review rather than an automatic major-version update.
