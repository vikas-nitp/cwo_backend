from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    model_validator,
)

PlatformId = Literal["MAKEMYTRIP", "CLEARTRIP"]
PaymentMethod = Literal["CREDIT", "DEBIT", "NO_CARD"]
Category = Literal["FLIGHT_DOMESTIC"]
BookingChannel = Literal["WEB", "APP", "WEB_AND_APP"]
DiscountType = Literal["PERCENT", "FLAT"]
EvidenceStatus = Literal["VERIFIED", "PARTIAL", "UNVERIFIED"]
PublishStatus = Literal["READY", "DRAFT", "HIDDEN"]


class Offer(BaseModel):
    model_config = ConfigDict(frozen=True)

    offer_id: str = Field(min_length=1)
    platform_id: PlatformId
    platform_name: str = Field(min_length=1)
    offer_title: str = Field(min_length=1)
    bank_id: str | None = None
    bank_name: str | None = None
    card_name: str | None = None
    payment_method: PaymentMethod
    category: Category
    booking_channel: BookingChannel
    discount_type: DiscountType
    discount_value: Decimal = Field(ge=0)
    max_discount: Decimal | None = Field(default=None, ge=0)
    min_transaction: Decimal | None = Field(default=None, ge=0)
    coupon_code: str | None = None
    valid_from: date
    valid_to: date
    usage_limit: str | None = None
    new_user_only: bool = False
    login_required: bool = False
    eligibility_notes: list[str] = Field(default_factory=list)
    terms_url: AnyHttpUrl | None = None
    source_url: AnyHttpUrl
    booking_url: AnyHttpUrl | None = None
    source_type: str | None = None
    evidence_status: EvidenceStatus
    last_verified_at: date | None = None
    priority_score: int = 0
    is_active: bool = True
    publish_status: PublishStatus
    extra: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_dates(self) -> "Offer":
        if self.valid_from > self.valid_to:
            raise ValueError("valid_from must be on or before valid_to")
        if self.payment_method == "NO_CARD" and self.bank_id:
            raise ValueError("NO_CARD offers cannot specify bank_id")
        return self

    @field_serializer("discount_value")
    def serialize_required_decimal(self, value: Decimal) -> float:
        return float(value)

    @field_serializer("max_discount", "min_transaction")
    def serialize_optional_decimal(self, value: Decimal | None) -> float | None:
        return None if value is None else float(value)


class BankMetadata(BaseModel):
    id: str
    name: str


class PlatformMetadata(BaseModel):
    id: PlatformId
    name: str


class AirportMetadata(BaseModel):
    code: str
    city: str
    name: str
    country: str
    is_domestic_default: bool


class OfferMetadata(BaseModel):
    data_version: str
    banks: list[BankMetadata]
    platforms: list[PlatformMetadata]
    payment_methods: list[PaymentMethod]
    categories: list[Category]
    booking_channels: list[BookingChannel]
    airports: list[AirportMetadata] = Field(default_factory=list)


class DataManifest(BaseModel):
    schema_version: str = "1.1"
    data_version: str
    generated_at: datetime
    source_row_count: int
    source_count: int = 1
    accepted_row_count: int
    rejected_row_count: int
    supported_platforms: list[PlatformId]


class FacetSnapshot(BaseModel):
    data_version: str
    active_on: date
    platforms: dict[str, dict[str, Any]]
    banks: dict[str, dict[str, Any]]
