# Harvest → Affiliate Transition Plan

## What this document is

A gate document. It defines the conditions under which Harvest transitions from scraping
promotional pages to receiving offer data via affiliate/partner APIs, and the steps to execute
that transition safely. **No code changes toward affiliation should land without this gate
passing.**

---

## Current state (Phase 1)

Harvest collects data by scraping publicly accessible offer pages from flight booking platforms
(MakeMyTrip, Cleartrip, Ixigo). This is legal, transparent, and consistent with the platforms'
own terms for informational use. No accounts, no logins, no rate-limit evasion.

All offers are displayed as-is with:
- Attribution links back to the original source page (`source_url`)
- "Verify offer before booking" disclaimer on every OfferCard
- Last-updated timestamp so users know data freshness

Revenue model in Phase 1: **none** (building trust, not monetising).

---

## Phase 2 gate — when affiliation becomes appropriate

**All five conditions must be true before any affiliate integration begins:**

| # | Condition | How to verify |
|---|-----------|--------------|
| 1 | **Catalogue depth**: ≥ 3 platforms, ≥ 50 publishable domestic offers in the nightly snapshot | `cardsage export --summary` shows `total_offers ≥ 50` and `sources ≥ 3` |
| 2 | **Data quality**: validation_status VALID or WARNING (not INVALID) for ≥ 90% of exported offers across 7 consecutive nightly runs | Inspect `exports/latest/summary.json` → `validation_summary` for 7 days |
| 3 | **User trust baseline**: site is live, privacy policy is complete (including Grievance Officer), and at least one cycle of user feedback has been reviewed | LAUNCH_CHECKLIST.md items 1–20 all checked |
| 4 | **Legal review**: affiliate T&Cs from the target platform have been read and recorded; any prohibited scraping clause does NOT apply retroactively | Written note from reviewer in `cardsage/docs/legal/` |
| 5 | **Written decision**: a human decision-log entry signed off by the project owner, dated, with the specific platform and affiliate programme named | `cardsage/docs/legal/AFFILIATE_DECISIONS.md` entry |

---

## What changes at the code level

When one platform transitions to affiliate:

1. **New data source type**: add `"AFFILIATE_API"` to `SourceType` in the ingestion model. The
   existing `OfferSurface.source_type` field already carries this value through the pipeline.

2. **Adapter**: create `cardsage/sources/<platform>/affiliate_adapter.py` that calls the
   platform's partner API and maps the response into `NormalizedOffer`. The existing scrape
   adapter stays in place for platforms not yet affiliated.

3. **Phase flag**: add `PHASE_2_ENABLED = True` only after the gate passes and the affiliate
   adapter is tested. Do not flip this flag as part of the adapter PR — it should be its own
   single-line change so it is easy to roll back.

4. **Source attribution**: affiliate offers use the booking URL as `source_url` rather than the
   promotional page. The `OfferCard` already renders `source_url` as "View original offer ↗".

5. **Booking URL**: affiliate offers should carry a properly tagged affiliate link in
   `booking_url` / `platform_url`. CTA behaviour on the frontend is unchanged.

6. **Disclosure**: if any affiliate link carries a commission, add a visible "We may earn a
   commission" note to the OfferCard footer. Do NOT bury this in the privacy policy only.

---

## What does NOT change

- Offers remain ranked by user benefit, not commission rate.
- Scraping adapters for non-affiliated platforms continue running on the nightly schedule.
- The "Verify offer before booking" disclaimer stays on every card regardless of source type.
- `MOBILE_APP_ENABLED = False` is unchanged (separate decision log required).

---

## Rollback

If an affiliate integration introduces data quality regressions:

1. Set the per-platform `enabled` flag in `cardsage/config/sources.py` to `False`.
2. Redeploy — the scrape adapter picks up immediately on the next nightly run.
3. Document the regression in `cardsage/docs/legal/AFFILIATE_DECISIONS.md`.

---

## Current status

**Gate: CLOSED** — Phase 1 conditions not yet fully met.

Next review date: when `LAUNCH_CHECKLIST.md` conditions 1–20 are all checked.
