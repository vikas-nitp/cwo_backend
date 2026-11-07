from datetime import date


def ids(repository, selected):
    return {offer.offer_id for offer in repository.list_offers(active_on=selected)}


def test_overlapping_and_future_validity_boundaries(client):
    repository = client.app.state.offer_repository

    # All fixture offers start 2026-07-01 — active on start date, not active the day before
    assert "MMT-HDFC-001" in ids(repository, date(2026, 7, 1))
    assert "MMT-HDFC-001" not in ids(repository, date(2026, 6, 30))

    # CT-ICICI-001 is a Cleartrip offer — same validity window
    assert "CT-ICICI-001" not in ids(repository, date(2026, 6, 30))
    assert "CT-ICICI-001" in ids(repository, date(2026, 7, 1))

    # Both MMT and CT offers are active within the validity window
    assert "MMT-AXIS-001" in ids(repository, date(2026, 10, 19))
    assert "CT-AXIS-001" in ids(repository, date(2026, 10, 19))


def test_expiry_is_inclusive_and_after_expiry_is_excluded(client):
    repository = client.app.state.offer_repository
    # All fixture offers expire 2027-12-31 — inclusive last day, excluded next day
    assert "MMT-HDFC-001" in ids(repository, date(2027, 12, 31))
    assert "MMT-HDFC-001" not in ids(repository, date(2028, 1, 1))
    # No offers exist after 2027-12-31
    assert ids(repository, date(2028, 1, 1)) == set()


def test_metadata_and_bounded_availability_endpoint(client):
    metadata = client.get("/api/v1/meta").json()
    assert metadata["availability_start"] == "2026-07-01"
    assert metadata["availability_end"] == "2027-12-31"
    response = client.get("/api/v1/availability?from=2026-07-30&to=2026-08-02")
    assert response.status_code == 200
    days = response.json()["days"]
    assert len(days) == 4
    assert all({"offer_count", "display_text", "available"} <= set(day) for day in days)
    # 31-day range exceeds the 30-day limit → 422
    assert client.get("/api/v1/availability?from=2026-07-01&to=2026-08-01").status_code == 422
