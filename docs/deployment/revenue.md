# Revenue Strategy — CardWiseOffer

> CardWiseOffer's advantage: users arrive with **dual high intent** — they're about to book a flight AND deciding which card to use. This is the ideal position for both booking affiliates and card application leads.

---

## Critical: Fix B1 Bug First (booking_url = null)

**`cardwiseoffer/src/domain/offerMapper.ts:55`** — `platformUrl: raw.booking_url ?? null`

Every CTA is currently disabled. Fixing this one line to fall back to `platformHomeUrl(platform_id)` unlocks all affiliate revenue immediately. This is the highest-ROI engineering task — not a UX fix, a revenue gate.

---

## Revenue Streams (ranked by effort vs. return)

### 1. Booking Platform Affiliates — DO FIRST

**How**: Replace CTA href with tracked affiliate URL from VCommission / Admitad India.
`"Continue to Cleartrip ↗"` → affiliate link with your publisher ID + click_id param.

| Platform | Affiliate Program | Est. per domestic booking |
|---|---|---|
| Cleartrip | VCommission / Admitad India | ₹100–400 |
| MakeMyTrip | VCommission / DAN | ₹150–500 |
| EaseMyTrip | VCommission | ₹100–300 |
| Ixigo | Admitad India | ₹50–200 |

**Where to sign up**: vcommission.com, admitad.com/en/india — free publisher accounts.

**Revenue estimate at 1,000 daily visitors**:
- 10% click through → 100 visits to platform
- 20% of those complete a booking → 20 bookings/day
- Avg ₹200/booking → **₹4,000/day = ₹1.2L/month**

**Effort**: Very Low — one-time URL wrapper in `offerMapper.ts` after B1 fix.

---

### 2. Email List — Build Now, Monetize Later

**Why build before you have revenue**: An email list is a durable asset that compounds. A 10,000-subscriber finance+travel list in India is worth ₹50,000–2,00,000/month in sponsor deals.

**Capture**: Add an email capture on the gate wall (the sign-in prompt for guests) and in the offer results — _"Get notified when new offers are added for your banks"_.

**Monetize**:
- Weekly "Best card offers this week" digest — sponsorship slots (₹5–20 per email to targeted audience)
- Bank/fintech sponsors pay ₹3,000–15,000 per send once list is 5,000+
- Use Resend (free up to 100/day, ₹0) or Mailchimp free tier

**Effort**: Low — email form + weekly digest template. No database needed (store email + preference in a simple append-only CSV/JSON initially).

---

### 3. Display Ads — Better Alternatives to AdSense

AdSense is the worst option for a finance audience. Better networks:

| Network | Why better | Est. CPM India |
|---|---|---|
| **Media.net** (Yahoo/Bing) | Finance advertisers pay more on Bing | ₹80–250 |
| **Taboola** | Native ads blend with content | ₹50–200 |
| **Carbon Ads** | Dev/tech audience, very targeted | ₹300–800 |
| **Direct bank ads** | Banks will pay ₹500–5,000 CPM for flight intent audience | ₹500–5,000 |
| Google AdSense | Generic, lowest for finance | ₹30–150 |

**Recommendation**: Start with Media.net alongside AdSense (they are compatible). Approach banks directly once you hit 10,000+ monthly unique visitors.

**Apply sequence**: AdSense (easy approval) → Media.net (higher CPM) → Direct bank deals (best CPM).

---

### 4. Credit Card Application Affiliates — Highest Per-Conversion Value

**How**: Add a secondary CTA on each offer card — _"Don't have this card? Apply in 5 mins →"_ — linking to the bank's card application page with your affiliate tracking.

| Bank | Program route | Est. per approved application |
|---|---|---|
| HDFC Credit Cards | BankBazaar / DAN affiliate | ₹500–1,500 |
| SBI Card | Direct / VCommission | ₹300–800 |
| Axis Bank | Admitad / direct | ₹500–1,500 |
| ICICI Credit | Admitad / BankBazaar | ₹500–1,200 |
| American Express | Direct affiliate program | ₹1,000–2,500 |

**Fastest route**: Partner with BankBazaar or Paisabazaar as a sub-affiliate — they handle tracking, bank relationships, and payout. You earn ~50–70% of their commission. Direct bank BD takes 3–6 months.

**Revenue estimate**: Even 1% of 1,000 daily visitors applying for a card = 10 applications/day, 40% approval rate = 4 approvals × ₹700 avg = ₹2,800/day = **₹84,000/month**.

**Effort**: Medium — card apply CTA in `OfferCard`, tracking params, affiliate account setup.

---

### 5. Premium Subscription — Phase 2+

**Freemium model**:

| Tier | Price | Features |
|---|---|---|
| Free | ₹0 | Top 3 offers per platform, basic search |
| **Pro** | **₹99/month** | All offers, email price alerts, weekly digest, offer history |
| Power | ₹299/month | Real-time SMS/WhatsApp alerts, multi-route tracking, saved card profiles |

**Why this works**: Users who research card offers before every flight are frequent flyers — i.e., price-sensitive, high-frequency bookers. They will pay ₹99 to save ₹1,500+ per booking.

**Needs**: Database (Phase 3), payment gateway (Razorpay — easy India setup, 2% fee).

**Revenue estimate at 500 paid users**: 400 × ₹99 + 100 × ₹299 = **₹69,500/month recurring**.

---

### 6. Sponsored Offer Positioning

**How**: Banks or platforms pay to have their offer shown first / highlighted with a "Featured" badge.

**Pricing**: ₹5,000–50,000/month depending on traffic.

**Must disclose**: "Sponsored" label required. User trust is the core asset — never obscure it.

**Effort**: Low once traffic is there — just a backend `priority_boost` flag + frontend "Featured" pill.
Consider only after 50,000+ monthly users.

---

### 7. B2B / API Access

**Corporate travel**: Companies with ≥20 employees use corporate cards for flights. A "CardWise for Teams" tier (₹2,000–20,000/month) helps finance teams set card policy.

**Widget licensing**: Travel blogs embed a "Best card for Delhi→Mumbai" widget. Charge ₹500–5,000/month per publisher.

**Effort**: High — separate product/go-to-market. Phase 4.

---

## Revenue Roadmap

```
Day 1 of launch
  └── Fix B1 bug (offerMapper.ts:55) ← HIGHEST ROI
  └── Sign up: VCommission + Admitad India publisher accounts
  └── Replace CTA with affiliate deep links

Month 1
  └── Add email capture (offer alerts opt-in)
  └── Apply: Google AdSense + Media.net
  └── Weekly offer digest email (Resend)

Month 2–3
  └── BankBazaar/Paisabazaar sub-affiliate for card apply CTA
  └── Approach Cleartrip/MMT directly for higher affiliate rates
  └── A/B test card-apply CTA placement

Month 4–6
  └── Approach banks directly for display ad deals (₹500+ CPM)
  └── Launch Pro subscription if email list > 2,000

Month 6+
  └── Premium subscription with Razorpay
  └── Sponsored positioning (traffic-gated)
  └── Corporate / API tier
```

---

## Realistic Revenue Projections

Assumptions: 1,000 daily active users, Indian domestic market.

| Stream | Month 1 | Month 3 | Month 6 |
|---|---|---|---|
| Booking affiliates | ₹40,000 | ₹80,000 | ₹1,50,000 |
| Card apply affiliates | — | ₹30,000 | ₹80,000 |
| Display ads (AdSense+Media.net) | ₹5,000 | ₹12,000 | ₹20,000 |
| Email sponsorships | — | ₹5,000 | ₹20,000 |
| Premium subscriptions | — | — | ₹50,000 |
| **Total** | **~₹45,000** | **~₹1,27,000** | **~₹3,20,000** |

> These assume organic traffic growth. SEO for "best credit card for Cleartrip" / "SBI card flight discount" type queries will compound over time.

---

## SEO Notes (free traffic = free revenue)

Highest-value organic queries to target:
- `"best credit card for cleartrip flights"`
- `"hdfc credit card flight discount 2026"`
- `"sbi credit card flight offer india"`
- `"which card to use for makemytrip"`

Each offer page should be indexable with a static URL (e.g., `/offers/cleartrip/sbi-credit`).
Currently the SPA renders everything client-side — add SSR or prerender for these pages (Vercel's prerender works with Vite).
