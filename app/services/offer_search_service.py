from datetime import date, timedelta
from app.core.config import BOOKING_WINDOW_DAYS
from app.domain.calculations import estimate_savings
from app.domain.ranking import rank_offers
from app.repositories.base import OfferRepository
from app.schemas.search import (
    SearchDateBenefit,
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
            categories=[request.category],
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
                SearchOffer.model_validate(
                    {
                        **offer.model_dump(),
                        "display_kind": item.display_kind,
                        "display_rank": item.display_rank,
                        "savings_delta": item.savings_delta,
                        "estimated_savings": item.estimate.estimated_savings,
                        "estimated_final_amount": item.estimate.estimated_final_amount,
                        "savings_label": item.estimate.savings_label,
                        "amount_eligible": item.estimate.eligible
                        if request.booking_amount is not None
                        else None,
                        "comparison_text": (
                            f"Save ₹{item.savings_delta:,.0f} more"
                            if request.booking_amount is not None
                            and item.savings_delta is not None
                            and item.savings_delta > 0
                            else None
                        ),
                        "booking_url": offer.booking_url
                        or BOOKING_URLS.get(offer.platform_id),
                    }
                )
            )
        date_strip = []
        for offset in range(BOOKING_WINDOW_DAYS + 1):
            strip_date = today + timedelta(days=offset)
            strip_offers = self.repository.list_offers(
                active_on=strip_date,
                platform_ids=list(request.platforms) or None,
                categories=[request.category],
            )
            amounts = [
                offer.max_discount
                if offer.max_discount is not None
                else offer.discount_value
                for offer in strip_offers
                if offer.discount_type == "FLAT" or offer.max_discount is not None
            ]
            percentages = [
                offer.discount_value
                for offer in strip_offers
                if offer.discount_type == "PERCENT" and offer.max_discount is None
            ]
            if amounts:
                benefit_type, benefit_value = "AMOUNT", max(amounts)
                display_text = f"Up to ₹{benefit_value:,.0f}"
            elif percentages:
                benefit_type, benefit_value = "PERCENTAGE", max(percentages)
                display_text = f"Up to {benefit_value:,.0f}% off"
            else:
                benefit_type, benefit_value, display_text = None, None, "No offers"
            date_strip.append(
                SearchDateBenefit(
                    date=strip_date,
                    benefit_type=benefit_type,
                    benefit_value=benefit_value,
                    display_text=display_text,
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
            date_strip=date_strip,
        )
