from datetime import date


def ids(repository, selected):
    return {offer.offer_id for offer in repository.list_offers(active_on=selected)}


def test_overlapping_and_future_validity_boundaries(client):
    repository = client.app.state.offer_repository

    # PAY-HSBC-8923A57C starts 2026-05-01 — active May 1, not active Apr 30
    assert "PAY-HSBC-8923A57C" in ids(repository, date(2026, 5, 1))
    assert "PAY-HSBC-8923A57C" not in ids(repository, date(2026, 4, 30))

    # MAK-INDUSIND-F5BA1439 starts 2026-08-14 — not active Aug 13, active Aug 14
    assert "MAK-INDUSIND-F5BA1439" not in ids(repository, date(2026, 8, 13))
    assert "MAK-INDUSIND-F5BA1439" in ids(repository, date(2026, 8, 14))

    # CLE-AXIS-A32A0200 starts 2026-10-19 — not active Oct 18, active Oct 19
    assert "CLE-AXIS-A32A0200" not in ids(repository, date(2026, 10, 18))
    assert "CLE-AXIS-A32A0200" in ids(repository, date(2026, 10, 19))


def test_expiry_is_inclusive_and_after_expiry_is_excluded(client):
    repository = client.app.state.offer_repository
    # MAK-CANARA-8D42A3BA expires 2027-03-31 — inclusive last day, excluded next day
    assert "MAK-CANARA-8D42A3BA" in ids(repository, date(2027, 3, 31))
    assert "MAK-CANARA-8D42A3BA" not in ids(repository, date(2027, 4, 1))
    # No publishable offers exist after 2030-12-31
    assert ids(repository, date(2031, 1, 1)) == set()


def test_metadata_and_bounded_availability_endpoint(client):
    metadata = client.get("/api/v1/meta").json()
    assert metadata["availability_start"] == "2026-05-01"
    assert metadata["availability_end"] == "2030-12-31"
    response = client.get("/api/v1/availability?from=2026-07-30&to=2026-08-02")
    assert response.status_code == 200
    days = response.json()["days"]
    assert len(days) == 4
    assert all({"offer_count", "display_text", "available"} <= set(day) for day in days)
    # 31-day range exceeds the 30-day limit → 422
    assert client.get("/api/v1/availability?from=2026-07-01&to=2026-08-01").status_code == 422
