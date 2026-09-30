"""Small file-backed storage helpers shared by the user-data routes."""

from __future__ import annotations

import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Any

from app.core import config

# Routes are sync handlers running in a thread pool, so read-modify-write
# cycles must be serialised. The lock is per-process: run a single worker
# (see Dockerfile) or move to a real database before scaling out.
STORE_LOCK = threading.RLock()


def data_path(*parts: str) -> Path:
    return Path(config.USER_DATA_DIR).joinpath(*parts)


def read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def write_json_atomic(path: Path, value: Any) -> None:
    """Write via a temp file + rename so readers never see a partial file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle)
        os.replace(tmp_name, path)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise
