# Backend deployment skill

**Date:** 2026-07-11
**Purpose:** Package and verify a read-only, file-backed FastAPI deployment.

## Previous behavior

The Procfile started Uvicorn but the service depended on absent Excel files and had no image build or readiness contract.

## New architecture

CI validates CSV, snapshots, contracts, tests, and Docker. The container starts Uvicorn and reads committed snapshots once.

## Files changed

Added `Dockerfile`, `.dockerignore`, `.env.example`, and `.github/workflows/ci.yml`; updated requirements and runtime configuration.

## Configuration

Set `APP_ENV`, `PORT`, `ALLOWED_ORIGINS`, snapshot path, booking window, and supported platforms. No secrets are embedded.

## Test procedure

Run `docker build -t cwo-backend .`, start the container, then query `/health/live` and `/health/ready`.

## Deployment notes

Render or Railway can use the Dockerfile. Configure a health check against `/health/ready` and deploy only after CI passes.

## Known limitations

The in-memory rate limiter is per process and unsuitable for precise multi-replica enforcement.

## Future migration path

Move distributed operational state to managed infrastructure when scaling beyond a single process; offer repository migration remains independent.
