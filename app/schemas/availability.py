from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, field_serializer, model_validator


class AvailabilityDay(BaseModel):
    date: date
    offer_count: int
    benefit_type: str | None
    benefit_value: Decimal | None
    display_text: str
    available: bool

    @field_serializer("benefit_value")
    def serialize_value(self, value: Decimal | None) -> float | None:
        return None if value is None else float(value)


class AvailabilityResponse(BaseModel):
    data_version: str
    availability_start: date | None
    availability_end: date | None
    dataset_last_updated_at: date
    days: list[AvailabilityDay] = Field(default_factory=list)


class AvailabilityRange(BaseModel):
    from_date: date
    to_date: date

    @model_validator(mode="after")
    def bounded(self):
        if self.to_date < self.from_date:
            raise ValueError("to must be on or after from")
        if (self.to_date - self.from_date).days > 30:
            raise ValueError("availability range cannot exceed 31 days")
        return self
