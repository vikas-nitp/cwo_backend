# VAPT Pre-Deployment Security Checklist

Completed: 2026-09-21. Review before each production release.

---

## Backend (cwo_backend/)

| # | Area | Finding | Severity | Status |
|---|------|---------|----------|--------|
| B1 | CORS | `ALLOWED_ORIGINS` is read from env var; wildcard `*` is rejected at startup in production mode by `RuntimeSettings.production_safety` validator. No localhost origins are permitted in production. | High | Fixed — already in config |
| B2 | JWT / Auth secret | No JWT authentication on backend API (public read-only API). No hardcoded secrets. | N/A | Not applicable |
| B3 | Security headers | `X-Content-Type-Options`, `X-Frame-Options`, and `Referrer-Policy` were absent. Added `SecurityHeadersMiddleware` in `app/core/middleware.py` — applied on every response. | Medium | Fixed (this PR) |
| B4 | Error leak | Generic exception handler returns `"An unexpected error occurred."` — no stack traces exposed. `RequestValidationError` handler returns only the first validation message, never a full traceback. | Medium | Fixed — already safe |
| B5 | Input constraints | String query params in `/api/v1/offers` (`bank`, `platform`, `payment_method`, `booking_channel`, `category`) had no length cap. Added `max_length=50` per item via `Annotated[str, Query(max_length=50)]`. | Low | Fixed (this PR) |
| B6 | Rate limiting | In-memory token bucket (30 req/60s global, 5 req/10s search). Single-instance only — breaks under horizontal scaling. | Medium | Accepted Risk — mitigate with Cloudflare rate limiting at CDN layer before multi-instance deploy |
| B7 | Docs exposure | `/docs`, `/redoc`, `/openapi.json` disabled when `APP_ENV != dev`. | Low | Fixed — already in config |
| B8 | Body size limit | `BodySizeLimitMiddleware` rejects POST bodies > 32 KB. | Low | Fixed — already in config |
| B9 | Dependency vulnerabilities | Run `pip-audit` against `requirements.txt` before each release. | Medium | Accepted Risk — add `pip-audit` to CI |
| B10 | Secrets in env | No secrets committed to repo. Ensure Railway env vars (`ALLOWED_ORIGINS`, `APP_ENV=production`) are set before go-live. | Critical | Accepted Risk — operator responsibility |

---

## Frontend (cardwiseoffer/)

| # | Area | Finding | Severity | Status |
|---|------|---------|----------|--------|
| F1 | Open redirect / unsafe href | `OfferCard.tsx` rendered `offer.platformUrl` directly in `<a href>` without an allowlist check. Added `isAllowed(ctaHref)` guard (exported from `platformUrlBuilder.ts`). If the URL is not on the `ALLOWED_HOSTS` set (HTTPS only), the CTA renders disabled. | High | Fixed (this PR) |
| F2 | Content Security Policy | No CSP meta tag in `index.html`. Added a CSP meta tag restricting scripts, styles, images, and connect targets. Note: `frame-ancestors` is ignored in `<meta>` CSP — enforced via `X-Frame-Options: DENY` from backend security headers instead. | Medium | Fixed (this PR) |
| F3 | Sensitive data in localStorage | Only `cwo-theme` (UI theme preference) is written to `localStorage`. No phone numbers, session tokens, or auth state are stored in `localStorage` or `sessionStorage`. Auth state lives in React memory only. | Critical | Clean — no action needed |
| F4 | Affiliate URL injection | `buildAffiliateUrl` in `affiliateLinks.ts` calls `isAllowed()` before appending any params, and returns the URL unchanged if the host is not whitelisted. `OfferCard.tsx` then re-checks the result with `isAllowed()` before setting `canBook=true`. | Medium | Fixed (this PR) |
| F5 | Dependency audit | Run `npm audit` before each release; address `critical` and `high` advisories. | Medium | Accepted Risk — add `npm audit --audit-level=high` to CI |
| F6 | `rel="noopener noreferrer"` | All outbound `<a target="_blank">` links carry `rel="noopener noreferrer"`. | Low | Fixed — already in place |

---

## Pre-Go-Live Operator Checklist

- [ ] Set `APP_ENV=production` on Railway
- [ ] Set `ALLOWED_ORIGINS` to the production Vercel domain (e.g. `https://cardsage.vercel.app`)
- [ ] Verify `/docs` returns 404 in production
- [ ] Enable Cloudflare proxy for rate limiting and DDoS protection
- [ ] Run `pip-audit` and `npm audit` — no critical/high advisories
- [ ] VAPT scan (external penetration test) before accepting user data (phone numbers)
- [ ] Review privacy policy with a legal advisor before public launch
