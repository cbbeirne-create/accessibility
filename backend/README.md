# Backend — Auditly (FastAPI)

This directory contains the FastAPI-based backend for Auditly: API routes, scanning services (axe-core + Playwright), report exporters (PDF/JSON), authentication, and integrations (Stripe, SendGrid, external scanner APIs).

Quick facts
- Entrypoint (dev): `uvicorn backend.main:app --host 0.0.0.0 --port 8000`
- Entrypoint (production with Gunicorn): `gunicorn -k uvicorn.workers.UvicornWorker backend.main:app -w <workers>`
- Config location: `backend/core/config.py` (loads environment from backend/.env or ROOT_DIR/.env)

Important files
- `backend/main.py` — creates FastAPI app, mounts routers, startup/shutdown hooks (scheduler)
- `backend/server.py` — API routes, Pydantic models, auth helpers, scan orchestration, and exporters
- `backend/core/config.py` — central settings (MONGO_URL, SECRET_KEY, Stripe/SendGrid/API keys)
- `backend/services/` — background services (scheduler, scanner orchestration, PDF generation helpers)
- `backend/models/` — Pydantic models (if present)
- `backend/requirements.txt` — Python dependencies
- `backend/Dockerfile` — container image build for the backend

Environment (minimum)
Create `backend/.env` (do NOT commit):

```
MONGO_URL=mongodb://mongodb:27017
DB_NAME=auditly
SECRET_KEY=<secure-random-value>
FRONTEND_URL=https://your-frontend.example.com
# Optional integrations:
STRIPE_SECRET_KEY=
SENDGRID_API_KEY=
WAVE_API_KEY=
EQUALWEB_API_KEY=
ACCESSIBE_API_KEY=
```

Run locally (development)

1. python -m venv .venv
2. source .venv/bin/activate
3. pip install -r requirements.txt
4. uvicorn backend.main:app --reload

Run tests

- From repo root or `backend/`: `pytest -q` (ensure test DB or mocks are configured; test helpers under `backend/tests` and `tests/`)

Docker (build & run)

- Build: `docker build -t auditly-backend ./backend`
- Run (compose): `docker-compose up --build`

Notes & TODOs
- Tighten CORS in production (backend/main.py uses allow_origins=["*"] currently).
- Replace default SECRET_KEY before production.
- Confirm Playwright browsers cache path (PLAYWRIGHT_BROWSERS_PATH) when running in container; mount a persistent cache path if using Playwright in workers.
- Consider splitting `server.py` into smaller modules (routes, auth, scanning, export) to improve maintainability.
- Add health checks, structured logging, and monitoring integration (Prometheus/Datadog) if deploying at scale.
