from app.domain.models import Offer
from app.schemas.common import Pagination
from pydantic import BaseModel


class OffersResponse(BaseModel):
    data_version: str
    offers: list[Offer]
    pagination: Pagination
