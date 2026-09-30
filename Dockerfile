FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 APP_ENV=production PORT=8000 USER_DATA_DIR=/app/data
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app app
COPY data data
COPY scripts scripts
COPY logging.yaml .
# data/generated is gitignored, so build the snapshots from data/source into the image
RUN python scripts/build_data_bundle.py \
    && mkdir -p data/user_cards data/subscriptions logs/archive
RUN useradd --no-create-home --shell /bin/false appuser \
    && chown -R appuser /app/data/user_cards /app/data/subscriptions /app/logs
USER appuser
EXPOSE 8000
# Single worker: rate limiting, visitor counts and file stores are per-process.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
