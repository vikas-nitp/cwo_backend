from app.domain.models import Offer
from app.schemas.common import Pagination
from pydantic import BaseModel


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
    offers: list[Offer]
    pagination: Pagination
    facets: CatalogueFacets
