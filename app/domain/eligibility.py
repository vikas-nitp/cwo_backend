from app.domain.models import Offer


def bank_matches(offer: Offer, bank_ids: list[str] | None) -> bool:
    return not bank_ids or offer.bank_id in {value.upper() for value in bank_ids}
