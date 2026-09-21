from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter(tags=["UserCards"])

_USER_CARDS_DIR = Path(__file__).resolve().parents[4] / "data" / "user_cards"
_CARDS_FILE = _USER_CARDS_DIR / "user1.jsonl"
_PREFS_FILE = _USER_CARDS_DIR / "user1_prefs.json"

PaymentMethod = Literal["CREDIT_CARD", "DEBIT_CARD"]

_DEFAULT_PREFS = {"notify_expiring": False, "notify_new": False}


# ── Request / Response models ───────────────────────────────────────────────

class SaveCardRequest(BaseModel):
    bank_id: str
    card_name: str | None = None
    payment_method: PaymentMethod


class CardRecord(BaseModel):
    card_id: str
    bank_id: str
    card_name: str | None
    payment_method: PaymentMethod


class NotificationPrefsRequest(BaseModel):
    notify_expiring: bool
    notify_new: bool


# ── Helpers ─────────────────────────────────────────────────────────────────

def _load_cards() -> list[dict]:
    if not _CARDS_FILE.exists():
        return []
    cards: list[dict] = []
    for line in _CARDS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            cards.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return cards


def _save_cards(cards: list[dict]) -> None:
    _USER_CARDS_DIR.mkdir(parents=True, exist_ok=True)
    with _CARDS_FILE.open("w", encoding="utf-8") as f:
        for card in cards:
            f.write(json.dumps(card) + "\n")


def _load_prefs() -> dict:
    if not _PREFS_FILE.exists():
        return dict(_DEFAULT_PREFS)
    try:
        data = json.loads(_PREFS_FILE.read_text(encoding="utf-8"))
        return {
            "notify_expiring": bool(data.get("notify_expiring", False)),
            "notify_new": bool(data.get("notify_new", False)),
        }
    except (json.JSONDecodeError, OSError):
        return dict(_DEFAULT_PREFS)


def _not_enabled_response():
    return JSONResponse(status_code=404, content={"error": {"code": "NOT_FOUND"}})


# ── Card endpoints ───────────────────────────────────────────────────────────

@router.post("/user/cards")
def save_card(request: Request, body: SaveCardRequest):
    flags = request.app.state.feature_flags
    if flags is None or not flags.userCardsEnabled:
        return _not_enabled_response()

    card_id = str(uuid.uuid4())
    record = {
        "card_id": card_id,
        "bank_id": body.bank_id,
        "card_name": body.card_name,
        "payment_method": body.payment_method,
    }
    _USER_CARDS_DIR.mkdir(parents=True, exist_ok=True)
    with _CARDS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    return record


@router.get("/user/cards")
def list_cards(request: Request):
    flags = request.app.state.feature_flags
    if flags is None or not flags.userCardsEnabled:
        return _not_enabled_response()

    return {"cards": _load_cards()}


@router.delete("/user/cards/{card_id}")
def delete_card(card_id: str, request: Request):
    flags = request.app.state.feature_flags
    if flags is None or not flags.userCardsEnabled:
        return _not_enabled_response()

    cards = _load_cards()
    new_cards = [c for c in cards if c.get("card_id") != card_id]
    if len(new_cards) == len(cards):
        return JSONResponse(status_code=404, content={"error": {"code": "NOT_FOUND", "message": "Card not found"}})

    _save_cards(new_cards)
    return {"deleted": True}


# ── Notification prefs endpoints ─────────────────────────────────────────────

@router.post("/user/notification-prefs")
def save_notification_prefs(request: Request, body: NotificationPrefsRequest):
    flags = request.app.state.feature_flags
    if flags is None or not flags.notificationsEnabled:
        return _not_enabled_response()

    prefs = {"notify_expiring": body.notify_expiring, "notify_new": body.notify_new}
    _USER_CARDS_DIR.mkdir(parents=True, exist_ok=True)
    _PREFS_FILE.write_text(json.dumps(prefs), encoding="utf-8")
    return {"saved": True}


@router.get("/user/notification-prefs")
def get_notification_prefs(request: Request):
    flags = request.app.state.feature_flags
    if flags is None or not flags.notificationsEnabled:
        return _not_enabled_response()

    return _load_prefs()
