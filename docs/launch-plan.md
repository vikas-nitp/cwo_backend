# Launch plan — tasks by phase

Legend: ✅ done · ⬜ to do · ❓ needs a decision first. Repos: **CS** cardsage, **BE** cwo_backend, **FE** cardwiseoffer.

## Phase 0 — Merge what is built (½ day)
- ⬜ Review and merge the three `claude/inspiring-hawking-rvunlm` branches (CS, BE, FE) — merge BE first, then FE, then CS
- ⬜ Add repo secrets: `BACKEND_REPO_TOKEN` (FE), `FRONTEND_REPO_TOKEN` (BE) — read-only PATs
- ⬜ Confirm all three CIs go green on `main` (first real run of the new workflows)
- ✅ Done already: packaging, backend feed, tests, per-browser saved cards, flag enforcement, docs

## Phase 1 — Make the data pipeline trustworthy (1–2 weeks)
- ❓ Decide who runs the scraper and where (own machine/cron, self-hosted runner, or a CS GitHub Action that opens a PR to BE)
- ⬜ Implement that scheduler; make it produce `offers.csv` and open/commit it to BE
- ❓ Decide `WARNING` offers: show them (backend serves `PARTIAL`) or keep hidden — then enforce the 0.70–0.84 band or fix the docs (CS BUG-11)
- ❓ Decide: keep scraping international (`ACTIVE_PHASE2_CATEGORIES`)
- ⬜ CS: capture real-page fixtures and fix parser bugs BUG-01, 02, 04, 05, 08 (+ add golden tests, BUG-09)
- ⬜ CS: BUG-10 — require evidence for LLM-filled fields so the model cannot invent values
- ⬜ CS: add an alert when a platform returns 0 offers or a big drop (site redesign detection)
- ⬜ BE: decide strict vs lenient build on bad rows (today one bad row blocks deploy)

## Phase 2 — Production hardening (1 week)
- ⬜ Deploy BE (Render/Railway): set `APP_ENV=production`, `ALLOWED_ORIGINS`, `TRUST_PROXY_HEADERS=true`, `IP_HASH_SALT`; health check `/health/ready`; single instance
- ⬜ Deploy FE (Vercel): `VITE_DATA_SOURCE=api`, `VITE_API_BASE_URL`; make the build get the synced bundle
- ⬜ Verify Docker image builds and `/health/ready` is green; run the smoke test in `docs/runbook.md`
- ⬜ Mount a volume at `USER_DATA_DIR` (or skip saved cards at launch)
- ⬜ Run the VAPT checklist (`docs/deployment/vapt-checklist.md`) and fix findings
- ⬜ Add uptime monitoring + error tracking (frontend and backend)
- ⬜ BE: cap/TTL for per-session files, or move to a database (needed before >1 instance)

## Phase 3 — Compliance and trust (parallel with Phase 2)
- ❓ Legal review of scraping six commercial sites; confirm the cease-and-desist runbook is workable
- ❓ Analytics: choose a provider, wire the script, turn on `cookieConsentEnabled` together with it
- ⬜ Reconcile the privacy policy with what is actually collected (session id, subscriber e-mails, analytics)
- ⬜ Decide e-mail storage: provider/database + retention and deletion policy before enabling `subscriptionsEnabled`
- ⬜ Keep `privacyPolicyEnabled` / `termsOfServiceEnabled` on

## Phase 4 — Soft launch (1–2 weeks)
- ⬜ Launch with committed flag defaults (auth, saved cards, notifications, subscriptions, coupons, international all off)
- ⬜ Check daily: offer count vs CSV rows, expired offers, a manual spot-check of 10 offers against the platform pages
- ⬜ Measure the traffic signal in `docs/roadmap.md` (needs analytics from Phase 3)
- ⬜ Collect feedback on wrong/expired offers; add a "report an issue" path

## Phase 5 — Optional features (only after demand is proven)
- ❓ Real sign-in: pick an SMS/OTP provider (MSG91/Twilio/Firebase), add signed sessions in BE, move saved cards to accounts
- ⬜ Notifications: actually send expiring/new-offer alerts (needs e-mail/SMS provider)
- ⬜ Coupons (`couponCodeEnabled`) after verifying codes are accurate
- ⬜ International offers (`flightInternationalEnabled`) after parser quality is proven
- ⬜ Ranking without a fare: add a reference-fare rule so "20% off" and "₹500 flat" compare fairly
- ⬜ Booking URLs for more platforms (add `booking_url` to the cardsage output)
- ⬜ Affiliate IDs (`VITE_*_AFFILIATE_ID`) per `docs/affiliate-transition.md`
- ⬜ Database (Postgres) when traffic or multi-instance needs it

## Phase 6 — Clean-up (anytime)
- ⬜ Remove the dead flag `phase2UserFeaturesEnabled`
- ⬜ Cardsage mobile-app ingestion stays off until endpoints are legally cleared
- ⬜ Review the generated shadcn `ui/` components and the sign-in/profile screens (not yet reviewed line by line)
