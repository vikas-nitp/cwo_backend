from datetime import date, timedelta
from app.core.config import BOOKING_WINDOW_DAYS
from app.domain.calculations import estimate_savings
from app.domain.ranking import rank_offers
from app.repositories.base import OfferRepository
from app.schemas.search import SearchOffer, SearchRequest, SearchResponse, SearchSummary

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
                        "booking_url": offer.booking_url
                        or BOOKING_URLS.get(offer.platform_id),
                    }
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
        )
