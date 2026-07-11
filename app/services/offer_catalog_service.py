from datetime import date

from app.repositories.base import OfferRepository
from app.schemas.common import Pagination
from app.schemas.offers import OffersResponse


class OfferCatalogService:
    def __init__(self, repository: OfferRepository):
        self.repository = repository

    def list(
        self,
        *,
        active_on: date,
        bank: str | None,
        platform: str | None,
        payment_method: str | None,
        booking_channel: str | None,
        category: str | None,
        page: int,
        limit: int,
    ) -> OffersResponse:
        offers = self.repository.list_offers(
            active_on=active_on,
            bank_ids=[bank] if bank else None,
            platform_ids=[platform] if platform else None,
            payment_method=payment_method,
            booking_channel=booking_channel,
            category=category,
        )
        offers.sort(
            key=lambda offer: (offer.priority_score, offer.valid_to), reverse=True
        )
        total = len(offers)
        start = (page - 1) * limit
        manifest = self.repository.get_manifest()
        return OffersResponse(
            data_version=manifest.data_version,
            offers=offers[start : start + limit],
            pagination=Pagination(
                page=page,
                limit=limit,
                total=total,
                total_pages=(total + limit - 1) // limit,
            ),
        )
