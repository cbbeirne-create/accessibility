# Auditly — Website Accessibility Monitoring

Auditly is a SaaS application for automated website accessibility testing, evidence capture, remediation guidance, trend tracking, scheduled monitoring, team collaboration and report export.

Auditly uses axe-core for automated checks and produces an **Auditly Accessibility Health Score** to help teams prioritise work. The score is not a WCAG conformance percentage or certification, and automated testing does not replace manual accessibility review.

## Architecture

```text
React frontend
      |
      v
FastAPI API  ----> MongoDB
      |                |
      | enqueue        | durable jobs / schedules / auth state
      v                |
 Scan queue <----------+
      |
      v
Playwright worker(s)
      |
      +--> axe-core
      +--> optional S3-compatible evidence storage
```

The API does not execute untrusted browser scans inside request handlers. Manual and scheduled scans are placed on a durable Mongo-backed queue and processed by dedicated workers with leases and retries.

## Stack

- **Backend:** Python, FastAPI, Motor/MongoDB
- **Scanner:** Playwright + pinned axe-core
- **Frontend:** React, React Router, Tailwind CSS
- **Billing:** Stripe
- **Email:** SendGrid
- **Reports:** JSON and PDF
- **Evidence:** inline development storage or optional S3-compatible object storage
- **Deployment:** Docker Compose with separate API and scan-worker services

## Core product capabilities

- Authenticated accessibility scans
- SSRF-resistant public URL validation
- Visual evidence capture
- Affected DOM selectors and HTML snippets
- WCAG/axe rule references and remediation guidance
- Scan history and comparisons
- Scheduled monitoring
- Team/organization workspaces
- Free/Pro entitlements
- Stripe subscriptions
- Email verification and password reset
- JSON/PDF export
- Durable worker queue with retries

## Repository layout

```text
backend/
  api/              FastAPI routes
  core/             configuration, database, security, rate limiting
  models/           Pydantic data models
  services/         scanning, queue, entitlements, email, reports, storage
  tests/            backend tests
  worker.py         dedicated scan-worker process
frontend/
  src/              React application
mongodb/             initialization/index definitions
.github/workflows/   CI
DEPLOYMENT.md        production deployment and security checklist
docker-compose.yml
.env.example
```

## Local development with Docker

1. Copy the environment template:

```bash
cp .env.example .env
```

2. Replace `SECRET_KEY` with a strong value of at least 32 characters:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

3. Start the stack:

```bash
docker compose up --build
```

Default local endpoints:

- Frontend: `http://localhost`
- API: `http://localhost:8000`
- API docs: `http://localhost:8000/api/docs`
- Liveness: `http://localhost:8000/api/health/live`
- Readiness: `http://localhost:8000/api/health/ready`

MongoDB is deliberately not published to the host by the supplied Compose configuration.

## Backend development

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
export SECRET_KEY="replace-with-a-long-random-development-secret"
uvicorn backend.main:app --reload --port 8000
```

Run a worker separately:

```bash
python -m backend.worker
```

For non-container development, the scanner can use the pinned axe-core CDN fallback if `backend/vendor/axe.min.js` is absent. Production images vendor the same pinned axe-core version at build time and do not depend on the CDN during scans.

## Frontend development

```bash
cd frontend
corepack enable
yarn install --frozen-lockfile
REACT_APP_BACKEND_URL=http://localhost:8000 yarn start
```

## Tests and CI

The pull-request CI workflow:

- installs backend dependencies
- compiles backend Python modules
- runs security-focused unit tests
- installs frontend dependencies from `yarn.lock`
- performs a production frontend build

Locally:

```bash
pytest -q backend/tests/unit
cd frontend && yarn build
```

## Security model

The hardened application includes:

- no default JWT signing secret
- 15-minute access tokens with issuer/audience/JTI claims
- rotating opaque refresh tokens in Secure/HttpOnly cookies
- refresh-token hashing, revocation and TTL cleanup
- verified-email gating for scan execution
- tenant-scoped scan access
- atomic usage quota reservation
- SSRF protections on initial navigation and browser HTTP(S) subrequests
- browser sandbox retained
- configured CORS rather than wildcard origins
- sensitive-route rate limiting
- Stripe webhook signature validation and event idempotency
- non-public MongoDB networking
- optional encrypted S3-compatible screenshot storage
- dedicated scan workers with durable queue leases/retries

See [DEPLOYMENT.md](DEPLOYMENT.md) for the production checklist and environment contract.

## Accessibility product note

No automated scanner can determine complete WCAG conformance. Auditly should be used to identify and prioritise machine-detectable issues, preserve evidence, guide remediation, and monitor regressions. Manual keyboard, screen-reader, zoom/reflow, cognitive/usability and assistive-technology testing remain necessary for a complete accessibility assessment.
