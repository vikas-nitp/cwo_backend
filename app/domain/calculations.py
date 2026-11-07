from dataclasses import dataclass
from decimal import Decimal

from app.domain.models import DiscountTier, Offer


@dataclass(frozen=True)
class SavingsEstimate:
    estimated_savings: Decimal | None
    estimated_final_amount: Decimal | None
    savings_label: str
    eligible: bool


def _money(value: Decimal) -> str:
    return f"{value:,.0f}" if value == value.to_integral() else f"{value:,.2f}"


def describe_offer(offer: Offer) -> str:
    if offer.discount_type == "FLAT":
        return f"Flat ₹{_money(offer.discount_value)} off"
    label = f"{_money(offer.discount_value)}% off"
    if offer.max_discount is not None:
        label += f", maximum ₹{_money(offer.max_discount)}"
    return label


def _find_tier(tiers: list[DiscountTier], amount: Decimal) -> DiscountTier | None:
    """Return the matching tier for the given booking amount, or None."""
    for tier in tiers:
        if amount < tier.min_amount:
            continue
        if tier.max_amount is None or amount <= tier.max_amount:
            return tier
    return None


def _savings_from_tier(tier: DiscountTier, booking_amount: Decimal) -> Decimal:
    """Compute savings for one tier."""
    if tier.discount_type == "FLAT":
        saving = tier.discount_value
    else:
        saving = booking_amount * tier.discount_value / Decimal("100")
        if tier.max_discount is not None:
            saving = min(saving, tier.max_discount)
    return min(max(saving, Decimal("0")), booking_amount)


def estimate_savings(
    offer: Offer,
    booking_amount: Decimal | None,
    *,
    tiered_discount_enabled: bool = False,
) -> SavingsEstimate:
    if booking_amount is None:
        return SavingsEstimate(None, None, describe_offer(offer), True)
    if booking_amount <= 0:
        raise ValueError("booking_amount must be positive")

    # Tier-aware path: use full tier table when FF is on and tiers are present
    tiers = offer.discount_tiers if tiered_discount_enabled else None
    if tiers:
        matched = _find_tier(tiers, booking_amount)
        if matched is None:
            return SavingsEstimate(Decimal("0"), booking_amount, "Minimum transaction not met", False)
        saving = _savings_from_tier(matched, booking_amount)
        return SavingsEstimate(saving, booking_amount - saving, f"Estimated saving ₹{_money(saving)}", True)

    if offer.min_transaction is not None and booking_amount < offer.min_transaction:
        return SavingsEstimate(Decimal("0"), booking_amount, "Minimum transaction not met", False)
    saving = (
        offer.discount_value
        if offer.discount_type == "FLAT"
        else booking_amount * offer.discount_value / Decimal("100")
    )
    if offer.max_discount is not None:
        saving = min(saving, offer.max_discount)
    saving = min(max(saving, Decimal("0")), booking_amount)
    return SavingsEstimate(saving, booking_amount - saving, f"Estimated saving ₹{_money(saving)}", True)
