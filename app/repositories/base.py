from datetime import date
from typing import Protocol

from app.domain.models import DataManifest, FacetSnapshot, Offer, OfferMetadata


class OfferRepository(Protocol):
    def list_offers(
        self,
        *,
        active_on: date,
        bank_ids: list[str] | None = None,
        platform_ids: list[str] | None = None,
        payment_methods: list[str] | None = None,
        categories: list[str] | None = None,
        booking_channels: list[str] | None = None,
    ) -> list[Offer]: ...
    def list_publishable(self) -> list[Offer]: ...
    def get_metadata(self) -> OfferMetadata: ...
    def get_manifest(self) -> DataManifest: ...
    def get_facets(self) -> FacetSnapshot: ...
