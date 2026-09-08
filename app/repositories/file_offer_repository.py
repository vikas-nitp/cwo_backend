import json
from datetime import date
from pathlib import Path

from app.domain.models import DataManifest, FacetSnapshot, Offer, OfferMetadata
from app.domain.validity import is_publishable


class FileOfferRepository:
    def __init__(
        self,
        offers_path: Path,
        metadata_path: Path,
        manifest_path: Path,
        facets_path: Path,
    ):
        self.offers_path = offers_path
        self.metadata_path = metadata_path
        self.manifest_path = manifest_path
        self.facets_path = facets_path
        self._offers: tuple[Offer, ...] = ()
        self._metadata: OfferMetadata | None = None
        self._manifest: DataManifest | None = None
        self._facets: FacetSnapshot | None = None

    @property
    def loaded(self) -> bool:
        return (
            self._metadata is not None
            and self._manifest is not None
            and self._facets is not None
            and bool(self._offers)
        )

    def load(self) -> None:
        offers_data = json.loads(self.offers_path.read_text())
        metadata_data = json.loads(self.metadata_path.read_text())
        manifest_data = json.loads(self.manifest_path.read_text())
        facets_data = json.loads(self.facets_path.read_text())
        offers = tuple(Offer.model_validate(item) for item in offers_data)
        if not offers:
            raise ValueError("snapshot contains no offers")
        if len({offer.offer_id for offer in offers}) != len(offers):
            raise ValueError("snapshot contains duplicate offer IDs")
        self._offers = offers
        self._metadata = OfferMetadata.model_validate(metadata_data)
        self._manifest = DataManifest.model_validate(manifest_data)
        self._facets = FacetSnapshot.model_validate(facets_data)
        versions = {
            self._metadata.data_version,
            self._manifest.data_version,
            self._facets.data_version,
        }
        if len(versions) != 1:
            raise ValueError("generated snapshot data versions do not match")
        if not self.list_publishable():
            raise ValueError("snapshot contains no publishable offers")

    def list_offers(
        self,
        *,
        active_on: date,
        bank_ids: list[str] | None = None,
        platform_ids: list[str] | None = None,
        payment_methods: list[str] | None = None,
        categories: list[str] | None = None,
        booking_channels: list[str] | None = None,
    ) -> list[Offer]:
        banks = {value.upper() for value in bank_ids or []}
        platforms = {value.upper() for value in platform_ids or []}
        methods = {value.upper() for value in payment_methods or []}
        category_values = {value.upper() for value in categories or []}
        channels = {value.upper() for value in booking_channels or []}
        return [
            offer
            for offer in self._offers
            if is_publishable(offer, active_on)
            and (not banks or offer.bank_id in banks)
            and (not platforms or offer.platform_id in platforms)
            and (not methods or offer.payment_method in methods)
            and (not category_values or offer.category in category_values)
            and (not channels or offer.booking_channel in channels)
        ]

    def list_publishable(self) -> list[Offer]:
        return [
            offer
            for offer in self._offers
            if offer.is_active
            and offer.publish_status == "READY"
            and offer.evidence_status == "VERIFIED"
        ]

    def get_metadata(self) -> OfferMetadata:
        if self._metadata is None:
            raise RuntimeError("offer data is not loaded")
        return self._metadata

    def get_manifest(self) -> DataManifest:
        if self._manifest is None:
            raise RuntimeError("offer data is not loaded")
        return self._manifest

    def get_facets(self) -> FacetSnapshot:
        if self._facets is None:
            raise RuntimeError("facet data is not loaded")
        return self._facets
