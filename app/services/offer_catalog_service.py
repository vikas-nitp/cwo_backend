from datetime import date

from app.repositories.base import OfferRepository
from app.schemas.common import Pagination
from app.schemas.offers import OffersResponse, PublicOffer


class OfferCatalogService:
    def __init__(self, repository: OfferRepository):
        self.repository = repository

    def list(
        self,
        *,
        active_on: date,
        banks: list[str] | None,
        platforms: list[str] | None,
        payment_method: str | None,
        booking_channel: str | None,
        category: str | None,
        page: int,
        limit: int,
    ) -> OffersResponse:
        offers = self.repository.list_offers(
            active_on=active_on,
            bank_ids=banks or None,
            platform_ids=platforms or None,
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
        public_offers = [
            PublicOffer(
                offer_id=o.offer_id,
                platform_id=o.platform_id,
                platform_name=o.platform_name,
                offer_title=o.offer_title,
                bank_id=o.bank_id,
                bank_name=o.bank_name,
                card_name=o.card_name,
                payment_method=o.payment_method,
                category=o.category,
                booking_channel=o.booking_channel,
                discount_type=o.discount_type,
                discount_value=o.discount_value,
                max_discount=o.max_discount,
                min_transaction=o.min_transaction,
                coupon_code=o.coupon_code,
                valid_from=o.valid_from,
                expiry_date=o.valid_to,
                new_user_only=o.new_user_only,
                login_required=o.login_required,
                usage_limit=o.usage_limit,
                eligibility_notes=o.eligibility_notes,
                terms_url=o.terms_url,
            )
            for o in offers[start : start + limit]
        ]
        return OffersResponse(
            data_version=manifest.data_version,
            offers=public_offers,
            pagination=Pagination(
                page=page,
                limit=limit,
                total=total,
                total_pages=(total + limit - 1) // limit,
            ),
        )
