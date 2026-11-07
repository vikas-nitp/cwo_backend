# CardwiseOffer — Launch Strategy

> MVP → Traffic → Revenue  
> Zero-to-launch strategy · 4–6 week traffic read · Phase-gated feature flags · Revenue + social roadmap

---

## MVP — What ships on Day 1

Goal: one user action — route + date → ranked card list — deployed publicly with no auth wall.

| # | Item | Priority |
|---|------|----------|
| 1 | Search: route + date → ranked offers (no login, no friction) | Must |
| 2 | Bank + Platform filters (HDFC, ICICI… × MMT, Cleartrip, Ixigo) | Must |
| 3 | Offer card: discount, validity, CTA "Book on MakeMyTrip →" link | Must |
| 3a | "Verify offer on [platform] before booking" disclaimer — always visible below CTA | Must |
| 4 | Mobile responsive | Must |
| 5 | SEO meta tags on every page (title, description, og:image) | Must |
| 6 | Google Analytics 4 + Search Console (day-1 instrumentation) | Must |
| 7 | Daily data refresh via GitHub Actions cron | Must |
| 8 | Savings estimate when booking amount given (optional field) | Nice |
| — | Auth / user accounts / saved cards | Later |
| — | Subscriptions / email alerts | Later |

---

## Feature Flags — Phase-gated rollout

### Phase 1 — Launch (Day 1)
```
ON:  publicAllOffersEnabled, bookingAmountComparisonEnabled, analyticsEnabled
OFF: couponCodeEnabled, authEnabled, subscriptionsEnabled
```

### Phase 2 — Social proof + About pages (Week 2–3 · if >200 DAU)
```
FLIP ON: couponCodeEnabled, visitorCountEnabled, howItWorksEnabled,
         aboutEnabled, contactEnabled, privacyPolicyEnabled, termsOfServiceEnabled
```

### Phase 3 — User accounts + saved cards (Week 4–6 · if >500 DAU)
```
FLIP ON: authEnabled, userCardsEnabled, phase2UserFeaturesEnabled
HOLD:    notificationsEnabled, subscriptionsEnabled
```

### Phase 4 — Notifications + subscriptions (Month 2–3 · if retention >20%)
```
FLIP ON: notificationsEnabled, subscriptionsEnabled
```

---

## Weeks 1–6 — Traffic Analysis Window

First six weeks is a **listening exercise**. Ship, instrument, watch. Build nothing new until data tells you what to build.

| Week | Action | Goal |
|------|--------|------|
| 1 | Deploy (Vercel + Railway), submit sitemap to GSC + Bing, verify GA4 events (search, filter_apply, offer_click), share in 3 PF communities | Live & indexed |
| 2 | Check Search Console queries, GA4 top bank/platform combos, mobile bounce rate, "no results" rate | Identify top 3 queries |
| 3 | Write 2–3 SEO posts ("Best HDFC card for MakeMyTrip"), add JSON-LD structured data, enable Phase 2 flags if 200+ DAU, first Instagram/X data-drop | 500+ organic sessions |
| 4 | Register VCommission/Admitad, add affiliate tracking to CTA links, measure offer-click → platform rate. **Hold AdSense application** — wait until real indexed content is live (4–6 weeks minimum) to avoid rejection. | First affiliate clicks tracked |
| 5 | If repeat visitors >20%: enable auth. If mostly one-time: hold, focus SEO. Survey 5 users. Add "alert me" email capture. | Decide auth yes/no |
| 6 | Full traffic + revenue audit. Decide: MVP proved? → invest in card affiliate outreach. Set next 3-month OKRs. | Informed Q4 roadmap |

---

## Top 5 Revenue Streams

**Priority order** — activate in sequence, not all at once.

### 1. Booking affiliates — Activate Week 4
Every "Book on MakeMyTrip →" click carries affiliate tag. High-intent audience = strong conversion.  
**Platform:** VCommission / Admitad India · **Est:** ₹150–400 per completed booking.

### 2. Card application affiliates — Month 2
"Don't have this card? Apply now →" linking to HDFC, ICICI, Axis apply pages. Highest CPA in Indian affiliate programs.  
**Est:** ₹800–2,500 per approved card application.

### 3. Google AdSense — Activate Week 5–6 (after real indexed content)
Lowest effort. Turns on once traffic is real and pages are indexed. Applying too early risks rejection.  
**Rule:** Do NOT apply until the site has 4–6 weeks of real indexed content and some organic sessions.  
**Est:** ₹40–120 CPM on finance audience.

### 4. Sponsored bank placement — Month 4+
Bank pays for featured offer card during a campaign. Labelled "Promoted". Direct outreach after 1K+ DAU.  
**Est:** ₹15,000–50,000/month per sponsor.

### 5. Offer alerts subscription — Month 3+ (post-auth)
"Alert me when HDFC gets a new MakeMyTrip deal" — freemium with paid WhatsApp/push tier.  
**Est:** 1–3% paid conversion on subscriber base.

> **Flywheel:** SEO organic → offer clicks → affiliate commission → reinvest in content → more SEO.  
> Card application affiliate is highest-yield. Prioritise any feature that gets a user from "which card?" to "I don't have that card".

---

## Social Media Strategy

Rule: **70% effort on SEO content** (evergreen, sends traffic for 12 months), **30% on social** (3-day spike).

| Channel | Content type | Cadence |
|---------|-------------|---------|
| Instagram | "Card hack of the month" carousel + Reels of the site in action | 4×/month |
| X / Twitter | Monthly data-drop threads ("October: ICICI leads MMT, BOB is the dark horse on Cleartrip") | 6–8×/month |
| Reddit | Answer questions in r/IndiaInvestments, r/creditCards. Link only when genuinely helpful. | As needed |
| YouTube Shorts | "₹2,000 saved in 60 seconds" — screen recording of a search surfacing a great deal | 2×/month from Month 2 |
| WhatsApp | Monthly "Best deals this month" shareable card — opt-in list via site email capture | 1×/month |
