# Review status — fixes done, pending, and decisions needed

Branch: `claude/inspiring-hawking-rvunlm` (both repos). Same file lives in `cwo_backend/docs/` and `cardwiseoffer/docs/`.
Last verified: backend 112 tests + ruff + mypy green; frontend 185 tests + typecheck + lint green. Docker build and GitHub Actions were NOT run.

## 1. Fixed

### Original six items
| # | Item | Fix |
|---|------|-----|
| 1 | Date-dependent backend tests (10 failing) | Tests build snapshots from committed `tests/fixtures/offers.fixture.csv` with a frozen date; no dependence on pipeline output |
| 2 | Frontend `savingsLabel` tests failing | Restored `pct < 50` rule (develop merge had overwritten it with `<= 100`) |
| 3 | Saved cards shared by all visitors | Per-browser `X-Session-Id`; per-session JSON files; lock + atomic writes; subscriptions locked too |
| 4 | Hardcoded / dead config | Removed unused `SUPPORTED_PLATFORMS`; platforms are data-driven; single-worker documented and enforced in Dockerfile/Procfile |
| 5 | Fragile cross-repo setup | `CWO_BACKEND_DIR` / `CWO_FRONTEND_DIR`; sync script validates inputs first; both CIs check out the other repo and verify contract equality; cardsage scrape workflow + converter removed; `offers.csv` is committable |
| 6 | Minor | Removed duplicate Bun lockfiles; added `types-PyYAML`; fixed mypy errors; README/docstring cleanup |

### Bugs found during review — backend
- `/offers` ETag ignored the date → stale offers after midnight (now includes `active_on`)
- Body-size limit buffered whole uploads (now enforced while streaming; chunked uploads rejected with 413)
- Log handler re-opened the file on every record after first midnight (now schedules next rollover)
- App could crash at startup in Docker (`logs/` not writable) → Dockerfile creates it; logging degrades to console
- Docker image had no offer data (`data/generated` is gitignored) → Dockerfile builds it
- CORS blocked `DELETE` and `X-Session-Id` → allowed
- Rate limit/logging treated `/health/live|ready` as normal traffic → all `/health*` exempt
- `CASHBACK >= 100` computed as a percentage → now flat rupees (matches frontend)
- Search with no matching offers returned 400 → now 200 with empty offers + date strip
- Search allowed max 2 banks but signed-in UI allows 4 → backend accepts up to 4
- availability returned 500 when data unloaded → 503; visitor counter capped (10,000); IP hash now keyed (HMAC); `list_publishable` uses IST; OpenAPI docs corrected (`valid_days` is Python weekday, `evidence_status` includes PARTIAL)
- CI: exact branch match when picking the other repo's branch, distinguishes auth errors from "branch missing", token sent as header not in URL

### Bugs found during review — frontend
- Frontend sent `CREDIT_CARD`/`DEBIT_CARD`; API expects `CREDIT`/`DEBIT` (every card save was a 422)
- Timeouts surfaced as "Unknown API error"; pre-aborted requests still went out
- Analytics fired before the visitor answered the cookie banner (now requires explicit accept)
- API-mode results lost the primary-card highlight (label keys didn't match `decorateResults`)
- API CASHBACK ≥ 100 savings treated as 0
- Local bundle served unpublished/unverified offers (now filtered like the backend)
- Delete-card failures were silent; profile fetched cards before sign-in/flag guards
- Session id: validated against backend pattern, safe fallback when `crypto.randomUUID` or storage is unavailable; privacy policy mentions it
- Date strip: next arrow no longer runs past `availability_end`; API "Up to ₹…" labels shortened
- "N offers tracked" badge hidden in API mode (count was stale); page size change resets to page 1
- Frontend CI previously could not typecheck on a clean checkout (missing generated data) → now builds backend data first

## 2. Pending (not done)
| Item | Why pending |
|------|-------------|
| Docker image build, CI workflows | Not runnable in this environment; first real run may surface issues |
| CI secrets | Add `BACKEND_REPO_TOKEN` (frontend repo) and `FRONTEND_REPO_TOKEN` (backend repo) — read-only PATs |
| Deployment env vars | Set `TRUST_PROXY_HEADERS=true`, `IP_HASH_SALT=<random>`, and `ALLOWED_ORIGINS` on Render/Railway |
| Unread UI code | shadcn `ui/` components not reviewed; SignInModal, Header, ProfileModal, AllOffersSection, BankMultiSelect only skimmed |
| Open PRs | None created (not requested) |

## 3. Needs your decision
1. **Real account sign-in.** Frontend auth is a stub (any 6-digit OTP works, memory-only). Saved cards are per *browser*, not per *account* (shared between accounts on one browser, empty on a new device). Needs: SMS/OTP provider choice (e.g. MSG91, Twilio, Firebase) + signed sessions on the backend.
2. **PARTIAL offers.** Backend serves only `VERIFIED` offers. cardsage's old converter marked WARNING offers as `PARTIAL`+`READY`, which are now invisible. Options: (a) cardsage emits `VERIFIED` for rows to show, or (b) backend also serves `PARTIAL`.
3. **Strict build on bad rows.** One invalid CSV row fails `build_data_bundle.py` and therefore the Docker build. Keep (safe, blocks deploys) or publish the valid rows and only warn?
4. **Ranking without a fare.** With no booking amount, backend compares "20% off" (20) against "₹500 flat" (500). Needs a product rule (e.g. assume a reference fare such as ₹5,000).
5. **Unbounded user files.** Each new `X-Session-Id` creates a file; rate limit slows but doesn't stop abuse. Options: cap total files, TTL cleanup, or move to a database (also needed before running >1 instance).
6. **Persistence.** Saved cards/subscriptions live on disk (`USER_DATA_DIR`); lost on redeploy unless a volume is mounted. Mount a volume or adopt a DB?
7. **Booking URL fallback.** Backend hardcodes booking URLs for MakeMyTrip and Cleartrip only; other platforms rely on `booking_url` in the CSV. Add `booking_url` to cardsage output, or keep a config map?
8. **Email PII.** Subscriber emails are stored as plaintext JSONL. Fine for MVP? Otherwise forward to an email provider/DB and add a retention/deletion policy.
9. **CI branch fallback.** If the other repo has no same-named branch, CI falls back to `main`. Acceptable, or require matching branch names?
