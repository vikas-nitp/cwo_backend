from datetime import date
from decimal import Decimal
import re

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)

from app.domain.models import (
    BookingChannel,
    Category,
    DiscountType,
    EvidenceStatus,
    PaymentMethod,
    PlatformId,
    PublishStatus,
)


class SearchRequest(BaseModel):
    from_airport: str = Field(alias="from")
    to_airport: str = Field(alias="to")
    date: date
    banks: list[str] = Field(default_factory=list, max_length=2)
    platforms: list[PlatformId] = Field(default_factory=list)
    category: Category = "FLIGHT_DOMESTIC"
    booking_amount: Decimal | None = Field(default=None, gt=0)

    @field_validator("from_airport", "to_airport", mode="before")
    @classmethod
    def airport_code(cls, value: str) -> str:
        value = str(value).strip().upper()
        if not re.fullmatch(r"[A-Z]{3}", value):
            raise ValueError("Airport code must be three uppercase letters")
        return value

    @field_validator("banks")
    @classmethod
    def normalize_banks(cls, value: list[str]) -> list[str]:
        normalized = list(
            dict.fromkeys(item.strip().upper() for item in value if item.strip())
        )
        if len(normalized) > 2:
            raise ValueError("Maximum two banks are allowed")
        return normalized

    @model_validator(mode="after")
    def different_airports(self) -> "SearchRequest":
        if self.from_airport == self.to_airport:
            raise ValueError("Origin and destination must differ")
        return self


class SearchSummary(BaseModel):
    from_airport: str = Field(alias="from")
    to_airport: str = Field(alias="to")
    date: date
    booking_amount: Decimal | None

    model_config = {"populate_by_name": True}

    @field_serializer("booking_amount")
    def serialize_amount(self, value: Decimal | None) -> float | None:
        return None if value is None else float(value)


class SearchOffer(BaseModel):
    offer_id: str
    display_kind: str
    display_rank: int
    savings_delta: Decimal | None
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
    estimated_savings: Decimal | None
    estimated_final_amount: Decimal | None
    savings_label: str
    coupon_code: str | None
    valid_from: date
    valid_to: date
    eligibility_notes: list[str]
    terms_url: AnyHttpUrl | None
    source_url: AnyHttpUrl
    booking_url: AnyHttpUrl | None
    evidence_status: EvidenceStatus
    last_verified_at: date | None
    priority_score: int
    is_active: bool
    publish_status: PublishStatus

    @field_serializer(
        "savings_delta",
        "discount_value",
        "max_discount",
        "min_transaction",
        "estimated_savings",
        "estimated_final_amount",
    )
    def serialize_amount(self, value: Decimal | None) -> float | None:
        return None if value is None else float(value)


class SearchResponse(BaseModel):
    data_version: str
    summary: SearchSummary
    offers: list[SearchOffer]
