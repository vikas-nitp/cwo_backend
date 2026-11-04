# Feature flags

Single source of truth: `data/config/feature_flags.json` (backend). The API serves it at
`GET /api/v1/feature-flags` (cached 5 min); the frontend bundles a copy in local mode
(`src/data/generated/featureFlags.json`). The model is strict: unknown or mistyped keys stop the app from starting.

**Add or change a flag everywhere at once:** `python3 scripts/add_feature_flag.py <flagName> <true|false>`
(updates the Pydantic model, JSON, OpenAPI contract, a test, and — if the frontend sits next to this repo or
`CWO_FRONTEND_DIR` is set — the frontend contract, types and capability map). Then rebuild: `python3 scripts/build_data_bundle.py`.

Flags are read at process start: **changing the JSON needs a redeploy/restart**, there is no hot reload.

## Reference (committed defaults)

| Flag | Default | Backend enforcement | Frontend effect | Notes |
|------|---------|---------------------|-----------------|-------|
| `publicAllOffersEnabled` | on | `GET /offers` → 403 `FEATURE_DISABLED` when off | Shows the "All Offers" tab | |
| `couponCodeEnabled` | **off** | Coupon codes blanked in `/offers` and `/search` | Shows coupon chip on cards | Off = codes never leave the server |
| `bookingAmountComparisonEnabled` | on | `/search` with `booking_amount` → 400 `BOOKING_COMPARISON_DISABLED` | Fare input + "save ₹X more" | |
| `flightInternationalEnabled` | **off** | `/offers?category=FLIGHT_INTERNATIONAL` and `/search` with that category → 403; `/offers` defaults to domestic only | Local-mode bundle drops international rows | cardsage exports international offers by default; this flag keeps them hidden |
| `visitorCountEnabled` | on | `/visitors/count` returns 404 when off | Live "N browsing" badge (polls every 60 s) | Counts client-supplied ids; indicative only |
| `subscriptionsEnabled` | **off** | `/subscriptions/email` → 404 when off | Footer e-mail capture | Stores plain-text e-mails on disk |
| `userCardsEnabled` | **off** | `/user/cards*` → 404 when off | Profile "saved cards", cards in All Offers | Needs `authEnabled`; data is per browser (`X-Session-Id`) |
| `notificationsEnabled` | **off** | `/user/notification-prefs` → 404 when off | Notification toggles on Profile | Preferences are stored but **nothing sends notifications yet** |
| `authEnabled` | **off** | none | "Sign in" button, 4-card compare for signed-in users | Frontend-only **stub**: any 6-digit OTP signs in, state is memory-only. Do not rely on it for access control |
| `cookieConsentEnabled` | **off** | none | Cookie banner; gates analytics on explicit accept | See "Combinations to avoid" |
| `analyticsEnabled` | on | none | Calls `window.gtag` if present | **No analytics script is loaded anywhere** (`index.html` has no gtag), so this tracks nothing today |
| `howItWorksEnabled` / `aboutEnabled` / `contactEnabled` | on | none | Show/hide the section | |
| `privacyPolicyEnabled` / `termsOfServiceEnabled` | on | none | Footer links and `/privacy`, `/terms` routes | Keep on in production |
| `splashScreenEnabled` | off | none | Intro splash | |
| `homeEntranceAnimationEnabled` | on | none | Home entrance animation | |
| `phase2UserFeaturesEnabled` | on | none | Mapped into capabilities but **read by nothing** | Dead flag; safe to remove in a future cleanup |

## Combinations to avoid

- `analyticsEnabled=on` with `cookieConsentEnabled=off`: once a gtag provider is wired in, every visitor is tracked with no
  consent step (India DPDP Act 2023 / consent expectations). Turn consent on first.
- `userCardsEnabled` / `notificationsEnabled` without `authEnabled`: the UI only offers them to signed-in users, so they are unreachable.
- `authEnabled=on` in production: the sign-in is a stub (see above).

## Production recommendation

Keep committed defaults for launch (`auth`, `userCards`, `notifications`, `subscriptions`, `coupon`, `international` all off) and
turn features on one at a time, each with its prerequisite (real auth, e-mail provider, consent banner, etc.).
