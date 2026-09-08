from datetime import date, timedelta
from app.core.dates import today_ist
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
        today = today or today_ist()
        metadata = self.repository.get_metadata()
        known_banks = {bank.id for bank in metadata.banks}
        unknown_banks = set(request.banks) - known_banks
        if unknown_banks:
            raise ValueError(f"Unknown bank ID: {', '.join(sorted(unknown_banks))}")
        if request.date < today:
            raise SearchDateError("Travel date cannot be in the past.")
        if (
            metadata.availability_start is None
            or metadata.availability_end is None
            or not metadata.availability_start
            <= request.date
            <= metadata.availability_end
        ):
            raise SearchDateError("Travel date is outside offer availability.")
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
        if not offers:
            raise SearchDateError("No eligible offers are available on this date.")
        date_strip = []
        strip_end = min(request.date + timedelta(days=6), metadata.availability_end)
        for offset in range((strip_end - request.date).days + 1):
            strip_date = request.date + timedelta(days=offset)
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
                    offer_count=len(strip_offers),
                    available=bool(strip_offers),
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
