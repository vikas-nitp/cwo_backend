import hashlib

from fastapi import Request, Response

from app.core.config import CONTRACT_VERSION


def version_headers(
    response: Response,
    *,
    version: str,
    cache_key: str,
    cache_control: str = "public, max-age=300",
) -> str:
    digest = hashlib.sha256(f"{version}:{cache_key}".encode()).hexdigest()[:16]
    etag = f'"{digest}"'
    response.headers["X-Data-Version"] = version
    response.headers["X-Contract-Version"] = CONTRACT_VERSION
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = cache_control
    return etag


def not_modified(request: Request, etag: str) -> bool:
    return request.headers.get("if-none-match") == etag
