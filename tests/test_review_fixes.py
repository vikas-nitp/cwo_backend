import logging
import time
from datetime import date
from decimal import Decimal

from app.core.logging import DailyRotatingFileHandler
from tests.test_validity import make_offer


def test_offers_etag_changes_with_active_on(client):
    first = client.get("/api/v1/offers?active_on=2026-07-13")
    second = client.get("/api/v1/offers?active_on=2026-09-10")
    assert first.headers["etag"] != second.headers["etag"]
    stale = client.get("/api/v1/offers?active_on=2026-09-10", headers={"If-None-Match": first.headers["etag"]})
    assert stale.status_code == 200


def test_chunked_body_over_limit_is_rejected(client):
    def chunks():
        for _ in range(40):
            yield b"x" * 1024

    response = client.post("/api/v1/search", content=chunks(), headers={"Content-Type": "application/json"})
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "REQUEST_TOO_LARGE"


def test_declared_body_over_limit_is_rejected(client):
    response = client.post("/api/v1/search", content=b"x" * (33 * 1024), headers={"Content-Type": "application/json"})
    assert response.status_code == 413


def test_availability_reports_unready_data(client, monkeypatch):
    monkeypatch.setattr(type(client.app.state.offer_repository), "loaded", property(lambda self: False))
    response = client.get("/api/v1/availability?from=2026-07-13&to=2026-07-14")
    assert response.status_code == 503


def test_visitor_count_is_bounded(client, monkeypatch):
    monkeypatch.setattr("app.api.routes.visitors._MAX_SESSIONS", 2)
    original = client.app.state.feature_flags
    client.app.state.feature_flags = original.model_copy(update={"visitorCountEnabled": True})
    try:
        for vid in ("a", "b", "c", "d"):
            last = client.get(f"/api/v1/visitors/count?v={vid}")
        assert last.json() == {"count": 2}
    finally:
        client.app.state.feature_flags = original


def test_cashback_value_rules():
    from app.domain.calculations import estimate_savings

    flat_cashback = make_offer(discount_type="CASHBACK", discount_value=Decimal("500"), max_discount=None)
    pct_cashback = make_offer(discount_type="CASHBACK", discount_value=Decimal("5"), max_discount=None)
    assert estimate_savings(flat_cashback, Decimal("10000")).estimated_savings == Decimal("500")
    assert estimate_savings(pct_cashback, Decimal("10000")).estimated_savings == Decimal("500")
    assert "cashback" in estimate_savings(flat_cashback, None).savings_label


def test_rollover_schedules_next_rollover(tmp_path):
    handler = DailyRotatingFileHandler(str(tmp_path / "app.log"))
    try:
        handler.rolloverAt = 0  # pretend midnight passed
        handler.doRollover()
        assert handler.rolloverAt > time.time()
        record = logging.LogRecord("t", logging.INFO, __file__, 1, "m", (), None)
        assert handler.shouldRollover(record) == 0
    finally:
        handler.close()


def test_publishable_uses_ist_today(client, monkeypatch):
    repo = client.app.state.offer_repository
    monkeypatch.setattr("app.repositories.file_offer_repository.today_ist", lambda: date(2031, 1, 1))
    assert repo.list_publishable() == []
