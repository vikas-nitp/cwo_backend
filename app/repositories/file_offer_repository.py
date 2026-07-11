import json
from datetime import date
from pathlib import Path

from app.domain.models import DataManifest, Offer, OfferMetadata
from app.domain.validity import is_publishable


class FileOfferRepository:
    def __init__(self, offers_path: Path, metadata_path: Path, manifest_path: Path):
        self.offers_path = offers_path
        self.metadata_path = metadata_path
        self.manifest_path = manifest_path
        self._offers: tuple[Offer, ...] = ()
        self._metadata: OfferMetadata | None = None
        self._manifest: DataManifest | None = None

    @property
    def loaded(self) -> bool:
        return (
            self._metadata is not None
            and self._manifest is not None
            and bool(self._offers)
        )

    def load(self) -> None:
        offers_data = json.loads(self.offers_path.read_text())
        metadata_data = json.loads(self.metadata_path.read_text())
        manifest_data = json.loads(self.manifest_path.read_text())
        offers = tuple(Offer.model_validate(item) for item in offers_data)
        if not offers:
            raise ValueError("snapshot contains no offers")
        self._offers = offers
        self._metadata = OfferMetadata.model_validate(metadata_data)
        self._manifest = DataManifest.model_validate(manifest_data)

    def list_offers(
        self,
        *,
        active_on: date,
        bank_ids: list[str] | None = None,
        platform_ids: list[str] | None = None,
        payment_method: str | None = None,
        category: str | None = None,
        booking_channel: str | None = None,
    ) -> list[Offer]:
        banks = {value.upper() for value in bank_ids or []}
        platforms = {value.upper() for value in platform_ids or []}
        return [
            offer
            for offer in self._offers
            if is_publishable(offer, active_on)
            and (not banks or offer.bank_id in banks)
            and (not platforms or offer.platform_id in platforms)
            and (payment_method is None or offer.payment_method == payment_method)
            and (category is None or offer.category == category)
            and (booking_channel is None or offer.booking_channel == booking_channel)
        ]

    def get_metadata(self) -> OfferMetadata:
        if self._metadata is None:
            raise RuntimeError("offer data is not loaded")
        return self._metadata

    def get_manifest(self) -> DataManifest:
        if self._manifest is None:
            raise RuntimeError("offer data is not loaded")
        return self._manifest
