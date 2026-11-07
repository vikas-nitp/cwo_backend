# CardOptimal — Brand & Config

## Active brand name
**CardOptimal** — as of 2026-09-25.

## Single source of truth

`APP_NAME` and `APP_DOMAIN` are defined once in `app/core/config.py`:

```python
APP_NAME = "CardOptimal"
APP_DOMAIN = "cardsage.in"   # placeholder — update when domain locked
```

All other files import from there:

```python
from app.core.config import APP_NAME
app = FastAPI(title=f"{APP_NAME} API", ...)
logger.info(f"Starting {APP_NAME} API (env={APP_ENV})")
```

Do NOT hardcode "CardOptimal", "CardwiseOffer", or "CardSage" anywhere else in the backend. The string "CardwiseOffer" should appear only in legacy comments or historical references — use the constant.

## Domain placeholder

`APP_DOMAIN = "cardsage.in"` and `.env.example` use `cardsage.in` until the final domain is confirmed.

When domain is locked:
1. Update `APP_DOMAIN` in `app/core/config.py`
2. Update `ALLOWED_ORIGINS` in `.env.example`
3. Update the origin in `tests/test_production_hardening.py` (fixture)
4. Update Railway env var `ALLOWED_ORIGINS`

## Previous brand names (historical)

| Name | Era | Status |
|---|---|---|
| CardwiseOffer | Original | Retired |
| CardSage | Sep 2026 rebrand attempt | Retired — name was taken |
| CardOptimal | Current | Active |
