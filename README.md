# Auditly — accessibility monitoring and remediation

Auditly scans public websites with Playwright and axe-core, records automated accessibility findings and visual evidence, and turns those findings into developer-facing remediation reports. It also supports authenticated workspaces, scheduled scans, scan history/comparison, Stripe subscriptions, notifications, JSON/PDF exports and team accounts.

> **Important:** the Auditly Accessibility Health Score is an automated indicator. It is **not** a WCAG conformance percentage, certification, or substitute for manual accessibility testing.

## Architecture

```text
frontend/                 React 19 + Vite SPA served by Nginx
backend/main.py           FastAPI API only
backend/worker.py         dedicated queue + scheduler process
backend/services/         scanner, queue, entitlements, storage, reports
MongoDB                   users, scans, sessions, durable queue, scheduler leases
S3-compatible storage     optional/recommended screenshot evidence storage
```

Browser scans do not run inside the FastAPI request process. API requests enqueue durable jobs in MongoDB and the worker atomically claims them.

## Security model

The hardened application includes:

- short-lived JWT access tokens kept only in browser memory;
- rotating HttpOnly refresh-token sessions with server-side revocation;
- explicit production CORS origins and security headers;
- verified-email requirement before expensive scans;
- atomic plan/quota enforcement;
- authenticated, organization-scoped scan access;
- SSRF checks on initial navigation **and browser subrequests**;
- private/loopback/link-local/reserved network blocking;
- dedicated non-root Playwright worker;
- rate limiting for authentication and scan creation;
- Stripe webhook signature verification and event idempotency;
- MongoDB not exposed on a host port by the supplied Compose stack;
- local pinned axe-core rather than runtime CDN injection.

Infrastructure-level egress restrictions are still recommended for the browser worker as a second SSRF/isolation layer.

## Development

### Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

export MONGO_URL=mongodb://localhost:27017
export DB_NAME=auditly
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(48))")

uvicorn backend.main:app --reload --port 8000
```

The browser worker is a separate process:

```bash
python -m backend.worker
```

The backend Docker image vendors axe-core automatically. For a non-Docker local backend, install the pinned browser script in `backend/node_modules`:

```bash
cd backend
npm install
cd ..
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Vite runs on port 3000 and proxies `/api` to `http://localhost:8000` in development.

### Docker Compose

Create a `.env` containing at least a secure `SECRET_KEY`, then:

```bash
docker compose build
docker compose up
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for the full production configuration, HTTPS/cookie requirements, object storage and worker-isolation guidance.

## Environment variables

Core settings:

```text
ENVIRONMENT=development|production
MONGO_URL=
DB_NAME=
SECRET_KEY=
FRONTEND_URL=
CORS_ALLOWED_ORIGINS=
COOKIE_SECURE=true|false
ACCESS_TOKEN_EXPIRE_MINUTES=20
REFRESH_TOKEN_EXPIRE_DAYS=30
MAX_CONCURRENT_SCANS=2
```

Optional integrations:

```text
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_PRO_PRICE_ID=
SENDGRID_API_KEY=
SENDER_EMAIL=
WAVE_API_KEY=
EQUALWEB_API_KEY=
ACCESSIBE_API_KEY=
S3_BUCKET=
S3_REGION=
S3_ENDPOINT_URL=
S3_PUBLIC_BASE_URL=
```

## Tests and CI

Backend regression tests:

```bash
pytest -q backend/tests/test_security_primitives.py
```

Frontend production build:

```bash
cd frontend
npm run build
```

`.github/workflows/ci.yml` runs backend compilation/tests, the frontend Vite build, and production Docker image builds on pushes and pull requests.

## API health endpoints

- `/api/health/live` — process liveness only
- `/api/health/ready` — database readiness
- `/api/health` — backward-compatible readiness alias

Health probes deliberately do not launch Chromium.

## Scanner/report behaviour

Auditly records axe-core failures, passes and incomplete/manual-review findings. For violations, reports can include:

- impact/severity;
- WCAG/axe tags;
- affected selectors;
- affected DOM HTML;
- axe failure summaries;
- remediation guidance;
- issue and full-page screenshots;
- scan history and before/after comparison.

Screenshots use S3-compatible object storage when configured. A Base64-in-Mongo fallback remains for development/small installations only.

## Repository layout

```text
backend/
  api/routes/       FastAPI route modules
  core/             config, database, auth primitives
  models/           Pydantic models
  services/         scanner, queue, scheduler, storage, reports
  tests/            backend regression tests
  main.py           API entrypoint
  worker.py         queue/scheduler worker entrypoint
frontend/
  src/              React application
  nginx.conf        production SPA/API proxy
.github/workflows/  CI
docker-compose.yml
DEPLOYMENT.md
```

`backend/server.py` is retained only as a compatibility import that forwards to `backend.main:app`; the old monolithic implementation is no longer present.
