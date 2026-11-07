# Offer Card Field Spec

> Reference for the full cardsage → backend → frontend pipeline.
> Live visual spec: https://claude.ai/artifact/FrF6Yb5rzzKHRakoehB5qt

## Card design

Current OfferCard component (`cardwiseoffer/src/components/OfferCard.tsx`) is the canonical design — do not change the card UI.

The three-tier data display strategy:
- **Minimum**: bank badge + discount value + CTA
- **Standard** (current): + coupon + validity + channel
- **Maximum** (future): + instant/cashback badges + eligibility notes + confidence + source attribution

## Critical bugs

### B1: CTA disabled for all offers
`offerMapper.ts:55` — `platformUrl: raw.booking_url ?? null`
`booking_url` is `null` for every offer in the static snapshot.
**Fix**: fall back to `platformHomeUrl(platform_id)` when `booking_url` is null.

### B2: Guest gate bypass
When filters produce ≤ 3 results, `hiddenCount = max(0, totalCount - 3) = 0` → gate never shown.

## Pipeline (cardsage → backend → frontend)

```
cardsage output JSON
        ↓  [BROKEN — not connected yet]
  data/source/offers.csv  (hand-curated, manual)
        ↓  scripts/build_offer_snapshot.py
  data/generated/offers.snapshot.json
        ↓  app/repositories/file_offer_repository.py
  /api/v1/offers  (PublicOffer schema)
        ↓  cardwiseoffer/src/domain/offerMapper.ts
  OfferViewModel  (frontend)
```

## Field mapping: cardsage → backend

| cardsage field | backend field | Status |
|---|---|---|
| `offer_id` | `offer_id` | ✓ |
| `valid_to` | `expiry_date` | ✓ aliased in ALIASES dict |
| `last_verified_at` | `updated_at` | ✓ model_validator fallback |
| `validation_status` | `evidence_status` | ~ must map: VALID→VERIFIED, WARNING/NEEDS_REVIEW→PARTIAL, INVALID→UNVERIFIED |
| — | `publish_status` | ✗ must derive: VERIFIED+confidence≥0.70→READY, else DRAFT |
| `confidence` | `priority_score` | ~ `int(confidence × 100)` |
| `booking_url` | `booking_url` | ✗ field does not exist in cardsage yet — add to cardsage model |
| `instant_discount` | — | ✗ cardsage has it; add to app/domain/models.py |
| `cashback_value` | — | ✗ cardsage has it; add to app/domain/models.py |
| `trip_type` | — | ✗ cardsage has it; add to app/domain/models.py |
| `card_network` | — | ✗ cardsage has it; add to app/domain/models.py |
| `is_upcoming` | — | ✗ cardsage has it; add to app/domain/models.py |
| `offer_source` | — | ✗ cardsage has it; add to app/domain/models.py |

## REQUIRED fields (ingestion will reject records missing these)

From `scripts/build_offer_snapshot.py` REQUIRED set:
`offer_id`, `platform_id`, `platform_name`, `offer_title`, `payment_method`, `category`,
`booking_channel`, `discount_type`, `discount_value`, `valid_from`, `expiry_date`,
`source_url`, `evidence_status`, `publish_status`

cardsage is missing: `evidence_status` and `publish_status` — must be derived in conversion script.

## Blocking work to connect the pipeline

1. Add `booking_url: str | None` to `cardsage/core/models.py` — the ONLY new field needed in cardsage
2. Build conversion script (`scripts/cardsage_to_snapshot.py`) that reads cardsage output JSON and derives `evidence_status`, `publish_status`, `priority_score`
3. Fix `cardwiseoffer/src/domain/offerMapper.ts:55` CTA fallback to `platformHomeUrl(platform_id)`

## Phase 2 enrichment (add to app/domain/models.py + app/schemas/offers.py)

Fields already in cardsage that need to flow through the backend:

```python
# Add to app/domain/models.py Offer class
instant_discount: bool = False
cashback_value: Decimal | None = None
applicable_airlines: list[str] = []
trip_type: str | None = None        # ONE_WAY / ROUNDTRIP / BOTH
card_network: str | None = None     # VISA / MASTERCARD / RUPAY / AMEX
is_upcoming: bool = False
offer_source: str | None = None     # BANK_CARD / AIRLINE_PROMO / PLATFORM_PROMO
```
