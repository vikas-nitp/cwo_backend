"""
Middleware for rate limiting, request logging, and security.
Railway-compatible (in-memory, single instance MVP).
"""

import hashlib
import time
import uuid
from collections import defaultdict
from datetime import date
from typing import Callable, Dict, Set

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import APP_ENV, RateLimitConfig
from app.core.logging import get_logger

logger = get_logger("app.middleware")


def _middleware_error(
    request: Request, status: int, code: str, message: str
) -> JSONResponse:
    request_id = getattr(
        request.state,
        "request_id",
        request.headers.get("x-request-id") or str(uuid.uuid4()),
    )
    return JSONResponse(
        status_code=status,
        content={
            "error": {
                "code": code,
                "message": message,
                "field": None,
                "request_id": request_id,
            }
        },
    )


# ────────────────────────────────────────────────────────────────────
# In-Memory Rate Limiter (Railway single-instance MVP)
# ────────────────────────────────────────────────────────────────────


class InMemoryRateLimiter:
    """
    Simple token bucket rate limiter.
    Fail-open: if anything errors, allow request + log warning.
    """

    def __init__(self):
        # {client_key: [(timestamp, count), ...]}
        self._global_buckets: Dict[str, list] = defaultdict(list)
        self._search_buckets: Dict[str, list] = defaultdict(list)
        self._cleanup_interval = 60  # seconds
        self._last_cleanup = time.time()

    def _get_client_key(self, request: Request) -> str:
        """Get client identifier (IP-based, privacy-safe)."""
        # Railway sets X-Forwarded-For
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"

        # Hash for privacy
        return hashlib.sha256(ip.encode()).hexdigest()[:16]

    def _cleanup_old_entries(self, bucket: list, window_seconds: int) -> list:
        """Remove entries older than window."""
        cutoff = time.time() - window_seconds
        return [ts for ts in bucket if ts > cutoff]

    def _maybe_cleanup(self):
        """Periodic cleanup to prevent memory growth."""
        now = time.time()
        if now - self._last_cleanup > self._cleanup_interval:
            self._last_cleanup = now
            # Clean global buckets
            for key in list(self._global_buckets.keys()):
                self._global_buckets[key] = self._cleanup_old_entries(
                    self._global_buckets[key], RateLimitConfig.GLOBAL_WINDOW_SEC
                )
                if not self._global_buckets[key]:
                    del self._global_buckets[key]
            # Clean search buckets
            for key in list(self._search_buckets.keys()):
                self._search_buckets[key] = self._cleanup_old_entries(
                    self._search_buckets[key], RateLimitConfig.SEARCH_WINDOW_SEC
                )
                if not self._search_buckets[key]:
                    del self._search_buckets[key]

    def check_global_limit(self, request: Request) -> tuple[bool, int]:
        """
        Check global rate limit.
        Returns (allowed, retry_after_seconds).
        """
        try:
            self._maybe_cleanup()
            client_key = self._get_client_key(request)
            now = time.time()

            # Clean and check
            bucket = self._cleanup_old_entries(
                self._global_buckets[client_key], RateLimitConfig.GLOBAL_WINDOW_SEC
            )

            if len(bucket) >= RateLimitConfig.GLOBAL_LIMIT:
                oldest = min(bucket) if bucket else now
                retry_after = (
                    int(RateLimitConfig.GLOBAL_WINDOW_SEC - (now - oldest)) + 1
                )
                return False, max(1, retry_after)

            bucket.append(now)
            self._global_buckets[client_key] = bucket
            return True, 0

        except Exception as e:
            logger.warning(f"Rate limiter error (fail-open): {e}")
            return True, 0  # Fail open

    def check_search_limit(self, request: Request) -> tuple[bool, int]:
        """
        Check search-specific rate limit (stricter).
        Returns (allowed, retry_after_seconds).
        """
        try:
            client_key = self._get_client_key(request)
            now = time.time()

            bucket = self._cleanup_old_entries(
                self._search_buckets[client_key], RateLimitConfig.SEARCH_WINDOW_SEC
            )

            if len(bucket) >= RateLimitConfig.SEARCH_LIMIT:
                oldest = min(bucket) if bucket else now
                retry_after = (
                    int(RateLimitConfig.SEARCH_WINDOW_SEC - (now - oldest)) + 1
                )
                return False, max(1, retry_after)

            bucket.append(now)
            self._search_buckets[client_key] = bucket
            return True, 0

        except Exception as e:
            logger.warning(f"Search rate limiter error (fail-open): {e}")
            return True, 0


# Global rate limiter instance
rate_limiter = InMemoryRateLimiter()


# ────────────────────────────────────────────────────────────────────
# Daily Visitors Tracker (Privacy-safe, in-memory)
# ────────────────────────────────────────────────────────────────────


class DailyVisitorsTracker:
    """
    Track unique daily visitors using hashed IP+UA (no PII stored).
    Resets daily. In-memory for MVP.
    """

    def __init__(self):
        self._current_date: str = ""
        self._visitor_hashes: Set[str] = set()
        self._salt = "cwo2026"  # Simple salt

    def _get_visitor_hash(self, request: Request) -> str:
        """Generate privacy-safe visitor identifier."""
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"

        ua = request.headers.get("user-agent", "")[:50]  # Truncate UA
        raw = f"{ip}:{ua}:{self._salt}"
        return hashlib.sha256(raw.encode()).hexdigest()[:24]

    def record_visit(self, request: Request) -> None:
        """Record a visit (deduplicated by hash)."""
        try:
            today = date.today().isoformat()

            # Reset on new day
            if today != self._current_date:
                self._current_date = today
                self._visitor_hashes.clear()

            visitor_hash = self._get_visitor_hash(request)
            self._visitor_hashes.add(visitor_hash)

        except Exception as e:
            logger.warning(f"Visitor tracking error: {e}")

    def get_count(self) -> tuple[str, int]:
        """Get today's visitor count."""
        today = date.today().isoformat()
        if today != self._current_date:
            return today, 0
        return self._current_date, len(self._visitor_hashes)


# Global visitor tracker
visitor_tracker = DailyVisitorsTracker()


# ────────────────────────────────────────────────────────────────────
# Rate Limiting Middleware
# ────────────────────────────────────────────────────────────────────


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Apply rate limiting. Skipped in dev mode.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip in dev
        if APP_ENV == "dev":
            return await call_next(request)

        path = request.url.path
        method = request.method

        # Check search-specific limit first
        if path == "/api/v1/search" and method == "POST":
            allowed, retry_after = rate_limiter.check_search_limit(request)
            if not allowed:
                logger.warning(f"Search rate limit exceeded for path={path}")
                response = _middleware_error(
                    request,
                    429,
                    "RATE_LIMITED",
                    "Too many search requests. Please wait.",
                )
                response.headers["Retry-After"] = str(retry_after)
                return response

        # Global limit (skip health check)
        if path != "/health":
            allowed, retry_after = rate_limiter.check_global_limit(request)
            if not allowed:
                logger.warning(f"Global rate limit exceeded for path={path}")
                response = _middleware_error(
                    request, 429, "RATE_LIMITED", "Too many requests. Please slow down."
                )
                response.headers["Retry-After"] = str(retry_after)
                return response

        return await call_next(request)


# ────────────────────────────────────────────────────────────────────
# Request Logging Middleware
# ────────────────────────────────────────────────────────────────────


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log request metadata (no PII).
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Record visitor for stats (on main pages)
        if request.url.path in ("/", "/api/v1/search", "/api/v1/meta"):
            visitor_tracker.record_visit(request)

        response = await call_next(request)

        latency_ms = int((time.time() - start_time) * 1000)

        # Log non-health requests
        if request.url.path != "/health":
            logger.info(
                f"{request.method} {request.url.path} "
                f"status={response.status_code} latency={latency_ms}ms"
            )

        return response


# ────────────────────────────────────────────────────────────────────
# Body Size Limit Middleware
# ────────────────────────────────────────────────────────────────────


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Reject requests with body > MAX_BODY_SIZE.
    """

    MAX_BODY_SIZE = 32 * 1024  # 32KB

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only check POST/PUT/PATCH
        if request.method in ("POST", "PUT", "PATCH"):
            content_length = request.headers.get("content-length")
            if content_length:
                try:
                    if int(content_length) > self.MAX_BODY_SIZE:
                        return _middleware_error(
                            request,
                            413,
                            "REQUEST_TOO_LARGE",
                            "Request body too large (max 32KB)",
                        )
                except ValueError:
                    pass

        return await call_next(request)


# ────────────────────────────────────────────────────────────────────
# Cache Headers Middleware
# ────────────────────────────────────────────────────────────────────


class CacheHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add Cache-Control headers to GET responses.
    """

    CACHE_RULES = {
        "/api/v1/meta": "public, max-age=86400",  # 24 hours
        "/api/v1/feature-flags": "public, max-age=300",  # 5 minutes
        "/api/v1/offers": "public, max-age=600",  # 10 minutes
        "/api/v1/stats/daily-visitors": "public, max-age=60",  # 1 minute
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Only add cache headers for GET requests with 200 status
        if request.method == "GET" and response.status_code == 200:
            path = request.url.path
            if path in self.CACHE_RULES:
                response.headers["Cache-Control"] = self.CACHE_RULES[path]
            else:
                # Default: no caching for unknown paths
                response.headers["Cache-Control"] = "no-store"

        return response
