from dataclasses import dataclass
from decimal import Decimal

from app.domain.models import Offer


@dataclass(frozen=True)
class SavingsEstimate:
    estimated_savings: Decimal | None
    estimated_final_amount: Decimal | None
    savings_label: str
    eligible: bool


def _money(value: Decimal) -> str:
    return f"{value:,.0f}" if value == value.to_integral() else f"{value:,.2f}"


def _is_flat(offer: Offer) -> bool:
    """FLAT offers, plus CASHBACK offers whose value is a rupee amount.

    Cashback values below 100 are percentages ("5% cashback" is stored as 5); values of 100 or
    more are flat rupee amounts. The frontend applies the same rule (see savingsLabel).
    """
    return offer.discount_type == "FLAT" or (offer.discount_type == "CASHBACK" and offer.discount_value >= 100)


def describe_offer(offer: Offer) -> str:
    noun = "cashback" if offer.discount_type == "CASHBACK" else "off"
    if _is_flat(offer):
        return f"Flat ₹{_money(offer.discount_value)} {noun}"
    label = f"{_money(offer.discount_value)}% {noun}"
    if offer.max_discount is not None:
        label += f", maximum ₹{_money(offer.max_discount)}"
    return label


def estimate_savings(offer: Offer, booking_amount: Decimal | None) -> SavingsEstimate:
    if booking_amount is None:
        return SavingsEstimate(None, None, describe_offer(offer), True)
    if booking_amount <= 0:
        raise ValueError("booking_amount must be positive")
    if offer.min_transaction is not None and booking_amount < offer.min_transaction:
        return SavingsEstimate(Decimal("0"), booking_amount, "Minimum transaction not met", False)
    saving = offer.discount_value if _is_flat(offer) else booking_amount * offer.discount_value / Decimal("100")
    if offer.max_discount is not None:
        saving = min(saving, offer.max_discount)
    saving = min(max(saving, Decimal("0")), booking_amount)
    return SavingsEstimate(saving, booking_amount - saving, f"Estimated saving ₹{_money(saving)}", True)
