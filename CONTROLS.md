# CardOptimal — System Controls Reference

Single-file cross-system quick reference.
Two control files own the entire runtime behaviour of this product.

```
../cardsage/constants/phases.py     ← parser knobs
data/config/controls.json           ← product knobs (backend + frontend)   ← YOU ARE HERE
```

---

## QUICK REFERENCE

### Add IXIGO + YATRA to production

1. `controls.json` → `platforms.supported`:
   ```json
   "supported": ["MAKEMYTRIP", "CLEARTRIP", "IXIGO", "YATRA"]
   ```
2. Verify IXIGO/YATRA are in `phases.py` → `ENABLED_SOURCES` (they already are)
3. Run `python3 scripts/build_data_bundle.py`
4. On Railway: `SUPPORTED_PLATFORMS=MAKEMYTRIP,CLEARTRIP,IXIGO,YATRA` (env var overrides file)

### Enable international flights (end-to-end)

Both files must change together:
```
phases.py          PARSE_INTERNATIONAL_OFFERS = True
                   ACTIVE_PHASE2_CATEGORIES = ["FLIGHT_INTERNATIONAL"]

controls.json      featureFlags.flightInternationalEnabled = true
```

### Enable coupon code display

```
phases.py          COUPON_EXTRACTION_ENABLED = True  (already True)

controls.json      featureFlags.couponCodeEnabled = true
```

### Activate social links (when accounts are live)

1. `cardwiseoffer/src/constants/index.ts` → fill `SOCIAL_LINKS.INSTAGRAM` / `.YOUTUBE`
2. `controls.json` → `featureFlags.instagramEnabled: true` / `youtubeEnabled: true`
3. Run `python3 scripts/build_data_bundle.py`

### Launch splash screen

```
controls.json      featureFlags.splashScreenEnabled = true
```

### Turn on user accounts (auth + saved cards)

```
controls.json      featureFlags.authEnabled = true
                   featureFlags.userCardsEnabled = true
                   featureFlags.notificationsEnabled = true
                   featureFlags.subscriptionsEnabled = true
```

---

## FILE 1 — Parser

**`cardsage/constants/phases.py`**

| Knob | Current | What it does |
|------|---------|--------------|
| `ENABLED_SOURCES` | all 10 | Which sites get crawled each run |
| `VISION_EXTRACTION_ENABLED` | `True` | Screenshot → Claude vision pass |
| `LLM_ENRICHMENT_ENABLED` | `True` | LLM enrichment for low-confidence offers |
| `COUPON_EXTRACTION_ENABLED` | `True` | OCR coupon code extraction |
| `PARSE_INTERNATIONAL_OFFERS` | `False` | Parse intl offers during crawl |
| `ACTIVE_PHASE2_CATEGORIES` | `[]` | Unlock non-domestic categories for export |
| `SKIP_CONFIRMED_EXPIRED` | `True` | Skip re-crawl of confirmed expired offers |
| `PLATFORM_START_DELAY_SECONDS` | `5.0` | Polite stagger between platform crawls |
| `MOBILE_WEB_ENABLED` | `False` | Mobile viewport emulation (adds no extra offers) |
| `MOBILE_APP_ENABLED` | `False` | Native app API ingestion (not yet implemented) |

---

## FILE 2 — Product (backend + frontend)

**`cwo_backend/data/config/controls.json`**

### Platforms

| Knob | Current | What it does |
|------|---------|--------------|
| `platforms.supported` | `["MAKEMYTRIP","CLEARTRIP"]` | Platforms the API exposes to users |
| `platforms.available` | 6 entries | Documentation only — all adapters with working code |

Override for a deploy without editing this file:
```
SUPPORTED_PLATFORMS=MAKEMYTRIP,CLEARTRIP,IXIGO,YATRA   # Railway env var
```

### Feature Flags

| Flag | Current | What it does |
|------|---------|--------------|
| `publicAllOffersEnabled` | `true` | All offers browser section |
| `bookingAmountComparisonEnabled` | `true` | Fare input + savings comparison |
| `analyticsEnabled` | `true` | PostHog analytics events |
| `visitorCountEnabled` | `true` | Visitor count badge |
| `tieredDiscountEnabled` | `true` | Tiered discount offer display |
| `homeEntranceAnimationEnabled` | `true` | Hero entrance animation |
| `howItWorksEnabled` | `true` | How it works section |
| `aboutEnabled` | `true` | About section in footer |
| `contactEnabled` | `true` | Contact section in footer |
| `privacyPolicyEnabled` | `true` | Privacy policy page + footer link |
| `termsOfServiceEnabled` | `true` | Terms page + footer link |
| `couponCodeEnabled` | `false` | Coupon code UI on offers |
| `flightInternationalEnabled` | `false` | International flight search |
| `cookieConsentEnabled` | `false` | Cookie consent banner |
| `authEnabled` | `false` | Sign-in / auth flow |
| `userCardsEnabled` | `false` | Saved cards on profile |
| `subscriptionsEnabled` | `false` | Email capture bar |
| `notificationsEnabled` | `false` | Notification prefs on profile |
| `splashScreenEnabled` | `false` | Branded intro animation on load |
| `instagramEnabled` | `false` | Instagram icon in footer |
| `youtubeEnabled` | `false` | YouTube icon in footer |
| `phase2UserFeaturesEnabled` | `true` | Dead — nothing reads this (remove candidate) |

---

## HOW IT FLOWS

```
controls.json
    ├── platforms.supported
    │       └── read by config.py → SUPPORTED_PLATFORMS
    │               └── used by FileOfferRepository to filter offers served via API
    │
    └── featureFlags
            └── read by feature_flags.py → FeatureFlags model
                    └── served at GET /api/v1/feature-flags
                            └── FE fetches on load → resolveFeatureCapabilities()
                                    └── components gate UI behind caps.*
```

**After any change to `controls.json`:**
```bash
cd cwo_backend
python3 scripts/build_data_bundle.py
```
This regenerates `cardwiseoffer/src/data/generated/featureFlags.json` so local dev
picks up the change without needing the backend API running.

---

## LINKED OPERATIONS (must change both files)

| Operation | `phases.py` | `controls.json` |
|-----------|------------|-----------------|
| Enable intl flights | `PARSE_INTERNATIONAL_OFFERS = True` + add `"FLIGHT_INTERNATIONAL"` to `ACTIVE_PHASE2_CATEGORIES` | `flightInternationalEnabled: true` |
| Enable coupon codes | `COUPON_EXTRACTION_ENABLED = True` (already true) | `couponCodeEnabled: true` |
| Add new OTA platform | Add to `ENABLED_SOURCES` | Add to `platforms.supported` |

---

## AdSense / Affiliate / Compliance UI

All deferred — no timeline. Flags will be added when needed:
- `adsenseEnabled` — AdSense units (do NOT enable until 4–6 weeks post-launch)
- `affiliateEnabled` — Affiliate link injection
- `complianceEnabled` — Compliance disclosures
