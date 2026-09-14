from datetime import date


def ids(repository, selected):
    return {offer.offer_id for offer in repository.list_offers(active_on=selected)}


def test_overlapping_and_future_validity_boundaries(client):
    repository = client.app.state.offer_repository
    july = ids(repository, date(2026, 7, 25))
    before_august = ids(repository, date(2026, 7, 31))
    august_first = ids(repository, date(2026, 8, 1))
    before_september = ids(repository, date(2026, 8, 31))
    september = ids(repository, date(2026, 9, 10))

    # July-1 offers are active in July
    assert {"MMT-HDFC-001", "MMT-SBI-001"} <= july
    # AXIS starts Aug 1 — not active Jul 31, active Aug 1
    assert "MMT-AXIS-001" not in before_august
    assert "MMT-AXIS-001" in august_first
    # AU starts Sep 1 — not active Aug 31, active Sep 10
    assert "MMT-AU-001" not in before_september
    assert "MMT-AU-001" in september


def test_expiry_is_inclusive_and_after_expiry_is_excluded(client):
    repository = client.app.state.offer_repository
    # MMT-AU-001 expires 2026-11-30 — inclusive last day, excluded next day
    assert "MMT-AU-001" in ids(repository, date(2026, 11, 30))
    assert "MMT-AU-001" not in ids(repository, date(2026, 12, 1))
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
