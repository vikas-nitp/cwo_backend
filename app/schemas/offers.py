from datetime import date
from decimal import Decimal

from app.domain.models import (
    BookingChannel,
    Category,
    DiscountType,
    PaymentMethod,
    PlatformId,
)
from app.schemas.common import Pagination
from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field


class PublicOffer(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    offer_id: str
    platform_id: PlatformId
    platform_name: str
    offer_title: str
    bank_id: str | None = None
    bank_name: str | None = None
    card_name: str | None = None
    supported_cards: list[str] = Field(default_factory=list)
    payment_method: PaymentMethod
    category: Category
    booking_channel: BookingChannel
    discount_type: DiscountType
    discount_value: Decimal
    max_discount: Decimal | None = None
    min_transaction: Decimal | None = None
    coupon_code: str | None = None
    valid_from: date
    expiry_date: date
    updated_at: date
    usage_limit: str | None = None
    new_user_only: bool
    eligibility_notes: list[str]
    terms_url: AnyHttpUrl | None = None
    booking_url: AnyHttpUrl | None = None


class FacetOption(BaseModel):
    id: str
    name: str
    count: int
    selected: bool
    disabled: bool


class CatalogueFacets(BaseModel):
    platforms: list[FacetOption]
    banks: list[FacetOption]
    payment_methods: list[FacetOption]
    booking_channels: list[FacetOption]


class OffersResponse(BaseModel):
    data_version: str
    offers: list[PublicOffer]
    pagination: Pagination
    facets: CatalogueFacets
