# CardwiseOffer — Dark Pattern Self-Audit
**CCPA Dark Pattern Guidelines 2023 · Consumer Protection E-Commerce Rules 2026**
Last reviewed: Sep 20 2026

---

## Audit scope

This document is the annual self-audit required under Consumer Protection (E-Commerce) Amendment
Rules 2026 (effective Jan 1, 2027). It covers the 13 named dark patterns from the CCPA Guidelines
2023 and the additional pricing and search-neutrality requirements of the 2026 Rules.

---

## CCPA 13 Named Patterns — Status

| # | Pattern | Definition | Status | Evidence |
|---|---------|-----------|--------|----------|
| 1 | False Urgency | Fabricating scarcity or countdown timers | ✅ PASS | No countdown timers or seat-count fabrication in UI |
| 2 | Basket Sneaking | Silent addition of items or fees | ✅ PASS | No checkout flow; no pre-ticked add-ons |
| 3 | Confirm Shaming | Manipulative decline microcopy | ✅ PASS | All decline options use neutral language |
| 4 | Forced Action | Requiring unrelated actions to use service | ✅ PASS | Sign-in optional; full results shown to guests |
| 5 | Subscription Trap | Obscuring auto-renewal terms | ✅ PASS | No subscriptions offered |
| 6 | Interface Interference | Visual design de-emphasising opt-outs | ✅ PASS | Consent checkboxes are equal size and weight |
| 7 | Bait and Switch | Advertising one price, delivering another | ✅ PASS | Savings are estimates with explicit disclaimers |
| 8 | Disguised Ads | Ads styled identically to organic results | ✅ PASS | No paid placements; all results are algorithmic |
| 9 | Nagging | Repeated, intrusive permission requests | ✅ PASS | No push permission requests |
| 10 | Trick Questions | Confusingly worded opt-ins | ✅ PASS | Consent notice uses plain language |
| 11 | SaaS Billing | Obscure cancellation or downgrade flows | ✅ PASS | No billing or paid tiers |
| 12 | Rogue Malwares | Fake virus/error messages | ✅ PASS | Not applicable |
| 13 | Search Manipulation | Burying relevant results in favour of paid ones | ✅ PASS | Ranking = mathematical savings only; no commercial influence |

**Result: 13/13 patterns clear as of Sep 20 2026.**

---

## Consumer Protection E-Commerce Rules 2026 — Pre-compliance Checklist

### 1. 30-Day Prior Price Mandate

**Requirement:** Any displayed "discount" must reference the lowest price offered in the
30 preceding days as the prior-price baseline — not an inflated reference price.

**CardwiseOffer status:** Savings estimates are calculated against the platform's listed
base fare at the time of data collection, not a manipulated reference price. However:

- [ ] **Open action:** Before Jan 1, 2027, confirm that the savings baseline used in the
  `discount_value` / `max_discount` fields in offer data reflects actual prior pricing and
  not an artificially inflated reference. Document the methodology in
  `cardsage/docs/savings-methodology.md`.

### 2. Sponsored Listing Disclosure

**Requirement:** Offers in results that are paid placements must be unmistakably labeled
"Sponsored" and must not be ranked above more relevant unpaid offers.

**CardwiseOffer status:** ✅ No sponsored placements exist. All ranking is algorithmic
(best mathematical savings per bank). If any bank partnership introduces paid placement
in future, add a `is_sponsored: bool` field to `PublicOffer` and render a "Sponsored"
chip on the card.

**Binding rule:** Sponsored placement must NEVER change the mathematical savings ranking —
it may only add a label. Any commercial arrangement that moves a lower-savings offer above
a higher-savings offer constitutes search manipulation under Rule 13 of CCPA Guidelines.

### 3. No Bundled Services Without Explicit Opt-In

**Requirement:** Platforms may not silently include services (insurance, convenience fees,
charitable donations) without a separate, unchecked opt-in.

**CardwiseOffer status:** ✅ No bundled services. CardwiseOffer is an informational tool
only — no bookings, no fees, no add-ons. If any booking hand-off feature is introduced,
this must be reviewed before launch.

---

## Audit trail

| Date | Auditor | Scope | Result |
|------|---------|-------|--------|
| Sep 20 2026 | Internal (Claude-assisted) | All 13 CCPA patterns + E-Commerce Rules 2026 | 13/13 pass |

**Next review due:** Before any new feature launch that introduces booking capability,
paid placement, or commercial partnerships. Minimum annual review in any case.
