from datetime import date, timedelta


def test_health(client):
    assert client.get("/health/live").json() == {"ok": True}
    ready = client.get("/health/ready")
    assert ready.status_code == 200
    assert ready.json()["data_loaded"] is True


def test_meta_and_flags(client):
    assert client.get("/api/v1/meta").json()["data_version"]
    assert client.get("/api/v1/feature-flags").json() == {
        "phase2UserFeaturesEnabled": False,
        "publicAllOffersEnabled": True,
        "couponCodeEnabled": False,
        "analyticsEnabled": True,
        "bookingAmountComparisonEnabled": False,
    }


def test_offers_pagination(client):
    payload = client.get("/api/v1/offers?limit=2").json()
    assert len(payload["offers"]) == 2
    assert payload["pagination"]["total"] == 6


def test_search_with_calculated_savings(client, valid_search):
    response = client.post("/api/v1/search", json=valid_search)
    assert response.status_code == 200, response.text
    body = response.json()
    assert "strip7days" not in body
    assert body["offers"][0]["estimated_savings"] is not None


def test_same_airport_and_date_window(client, valid_search):
    same = {**valid_search, "to": "DEL"}
    assert client.post("/api/v1/search", json=same).status_code == 422
    late = {**valid_search, "date": (date.today() + timedelta(days=11)).isoformat()}
    response = client.post("/api/v1/search", json=late)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_SEARCH_DATE"


def test_unsupported_platform(client, valid_search):
    response = client.post(
        "/api/v1/search", json={**valid_search, "platforms": ["GOIBIBO"]}
    )
    assert response.status_code == 422


def test_not_found_uses_error_contract(client):
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
