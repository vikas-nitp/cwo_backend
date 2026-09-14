from datetime import date

from app.domain.models import Offer


def is_active_on_day(offer: Offer, active_on: date) -> bool:
    """Return True if the offer is valid on the given weekday.

    ``valid_days`` uses Python's weekday convention: 0=Monday … 6=Sunday.
    ``None`` means the offer is valid every day.
    """
    if offer.valid_days is None:
        return True
    return active_on.weekday() in offer.valid_days


def is_publishable(offer: Offer, active_on: date) -> bool:
    return (
        offer.is_active
        and offer.publish_status == "READY"
        and offer.evidence_status == "VERIFIED"
        and offer.valid_from <= active_on <= offer.expiry_date
        and is_active_on_day(offer, active_on)
    )
