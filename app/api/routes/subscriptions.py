from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter(tags=["Subscriptions"])

_SUBSCRIPTIONS_DIR = Path(__file__).resolve().parents[4] / "data" / "subscriptions"
_EMAILS_FILE = _SUBSCRIPTIONS_DIR / "emails.jsonl"
_EMAIL_RE = re.compile(r"^[^@]+@[^@]+\.[^@]+$")


class EmailSubscribeRequest(BaseModel):
    email: str
    source: str | None = None


def _validate_email(email: str) -> bool:
    return bool(_EMAIL_RE.match(email.strip())) and len(email) <= 320


def _load_emails() -> set[str]:
    if not _EMAILS_FILE.exists():
        return set()
    emails: set[str] = set()
    for line in _EMAILS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
            if "email" in record:
                emails.add(record["email"].lower())
        except json.JSONDecodeError:
            continue
    return emails


@router.post("/subscriptions/email")
def subscribe_email(request: Request, body: EmailSubscribeRequest):
    flags = request.app.state.feature_flags
    if flags is None or not flags.subscriptionsEnabled:
        return JSONResponse(status_code=404, content={"error": {"code": "NOT_FOUND"}})

    email = body.email.strip()
    if not _validate_email(email):
        return JSONResponse(
            status_code=422,
            content={"error": {"code": "INVALID_EMAIL", "message": "Invalid email address"}},
        )

    existing = _load_emails()
    if email.lower() in existing:
        return {"status": "already_subscribed"}

    client_host = request.client.host if request.client else "unknown"
    ip_hash = hashlib.sha256(client_host.encode()).hexdigest()

    record = {
        "email": email,
        "source": body.source,
        "subscribed_at": datetime.now(timezone.utc).isoformat(),
        "ip_hash": ip_hash,
    }

    _SUBSCRIPTIONS_DIR.mkdir(parents=True, exist_ok=True)
    with _EMAILS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    return {"status": "subscribed"}
