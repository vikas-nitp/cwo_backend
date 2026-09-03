from datetime import date, timedelta
from decimal import Decimal
from typing import cast

from pydantic import AnyHttpUrl

from app.core.config import BOOKING_WINDOW_DAYS
from app.domain.calculations import estimate_savings
from app.domain.ranking import rank_offers
from app.repositories.base import OfferRepository
from app.schemas.search import (
    DateStripItem,
    SearchOffer,
    SearchRequest,
    SearchResponse,
    SearchSummary,
)

BOOKING_URLS = {
    "MAKEMYTRIP": "https://www.makemytrip.com/flights/",
    "CLEARTRIP": "https://www.cleartrip.com/flights",
}


class SearchDateError(ValueError):
    pass


class OfferSearchService:
    def __init__(self, repository: OfferRepository):
        self.repository = repository

    def _build_strip(self, start: date, category: str) -> list[DateStripItem]:
        strip = []
        for i in range(7):
            day = start + timedelta(days=i)
            day_offers = self.repository.list_offers(active_on=day, category=category)

            capped = []
            for o in day_offers:
                if o.discount_type == "FLAT" or o.max_discount is not None:
                    capped.append(o.max_discount if o.max_discount is not None else o.discount_value)

            uncapped_pct = [
                o.discount_value
                for o in day_offers
                if o.discount_type == "PERCENT" and o.max_discount is None
            ]

            if capped:
                display_text = f"Up to ₹{int(max(capped)):,}"
            elif uncapped_pct:
                display_text = f"Up to {int(max(uncapped_pct))}% off"
            else:
                display_text = "No offers"

            strip.append(DateStripItem(date=day.isoformat(), display_text=display_text))
        return strip

    def search(
        self, request: SearchRequest, today: date | None = None
    ) -> SearchResponse:
        today = today or date.today()
        if request.date < today or request.date > today + timedelta(
            days=BOOKING_WINDOW_DAYS
        ):
            raise SearchDateError(
                f"Travel date must be from today through the next {BOOKING_WINDOW_DAYS} days."
            )
        offers = self.repository.list_offers(
            active_on=request.date,
            platform_ids=list(request.platforms) or None,
            category=request.category,
        )
        ranked = rank_offers(
            [
                (offer, estimate_savings(offer, request.booking_amount))
                for offer in offers
            ],
            request.banks,
            request.date,
        )
        results = []
        for item in ranked:
            offer = item.offer
            results.append(
                SearchOffer(
                    offer_id=offer.offer_id,
                    display_kind=item.display_kind,
                    display_rank=item.display_rank,
                    savings_delta=item.savings_delta,
                    platform_id=offer.platform_id,
                    platform_name=offer.platform_name,
                    offer_title=offer.offer_title,
                    bank_id=offer.bank_id,
                    bank_name=offer.bank_name,
                    card_name=offer.card_name,
                    payment_method=offer.payment_method,
                    category=offer.category,
                    booking_channel=offer.booking_channel,
                    discount_type=offer.discount_type,
                    discount_value=offer.discount_value,
                    max_discount=offer.max_discount,
                    min_transaction=offer.min_transaction,
                    estimated_savings=item.estimate.estimated_savings,
                    estimated_final_amount=item.estimate.estimated_final_amount,
                    savings_label=item.estimate.savings_label,
                    coupon_code=offer.coupon_code,
                    valid_from=offer.valid_from,
                    expiry_date=offer.valid_to,
                    new_user_only=offer.new_user_only,
                    eligibility_notes=offer.eligibility_notes,
                    terms_url=offer.terms_url,
                    booking_url=cast(AnyHttpUrl, BOOKING_URLS.get(offer.platform_id)),
                )
            )
        return SearchResponse(
            data_version=self.repository.get_manifest().data_version,
            summary=SearchSummary.model_validate(
                {
                    "from": request.from_airport,
                    "to": request.to_airport,
                    "date": request.date,
                    "booking_amount": request.booking_amount,
                }
            ),
            offers=results,
            date_strip=self._build_strip(request.date, request.category),
        )
