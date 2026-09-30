import threading

import pytest

SESSION_A = {"X-Session-Id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"}
SESSION_B = {"X-Session-Id": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"}
CARD = {"bank_id": "HDFC", "card_name": "Regalia", "payment_method": "CREDIT"}


@pytest.fixture
def user_client(client):
    original = client.app.state.feature_flags
    client.app.state.feature_flags = original.model_copy(
        update={"userCardsEnabled": True, "notificationsEnabled": True, "subscriptionsEnabled": True}
    )
    yield client
    client.app.state.feature_flags = original


def test_cards_are_isolated_per_session(user_client):
    saved = user_client.post("/api/v1/user/cards", json=CARD, headers=SESSION_A)
    assert saved.status_code == 200
    assert user_client.get("/api/v1/user/cards", headers=SESSION_A).json()["cards"] == [saved.json()]
    assert user_client.get("/api/v1/user/cards", headers=SESSION_B).json()["cards"] == []


def test_delete_only_affects_own_session(user_client):
    card_id = user_client.post("/api/v1/user/cards", json=CARD, headers=SESSION_A).json()["card_id"]
    assert user_client.delete(f"/api/v1/user/cards/{card_id}", headers=SESSION_B).status_code == 404
    assert user_client.delete(f"/api/v1/user/cards/{card_id}", headers=SESSION_A).json() == {"deleted": True}
    assert user_client.get("/api/v1/user/cards", headers=SESSION_A).json()["cards"] == []


def test_session_header_is_required_and_validated(user_client):
    assert user_client.get("/api/v1/user/cards").status_code == 422
    for bad in ("short", "../../etc/passwd-padding-padding", "x" * 65):
        response = user_client.get("/api/v1/user/cards", headers={"X-Session-Id": bad})
        assert response.status_code == 422, bad


def test_rejects_legacy_payment_method_values(user_client):
    body = {**CARD, "payment_method": "CREDIT_CARD"}
    assert user_client.post("/api/v1/user/cards", json=body, headers=SESSION_A).status_code == 422


def test_card_limit(user_client):
    for _ in range(20):
        assert user_client.post("/api/v1/user/cards", json=CARD, headers=SESSION_A).status_code == 200
    over = user_client.post("/api/v1/user/cards", json=CARD, headers=SESSION_A)
    assert over.status_code == 422
    assert over.json()["error"]["code"] == "CARD_LIMIT_REACHED"
    assert user_client.post("/api/v1/user/cards", json=CARD, headers=SESSION_B).status_code == 200


def test_notification_prefs_are_per_session_and_keep_cards(user_client):
    user_client.post("/api/v1/user/cards", json=CARD, headers=SESSION_A)
    prefs = {"notify_expiring": True, "notify_new": False}
    assert user_client.post("/api/v1/user/notification-prefs", json=prefs, headers=SESSION_A).json() == {"saved": True}
    assert user_client.get("/api/v1/user/notification-prefs", headers=SESSION_A).json() == prefs
    assert user_client.get("/api/v1/user/notification-prefs", headers=SESSION_B).json() == {
        "notify_expiring": False,
        "notify_new": False,
    }
    assert len(user_client.get("/api/v1/user/cards", headers=SESSION_A).json()["cards"]) == 1


def test_concurrent_saves_do_not_lose_cards(user_client):
    def save():
        user_client.post("/api/v1/user/cards", json=CARD, headers=SESSION_A)

    threads = [threading.Thread(target=save) for _ in range(10)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len(user_client.get("/api/v1/user/cards", headers=SESSION_A).json()["cards"]) == 10


def test_cors_preflight_allows_delete_and_session_header(client):
    response = client.options(
        "/api/v1/user/cards/abc",
        headers={
            "Origin": "http://localhost:8080",
            "Access-Control-Request-Method": "DELETE",
            "Access-Control-Request-Headers": "x-session-id",
        },
    )
    assert response.status_code == 200
    assert "DELETE" in response.headers["access-control-allow-methods"]
    assert "x-session-id" in response.headers["access-control-allow-headers"].lower()


def test_email_subscription_is_deduplicated(user_client):
    body = {"email": "Person@Example.com"}
    assert user_client.post("/api/v1/subscriptions/email", json=body).json() == {"status": "subscribed"}
    assert user_client.post("/api/v1/subscriptions/email", json={"email": "person@example.com"}).json() == {
        "status": "already_subscribed"
    }
