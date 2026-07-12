from datetime import date


def ids(repository, selected):
    return {offer.offer_id for offer in repository.list_offers(active_on=selected)}


def test_overlapping_and_future_validity_boundaries(client):
    repository = client.app.state.offer_repository
    july = ids(repository, date(2026, 7, 25))
    september = ids(repository, date(2026, 9, 10))
    before_future = ids(repository, date(2026, 8, 14))
    future_active = ids(repository, date(2026, 8, 15))

    assert {"MMT-HDFC-01", "MMT-SBI-01"} <= july
    assert "MMT-HDFC-01" in september and "MMT-SBI-01" not in september
    assert "MMT-AXIS-01" not in before_future
    assert "MMT-AXIS-01" in future_active


def test_expiry_is_inclusive_and_after_expiry_is_excluded(client):
    repository = client.app.state.offer_repository
    assert "MMT-HDFC-D01" in ids(repository, date(2026, 7, 31))
    assert "MMT-HDFC-D01" not in ids(repository, date(2026, 8, 1))
    assert not ids(repository, date(2026, 10, 16))


def test_metadata_and_bounded_availability_endpoint(client):
    metadata = client.get("/api/v1/meta").json()
    assert metadata["availability_start"] == "2026-07-13"
    assert metadata["availability_end"] == "2026-10-15"
    response = client.get("/api/v1/availability?from=2026-07-30&to=2026-08-02")
    assert response.status_code == 200
    days = response.json()["days"]
    assert len(days) == 4
    assert all({"offer_count", "display_text", "available"} <= set(day) for day in days)
    assert (
        client.get("/api/v1/availability?from=2026-07-01&to=2026-08-01").status_code
        == 422
    )
