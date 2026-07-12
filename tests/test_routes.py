from datetime import date, timedelta


def test_health(client):
    assert client.get("/health/live").json() == {"ok": True}
    ready = client.get("/health/ready")
    assert ready.status_code == 200
    assert ready.json()["data_loaded"] is True


def test_meta_and_flags(client):
    assert client.get("/api/v1/meta").json()["data_version"]
    flags = client.get("/api/v1/feature-flags").json()
    assert flags == {
        "phase2UserFeaturesEnabled": False,
        "publicAllOffersEnabled": True,
        "couponCodeEnabled": False,
        "analyticsEnabled": True,
        "bookingAmountComparisonEnabled": False,
        "config_version": flags["config_version"],
    }


def test_offers_pagination(client):
    payload = client.get("/api/v1/offers?limit=2").json()
    assert len(payload["offers"]) == 2
    assert payload["pagination"]["total"] == 6
    assert payload["facets"]["platforms"]
    assert all("coupon_code" not in offer for offer in payload["offers"])


def test_search_with_calculated_savings(client, valid_search):
    response = client.post("/api/v1/search", json=valid_search)
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["date_strip"]) == 11
    assert body["date_strip"][0]["date"] == date.today().isoformat()
    assert body["date_strip"][0]["display_text"]
    assert "estimated_savings" not in body["offers"][0]


def test_booking_comparison_is_flag_guarded(client, valid_search):
    original = client.app.state.feature_flags
    payload = {**valid_search, "booking_amount": 6500}
    try:
        disabled = client.post("/api/v1/search", json=payload)
        assert disabled.status_code == 400
        assert disabled.json()["error"]["code"] == "BOOKING_COMPARISON_DISABLED"
        client.app.state.feature_flags = original.model_copy(
            update={"bookingAmountComparisonEnabled": True}
        )
        enabled = client.post("/api/v1/search", json=payload)
        assert enabled.status_code == 200
        assert enabled.json()["offers"][0]["estimated_savings"] is not None
    finally:
        client.app.state.feature_flags = original


def test_same_airport_and_date_window(client, valid_search):
    same = {**valid_search, "to": "DEL"}
    assert client.post("/api/v1/search", json=same).status_code == 422
    late = {**valid_search, "date": (date.today() + timedelta(days=11)).isoformat()}
    response = client.post("/api/v1/search", json=late)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_SEARCH_DATE"


def test_unknown_dynamic_platform_returns_no_offers(client, valid_search):
    response = client.post(
        "/api/v1/search", json={**valid_search, "platforms": ["GOIBIBO"]}
    )
    assert response.status_code == 200
    assert response.json()["offers"] == []


def test_not_found_uses_error_contract(client):
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_multi_select_filters_and_strict_bank(client):
    response = client.get(
        "/api/v1/offers?platform=MAKEMYTRIP&platform=CLEARTRIP&bank=HDFC&bank=SBI&payment_method=CREDIT"
    )
    assert response.status_code == 200
    offers = response.json()["offers"]
    assert {offer["offer_id"] for offer in offers} == {"MMT-HDFC-001", "MMT-SBI-001"}
    assert all(offer["bank_id"] in {"HDFC", "SBI"} for offer in offers)


def test_unsupported_filter_codes(client):
    platform = client.get("/api/v1/offers?platform=GOIBIBO")
    assert platform.status_code == 400
    assert platform.json()["error"]["code"] == "UNSUPPORTED_PLATFORM"
    bank = client.get("/api/v1/offers?bank=UNKNOWN")
    assert bank.status_code == 400
    assert bank.json()["error"]["code"] == "UNSUPPORTED_FILTER"


def test_version_cache_headers_and_conditional_get(client, valid_search):
    meta = client.get("/api/v1/meta")
    assert meta.headers["x-contract-version"] == "1.1"
    assert meta.headers["x-data-version"]
    assert (
        client.get(
            "/api/v1/meta", headers={"If-None-Match": meta.headers["etag"]}
        ).status_code
        == 304
    )
    offers = client.get("/api/v1/offers")
    assert (
        client.get(
            "/api/v1/offers", headers={"If-None-Match": offers.headers["etag"]}
        ).status_code
        == 304
    )
    search = client.post("/api/v1/search", json=valid_search)
    assert search.headers["cache-control"] == "no-store"
    assert search.headers["x-contract-version"] == "1.1"


def test_readiness_allows_no_offer_active_today(client, monkeypatch):
    repository = client.app.state.offer_repository
    monkeypatch.setattr(repository, "list_offers", lambda **kwargs: [])
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["offer_count"] == 6
    assert response.json()["active_offer_count"] == 0
