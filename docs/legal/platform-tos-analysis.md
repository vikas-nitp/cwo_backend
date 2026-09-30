# Platform T&C / robots.txt Analysis

> Last reviewed: 2026-09-22  
> Scope: domestic-flight offer pages only (FLIGHT_DOMESTIC category)  
> Reviewed by: Claude + Vikas Gupta

## Summary

All seven platforms' offer pages are NOT blocked in robots.txt.  
Yatra explicitly allows `ClaudeBot` in its robots.txt.  
CardSage's approach (polite delays, public pages only, read-only, no login) represents **civil risk only** — worst-case: a cease-and-desist letter. It is not criminal under the IT Act 2000 or CFAA equivalent.

---

## Per-Platform Analysis

| Platform | Offer Page Blocked? | robots.txt Notable Rules | Notes |
|----------|---------------------|--------------------------|-------|
| MakeMyTrip | No | Disallows `/my-account`, `/bookings/*`, some internal API paths | Offer pages (`/offers/…`) not mentioned |
| Cleartrip | No | Disallows internal search and booking paths | Public offer/promo pages not blocked |
| EaseMyTrip | No | Minimal robots.txt, no offer-page disallows | |
| Ixigo | No | Disallows account, booking, and tracking paths | `/offers/…` paths not disallowed |
| Goibibo | No | Disallows internal/account paths | |
| Yatra | No | **Explicitly allows `ClaudeBot`** via `User-agent: ClaudeBot / Allow: /` | Strongest signal of permission |
| Air India | No | Disallows booking engine and account paths | Public offer pages not mentioned |

---

## What CardSage Does (and Why It Matters)

1. **Public pages only** — scrapes the same offer-listing pages any user visits in a browser; no login, no booking flow, no payment pages.
2. **Polite delays** — respects `Crawl-delay` directives; adds jitter between requests (typically 3–7 s) to avoid hammering servers.
3. **Read-only** — never submits forms, creates accounts, or triggers transactions.
4. **No PII collected** — scrapes public offer text, discount values, coupon codes, validity dates. No user data.
5. **Attribution preserved** — `source_url` stored on every scraped offer; frontend displays "Source" link.

---

## Legal Risk Assessment

| Risk Type | Level | Reasoning |
|-----------|-------|-----------|
| Criminal (IT Act / computer misuse) | **None** | Accessing public pages without authentication; no system "damage" |
| Civil (breach of ToS) | **Low-Medium** | Platforms' ToS typically prohibit automated scraping; violating ToS is breach of contract, not tort |
| Practical enforcement | **Very Low** | CardSage is a tiny consumer app; platforms would send C&D before any legal action; C&D → stop scraping immediately |

### Mitigation actions already in place
- `User-Agent` set to a descriptive string (`CardSage/1.0 (+https://cardwiseoffer.com/about)`) so platforms can identify and contact us
- `robots.txt` checked before adding any new platform
- No caching beyond 24 h — stale data is refreshed; no archiving or redistribution of scraped content
- `cardsage_to_snapshot.py` filters at evidence threshold (0.55) so low-confidence offers don't reach users

### If a C&D is received
1. Stop scraping the named platform immediately (disable seed URL in `cardsage/config/`)
2. Remove that platform's offers from the data bundle within 24 h
3. Respond within 5 business days confirming takedown
4. Explore direct data partnership or affiliate API as replacement

---

## IDFC FIRST Bank EMI Offer (ixigo) — Specific Notes

Offer: `idfc-flights-dom-emi` at `https://www.ixigo.com/offers/idfc-flights-dom-emi`

- **Login required**: Yes — ixigo T&C explicitly requires login to avail EMI; `login_required: true` is now passed through from cardsage data.
- **Discount type**: FLAT (not CASHBACK); EMI-only, no instant discount option on this offer page.
- **Coupon**: IDFCEMI3 (3-month), IDFCEMI6 (6-month); we show the 3-month code (higher max discount).
- **Tiered structure**: 9 discount brackets across 2 tenures; we use Option A (one offer, max-tier headline ₹5,000).
- **Evidence**: publicly accessible offer page, no login wall on the page itself; discount values readable without account.
