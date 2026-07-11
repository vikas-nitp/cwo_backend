from datetime import date
from typing import Protocol

from app.domain.models import DataManifest, Offer, OfferMetadata


class OfferRepository(Protocol):
    def list_offers(
        self,
        *,
        active_on: date,
        bank_ids: list[str] | None = None,
        platform_ids: list[str] | None = None,
        payment_method: str | None = None,
        category: str | None = None,
        booking_channel: str | None = None,
    ) -> list[Offer]: ...
    def get_metadata(self) -> OfferMetadata: ...
    def get_manifest(self) -> DataManifest: ...
