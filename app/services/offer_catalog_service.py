from __future__ import annotations

from datetime import date

from app.repositories.base import OfferRepository
from app.schemas.common import Pagination
from app.schemas.offers import CatalogueFacets, FacetOption, OffersResponse, PublicOffer


class UnsupportedFilterError(ValueError):
    pass


def _normalize(values: list[str] | None) -> list[str]:
    return list(
        dict.fromkeys(value.strip().upper() for value in values or [] if value.strip())
    )


class OfferCatalogService:
    def __init__(self, repository: OfferRepository):
        self.repository = repository

    def _validate(self, platforms, banks, methods, channels, categories) -> None:
        metadata = self.repository.get_metadata()
        supported: dict[str, set[str]] = {
            "platform": {item.id for item in metadata.platforms},
            "bank": {item.id for item in metadata.banks},
            "payment_method": set(metadata.payment_methods),
            "booking_channel": set(metadata.booking_channels),
            "category": set(metadata.categories),
        }
        for field, values in (
            ("platform", platforms),
            ("bank", banks),
            ("payment_method", methods),
            ("booking_channel", channels),
            ("category", categories),
        ):
            unknown = set(values) - supported[field]
            if unknown:
                raise UnsupportedFilterError(
                    f"Unsupported {field}: {', '.join(sorted(unknown))}"
                )

    def _options(
        self,
        *,
        group: str,
        active_on: date,
        selected: list[str],
        platforms: list[str],
        banks: list[str],
        methods: list[str],
        channels: list[str],
        categories: list[str],
    ) -> list[FacetOption]:
        metadata = self.repository.get_metadata()
        filters = {
            "platform_ids": None if group == "platforms" else platforms or None,
            "bank_ids": None if group == "banks" else banks or None,
            "payment_methods": None if group == "payment_methods" else methods or None,
            "booking_channels": None
            if group == "booking_channels"
            else channels or None,
            "categories": categories or None,
        }
        candidates = self.repository.list_offers(active_on=active_on, **filters)
        if group == "platforms":
            raw: list[tuple[str, str]] = [
                (item.id, item.name) for item in metadata.platforms
            ]
            attribute = "platform_id"
        elif group == "banks":
            raw = [(item.id, item.name) for item in metadata.banks]
            attribute = "bank_id"
        elif group == "payment_methods":
            raw = [
                (item, item.replace("_", " ").title())
                for item in metadata.payment_methods
            ]
            attribute = "payment_method"
        else:
            raw = [
                (item, item.replace("_", " ").title())
                for item in metadata.booking_channels
            ]
            attribute = "booking_channel"
        return [
            FacetOption(
                id=identifier,
                name=name,
                count=sum(
                    1 for offer in candidates if getattr(offer, attribute) == identifier
                ),
                selected=identifier in selected,
                disabled=not any(
                    getattr(offer, attribute) == identifier for offer in candidates
                ),
            )
            for identifier, name in raw
        ]

    def list(
        self,
        *,
        active_on: date,
        banks: list[str] | None,
        platforms: list[str] | None,
        payment_methods: list[str] | None,
        booking_channels: list[str] | None,
        categories: list[str] | None,
        page: int,
        limit: int,
    ) -> OffersResponse:
        banks, platforms = _normalize(banks), _normalize(platforms)
        methods, channels, categories = (
            _normalize(payment_methods),
            _normalize(booking_channels),
            _normalize(categories),
        )
        self._validate(platforms, banks, methods, channels, categories)
        offers = self.repository.list_offers(
            active_on=active_on,
            bank_ids=banks or None,
            platform_ids=platforms or None,
            payment_methods=methods or None,
            booking_channels=channels or None,
            categories=categories or None,
        )
        offers.sort(
            key=lambda offer: (offer.priority_score, offer.expiry_date), reverse=True
        )
        facets = CatalogueFacets(
            platforms=self._options(
                group="platforms",
                active_on=active_on,
                selected=platforms,
                platforms=platforms,
                banks=banks,
                methods=methods,
                channels=channels,
                categories=categories,
            ),
            banks=self._options(
                group="banks",
                active_on=active_on,
                selected=banks,
                platforms=platforms,
                banks=banks,
                methods=methods,
                channels=channels,
                categories=categories,
            ),
            payment_methods=self._options(
                group="payment_methods",
                active_on=active_on,
                selected=methods,
                platforms=platforms,
                banks=banks,
                methods=methods,
                channels=channels,
                categories=categories,
            ),
            booking_channels=self._options(
                group="booking_channels",
                active_on=active_on,
                selected=channels,
                platforms=platforms,
                banks=banks,
                methods=methods,
                channels=channels,
                categories=categories,
            ),
        )
        total = len(offers)
        start = (page - 1) * limit
        return OffersResponse(
            data_version=self.repository.get_manifest().data_version,
            offers=[
                PublicOffer.model_validate(offer)
                for offer in offers[start : start + limit]
            ],
            pagination=Pagination(
                page=page,
                limit=limit,
                total=total,
                total_pages=(total + limit - 1) // limit,
            ),
            facets=facets,
        )
