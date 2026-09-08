from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.domain.calculations import SavingsEstimate
from app.domain.models import Offer


DisplayKind = str


@dataclass(frozen=True)
class RankedOffer:
    offer: Offer
    estimate: SavingsEstimate
    display_kind: DisplayKind
    display_rank: int
    savings_delta: Decimal | None


def _benefit(offer: Offer, estimate: SavingsEstimate) -> Decimal:
    if estimate.estimated_savings is not None:
        return estimate.estimated_savings
    if offer.max_discount is not None:
        return offer.max_discount
    return offer.discount_value


def rank_offers(
    items: list[tuple[Offer, SavingsEstimate]],
    selected_banks: list[str],
    travel_date: date,
) -> list[RankedOffer]:
    selected = list(dict.fromkeys(bank.upper() for bank in selected_banks))
    ordered = sorted(
        items,
        key=lambda item: (_benefit(*item), item[0].priority_score, item[0].expiry_date),
        reverse=True,
    )
    result: list[tuple[Offer, SavingsEstimate, str]] = []
    used: set[str] = set()

    if not selected:
        general = next(
            (item for item in ordered if item[0].payment_method != "NO_CARD"), None
        )
        if general:
            result.append((*general, "GENERAL_BEST"))
            used.add(general[0].offer_id)

    for index, bank in enumerate(selected[:2]):
        match = next(
            (item for item in ordered if item[0].bank_id == bank and item[1].eligible),
            None,
        )
        if match:
            result.append(
                (*match, "SELECTED_CARD" if index == 0 else "SECOND_SELECTED_CARD")
            )
            used.add(match[0].offer_id)

    selected_best = max((_benefit(o, e) for o, e, _ in result), default=Decimal("-1"))
    alternative = next(
        (
            item
            for item in ordered
            if item[0].bank_id
            and item[0].bank_id not in selected
            and item[0].offer_id not in used
            and _benefit(*item) > selected_best
        ),
        None,
    )
    if alternative and selected:
        result.append((*alternative, "BETTER_ALTERNATIVE"))
        used.add(alternative[0].offer_id)

    default = next(
        (
            item
            for item in ordered
            if item[0].payment_method == "NO_CARD" and item[0].offer_id not in used
        ),
        None,
    )
    if default:
        result.append((*default, "DEFAULT_OFFER"))
        used.add(default[0].offer_id)

    if not result and ordered:
        result.append((*ordered[0], "GENERAL_BEST"))

    baseline = result[0][1].estimated_savings if result else None
    return [
        RankedOffer(
            o,
            e,
            kind,
            i,
            e.estimated_savings - baseline
            if baseline is not None
            and e.eligible
            and e.estimated_savings is not None
            and e.estimated_savings > baseline
            else None,
        )
        for i, (o, e, kind) in enumerate(result, 1)
    ]
