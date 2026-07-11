from datetime import date

from app.domain.models import Offer


def is_publishable(offer: Offer, active_on: date) -> bool:
    return (
        offer.is_active
        and offer.publish_status == "READY"
        and offer.evidence_status == "VERIFIED"
        and offer.valid_from <= active_on <= offer.valid_to
    )
