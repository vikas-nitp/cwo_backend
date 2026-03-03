"""
CardwiseOffer Backend - FastAPI Application

Run with:
    cd cwo_backend && PYTHONPATH=$(pwd) venv/bin/python3 -m uvicorn app.main:app --port 8001 --reload
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config import APP_ENV, API_PREFIX, CORS_ORIGINS
from app.core.logging import setup_logging, get_logger
from app.core.middleware import (
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    BodySizeLimitMiddleware,
    CacheHeadersMiddleware,
)
from app.services import load_data
from app.routes import meta_router, offers_router, search_router, auth_router, stats_router

# Setup logging first
setup_logging()
logger = get_logger("app")

# Disable docs in production
_docs_url = "/docs" if APP_ENV == "dev" else None
_redoc_url = "/redoc" if APP_ENV == "dev" else None
_openapi_url = "/openapi.json" if APP_ENV == "dev" else None

# Initialize FastAPI app
app = FastAPI(
    title="CardwiseOffer API",
    version="1.0.0",
    description="API for CardwiseOffer - Find best credit card offers",
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url=_openapi_url,
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
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Load data at startup
logger.info(f"Starting CardwiseOffer API (env={APP_ENV})")
logger.info(f"CORS origins: {CORS_ORIGINS}")
load_data()

# Health check
@app.get("/health")
def health():
    return {"ok": True, "env": APP_ENV}

# API routes
app.include_router(meta_router, prefix=API_PREFIX)
app.include_router(offers_router, prefix=API_PREFIX)
app.include_router(search_router, prefix=API_PREFIX)
app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(stats_router, prefix=API_PREFIX)


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
