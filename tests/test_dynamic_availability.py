from datetime import date


def ids(repository, selected):
    return {offer.offer_id for offer in repository.list_offers(active_on=selected)}


def test_overlapping_and_future_validity_boundaries(client):
    repository = client.app.state.offer_repository

    # MAK-ICICI-9DD070 starts 2026-07-01 — active Jul 12, not active Jun 30
    assert "MAK-ICICI-9DD070" in ids(repository, date(2026, 7, 12))
    assert "MAK-ICICI-9DD070" not in ids(repository, date(2026, 6, 30))

    # MAK-INDUSIND-2B9F7D starts 2026-08-14 — not active Aug 13, active Aug 14
    assert "MAK-INDUSIND-2B9F7D" not in ids(repository, date(2026, 8, 13))
    assert "MAK-INDUSIND-2B9F7D" in ids(repository, date(2026, 8, 14))

    # MAK-KOTAK-919B61 starts 2026-09-01 — not active Aug 31, active Sep 10
    assert "MAK-KOTAK-919B61" not in ids(repository, date(2026, 8, 31))
    assert "MAK-KOTAK-919B61" in ids(repository, date(2026, 9, 10))


def test_expiry_is_inclusive_and_after_expiry_is_excluded(client):
    repository = client.app.state.offer_repository
    # MAK-KOTAK-919B61 expires 2027-03-31 — inclusive last day, excluded next day
    assert "MAK-KOTAK-919B61" in ids(repository, date(2027, 3, 31))
    assert "MAK-KOTAK-919B61" not in ids(repository, date(2027, 4, 1))
    # No offers exist after 2027-03-31
    assert ids(repository, date(2031, 1, 1)) == set()


def test_metadata_and_bounded_availability_endpoint(client):
    metadata = client.get("/api/v1/meta").json()
    assert metadata["availability_start"] == "2025-09-22"
    assert metadata["availability_end"] == "2027-03-31"
    response = client.get("/api/v1/availability?from=2026-07-30&to=2026-08-02")
    assert response.status_code == 200
    days = response.json()["days"]
    assert len(days) == 4
    assert all({"offer_count", "display_text", "available"} <= set(day) for day in days)
    # 31-day range exceeds the 30-day limit → 422
    assert client.get("/api/v1/availability?from=2026-07-01&to=2026-08-01").status_code == 422
