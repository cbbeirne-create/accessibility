FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    AXE_CORE_PATH=/app/backend/node_modules/axe-core/axe.min.js

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl nodejs npm \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt && \
    playwright install --with-deps chromium && \
    chmod -R a+rX /ms-playwright

COPY backend/package.json /app/backend/package.json
RUN cd /app/backend && npm install --omit=dev --no-audit --no-fund

COPY backend /app/backend

RUN useradd --create-home --uid 10001 scanner && chown -R scanner:scanner /app
USER scanner

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://localhost:8000/api/health/live || exit 1

CMD ["gunicorn", "backend.main:app", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "60"]
