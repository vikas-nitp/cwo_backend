# Render and Railway deployment

Use the repository Dockerfile with no pre-deploy database or filesystem migration. Set `APP_ENV=production`, `PORT`, exact `ALLOWED_ORIGINS`, all snapshot/config paths from `.env.example`, and `CONTRACT_VERSION=1.1`.

For Render, select Docker runtime and use `/health/ready` as the health-check path. For Railway, deploy from the Dockerfile and configure the same readiness probe/domain variables. Do not mount a writable data volume; snapshots and feature configuration are immutable image inputs.

After deployment verify:

```bash
curl -fsS https://api.example.com/health/live
curl -fsS https://api.example.com/health/ready
curl -I https://api.example.com/api/v1/meta
```

Readiness must include data, feature-config, and contract versions. Configure frontend preview and production origins explicitly; do not use wildcard production CORS or embed secrets in repository files.
