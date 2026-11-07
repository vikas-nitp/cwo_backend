# Deployment Plan — CardWiseOffer

> Phase 1: static file-based, no database. Phase 3 adds PostgreSQL.

## Architecture

```
cardwiseoffer.com  (frontend)          api.cardwiseoffer.com  (backend)
Vercel / Cloudflare Pages              Railway / Render.com
React SPA (Vite build)                 FastAPI + uvicorn
        │                                      │
        └──────── HTTPS API calls ─────────────┘
                                               │
                              offers.snapshot.json (bundled in image)
                              feature_flags.json
```

## Stack decisions

| Layer | Choice | Why |
|---|---|---|
| Frontend hosting | **Vercel** (free tier) | Zero-config Vite deploy, PR previews, custom domain |
| Backend hosting | **Railway** ($5/mo starter) | Dockerfile already in repo, always-on, custom domain |
| cardsage scraper | **GitHub Actions** cron | Runs on schedule, commits updated JSONs, free |
| Database | File-based JSON (Phase 1) | Already working; Phase 3 upgrades to PostgreSQL |
| Domain | cardwiseoffer.com | Frontend; api.cardwiseoffer.com for backend |

## Pre-deployment checklist

### Backend (cwo_backend/)
- [ ] Set `CORS_ORIGINS` env var to `https://cardwiseoffer.com`
- [ ] Set `ENVIRONMENT=production` in Railway env vars
- [ ] Set `LOG_LEVEL=INFO`
- [ ] Health check endpoint: `GET /health` → 200
- [ ] Dockerfile builds cleanly: `docker build -t cwo_backend .`
- [ ] `offers.snapshot.json` bundled into Docker image or mounted as volume

### Frontend (cardwiseoffer/)
- [ ] Set `VITE_API_BASE_URL=https://api.cardwiseoffer.com` in Vercel env vars
- [ ] `npm run build` passes with no type errors
- [ ] `npm run data:check` passes
- [ ] Privacy Policy and Terms pages live at `/privacy` and `/terms`
- [ ] `robots.txt` in `/public`

### cardsage scraper (GitHub Actions)
- [ ] `.github/workflows/scrape.yml` — runs `python -m cardsage run --source all` on cron
- [ ] Commits updated `cardsage/output/latest/*.json` to repo
- [ ] Triggers backend rebuild / data refresh

## VAPT before go-live (P0)

Before accepting real user data (sign-in, email):
- [ ] XSS audit on all user-visible offer fields
- [ ] Rate limiting on `/api/v1/search` and auth endpoints
- [ ] No PII logged in plaintext
- [ ] HTTPS enforced, HSTS header set
- [ ] OTP brute-force protection

## Monetization

> Full analysis with projections: **[docs/deployment/revenue.md](revenue.md)**

**Priority order** (fix B1 bug first — it's a revenue gate, not just a UX fix):

1. **Fix `offerMapper.ts:55`** → enables all affiliate click-through (Day 1)
2. **VCommission + Admitad** publisher accounts → replace CTA with affiliate links (Day 1)
3. **Email capture** on guest gate and results page (Month 1)
4. **AdSense + Media.net** display ads — Media.net pays 2–3× AdSense CPM for finance (Month 1)
5. **Card apply CTA** via BankBazaar sub-affiliate (Month 2–3)
6. **Premium subscription** ₹99/month via Razorpay (Month 6+, needs Phase 3 DB)

Rough projection at 1,000 DAU: ₹45,000/mo at launch → ₹3,20,000/mo at Month 6.

## Phase 3 upgrade path (database)

When adding PostgreSQL:
1. Replace `FileOfferRepository` with `PostgresOfferRepository`
2. Add Alembic migrations
3. cardsage → conversion script → direct DB insert (skip snapshot.json)
4. Add Redis for feature flag caching
