from datetime import date, timedelta

from fastapi import APIRouter, HTTPException, Query, Request

from app.schemas.availability import (
    AvailabilityDay,
    AvailabilityResponse,
)

router = APIRouter(tags=["Availability"])


@router.get("/availability", response_model=AvailabilityResponse)
def availability(
    request: Request,
    from_date: date = Query(alias="from"),
    to_date: date = Query(alias="to"),
):
    if to_date < from_date or (to_date - from_date).days > 30:
        raise HTTPException(
            status_code=422, detail="Availability range must be 1 to 31 days"
        )
    repository = request.app.state.offer_repository
    metadata = repository.get_metadata()
    days = []
    for offset in range((to_date - from_date).days + 1):
        day = from_date + timedelta(days=offset)
        offers = repository.list_offers(active_on=day)
        amounts = [
            offer.max_discount or offer.discount_value
            for offer in offers
            if offer.discount_type == "FLAT" or offer.max_discount is not None
        ]
        percentages = [
            offer.discount_value
            for offer in offers
            if offer.discount_type == "PERCENT" and offer.max_discount is None
        ]
        if amounts:
            kind, value = "AMOUNT", max(amounts)
            text = f"Up to ₹{value:,.0f}"
        elif percentages:
            kind, value = "PERCENTAGE", max(percentages)
            text = f"Up to {value:,.0f}% off"
        else:
            kind, value, text = None, None, "No offers"
        days.append(
            AvailabilityDay(
                date=day,
                offer_count=len(offers),
                benefit_type=kind,
                benefit_value=value,
                display_text=text,
                available=bool(offers),
            )
        )
    return AvailabilityResponse(
        data_version=metadata.data_version,
        availability_start=metadata.availability_start,
        availability_end=metadata.availability_end,
        dataset_last_updated_at=metadata.dataset_last_updated_at,
        days=days,
    )
