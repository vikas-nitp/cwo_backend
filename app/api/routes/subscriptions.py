from __future__ import annotations

import hmac
import json
import os
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.core.storage import STORE_LOCK, data_path

router = APIRouter(tags=["Subscriptions"])

_IP_HASH_KEY = os.getenv("IP_HASH_SALT", "cwo-dev-salt-change-me").encode()
_EMAIL_RE = re.compile(r"^[^@]+@[^@]+\.[^@]+$")


class EmailSubscribeRequest(BaseModel):
    email: str = Field(max_length=320)
    source: str | None = Field(default=None, max_length=200)


def _validate_email(email: str) -> bool:
    return bool(_EMAIL_RE.match(email.strip())) and len(email) <= 320


def _emails_file():
    return data_path("subscriptions", "emails.jsonl")


def _load_emails() -> set[str]:
    path = _emails_file()
    if not path.exists():
        return set()
    emails: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
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

    client_host = request.client.host if request.client else "unknown"
    # Keyed hash: a plain SHA-256 of an IP can be reversed by enumerating the IPv4 space.
    ip_hash = hmac.new(_IP_HASH_KEY, client_host.encode(), "sha256").hexdigest()

    record = {
        "email": email,
        "source": body.source,
        "subscribed_at": datetime.now(timezone.utc).isoformat(),
        "ip_hash": ip_hash,
    }

    with STORE_LOCK:
        if email.lower() in _load_emails():
            return {"status": "already_subscribed"}
        path = _emails_file()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    return {"status": "subscribed"}
