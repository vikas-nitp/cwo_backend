"""
CardwiseOffer Backend - FastAPI Application

Run with:
    cd cwo_backend && PYTHONPATH=$(pwd) venv/bin/python3 -m uvicorn app.main:app --port 8001 --reload
"""

from contextlib import asynccontextmanager
from pathlib import Path
import re
import uuid
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config import (
    APP_ENV,
    API_PREFIX,
    CORS_ORIGINS,
    OFFERS_SNAPSHOT_PATH,
    METADATA_SNAPSHOT_PATH,
    MANIFEST_PATH,
    FACETS_SNAPSHOT_PATH,
    FEATURE_FLAGS_PATH,
)
from app.core.feature_flags import load_feature_flags
from app.core.logging import setup_logging, get_logger
from app.core.middleware import (
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    BodySizeLimitMiddleware,
    CacheHeadersMiddleware,
)
from app.api.errors import install_error_handlers
from app.api.routes.health import router as health_router
from app.api.routes.meta import router as meta_router
from app.api.routes.offers import router as offers_router
from app.api.routes.search import router as search_router
from app.api.routes.feature_flags import router as feature_flags_router
from app.repositories.file_offer_repository import FileOfferRepository

# Setup logging first
setup_logging()
logger = get_logger("app")

# Disable docs in production
_docs_url = "/docs" if APP_ENV == "dev" else None
_redoc_url = "/redoc" if APP_ENV == "dev" else None
_openapi_url = "/openapi.json" if APP_ENV == "dev" else None


@asynccontextmanager
async def lifespan(application: FastAPI):
    repository = FileOfferRepository(
        Path(OFFERS_SNAPSHOT_PATH),
        Path(METADATA_SNAPSHOT_PATH),
        Path(MANIFEST_PATH),
        Path(FACETS_SNAPSHOT_PATH),
    )
    application.state.offer_repository = repository
    application.state.feature_flags = None
    application.state.feature_flags_error = None
    try:
        repository.load()
        logger.info(
            "Loaded %s offers (data_version=%s)",
            repository.get_manifest().accepted_row_count,
            repository.get_manifest().data_version,
        )
    except Exception as exc:
        logger.exception("Offer snapshot failed to load: %s", exc)
    try:
        flags = load_feature_flags(Path(FEATURE_FLAGS_PATH))
        application.state.feature_flags = flags
        logger.info("Loaded feature flags (config_version=%s)", flags.version())
    except Exception as exc:
        application.state.feature_flags_error = str(exc)
        logger.exception("Feature flags failed to load: %s", exc)
    yield


# Initialize FastAPI app
app = FastAPI(
    title="CardwiseOffer API",
    version="1.1.0",
    description="API for CardwiseOffer - Find best credit card offers",
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url=_openapi_url,
    lifespan=lifespan,
)

# Add middlewares (order matters: first added = outermost)
app.add_middleware(GZipMiddleware, minimum_size=1000)  # Compress responses > 1KB
app.add_middleware(CacheHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(BodySizeLimitMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if APP_ENV == "dev" else CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Request-ID"],
)

logger.info(f"Starting CardwiseOffer API (env={APP_ENV})")
logger.info(f"CORS origins: {CORS_ORIGINS}")


@app.middleware("http")
async def request_id(request, call_next):
    incoming = request.headers.get("x-request-id", "")
    request.state.request_id = (
        incoming
        if re.fullmatch(r"[A-Za-z0-9._:-]{1,64}", incoming)
        else str(uuid.uuid4())
    )
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


install_error_handlers(app)

# API routes
app.include_router(health_router)
app.include_router(meta_router, prefix=API_PREFIX)
app.include_router(offers_router, prefix=API_PREFIX)
app.include_router(search_router, prefix=API_PREFIX)
app.include_router(feature_flags_router, prefix=API_PREFIX)


# ── Development Server ──────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    is_dev = APP_ENV == "dev"

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=is_dev,  # Auto-reload only in dev
        reload_dirs=["app"] if is_dev else None,
        log_level="debug" if is_dev else "info",
    )
