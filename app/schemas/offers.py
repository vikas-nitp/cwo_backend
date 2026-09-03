from datetime import date
from decimal import Decimal

from pydantic import AnyHttpUrl, BaseModel, field_serializer

from app.domain.models import (
    BookingChannel,
    Category,
    DiscountType,
    PaymentMethod,
    PlatformId,
)
from app.schemas.common import Pagination


class PublicOffer(BaseModel):
    offer_id: str
    platform_id: PlatformId
    platform_name: str
    offer_title: str
    bank_id: str | None
    bank_name: str | None
    card_name: str | None
    payment_method: PaymentMethod
    category: Category
    booking_channel: BookingChannel
    discount_type: DiscountType
    discount_value: Decimal
    max_discount: Decimal | None
    min_transaction: Decimal | None
    coupon_code: str | None
    valid_from: date
    expiry_date: date
    new_user_only: bool
    login_required: bool
    usage_limit: str | None
    eligibility_notes: list[str]
    terms_url: AnyHttpUrl | None

    @field_serializer("discount_value", "max_discount", "min_transaction")
    def serialize_decimal(self, value: Decimal | None) -> float | None:
        return None if value is None else float(value)


class OffersResponse(BaseModel):
    data_version: str
    offers: list[PublicOffer]
    pagination: Pagination
    facets: None = None
