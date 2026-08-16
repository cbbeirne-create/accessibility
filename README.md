# Auditly — Website Accessibility Scanner

Auditly is a web application that performs automated accessibility scans of websites, captures visual evidence, and produces developer and stakeholder-facing reports (JSON and tagged PDFs). It includes a FastAPI backend that performs scans (axe-core + external APIs) and a Create React App frontend for user flows, billing (Stripe) and report export.

## Stack
- Language(s): Python (backend), JavaScript/React (frontend)
- Backend: FastAPI, Motor (MongoDB async client), Playwright for browser-based scans
- Frontend: Create React App, Tailwind CSS
- Notable libraries: FastAPI, Pydantic, Playwright, ReportLab (PDF generation), stripe, sendgrid

## Repository layout
```
backend/        FastAPI app, scan services, API routes, Dockerfile
frontend/       Create React App UI, Tailwind, Dockerfile
app/            helper wrapper (contains frontend/) 
mongodb/        example Mongo setup / scripts
memory/         in-memory test helpers
test_reports/   generated scan/test reports and remediation artifacts
tests/          test suites for backend/frontend
docker-compose.yml
deploy.sh
DEPLOYMENT.md
```

## Quickstart (development)
1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# provide env vars (see Environment) or copy .env.example -> .env
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/api/docs

2. Frontend

```bash
cd frontend
yarn install
yarn start
# or npm install && npm start
```

3. Using docker-compose (both services)

```bash
# from repo root
docker-compose up --build
```

## Environment
Create a backend/.env file (not committed) with at minimum:
```
MONGO_URL=mongodb://localhost:27017
DB_NAME=auditly
SECRET_KEY=<secure random value>
FRONTEND_URL=http://localhost:3000
# Optional for integrations
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
SENDGRID_API_KEY=
WAVE_API_KEY=
EQUALWEB_API_KEY=
ACCESSIBE_API_KEY=
```

Notes:
- Never commit secret keys. Use your platform secret store for production deployments.
- CORS is permissive by default in development; restrict allowed origins in production.

## Running tests
- Backend: run pytest from the repository root or backend directory (tests are under backend/tests and tests/)
- Frontend: `yarn test` inside frontend/

## Deployment
See DEPLOYMENT.md and docker-compose.yml. The project includes Dockerfiles for backend and frontend; review them for production best practices (non-root user, multi-stage builds, pinned base images, environment secrets).

## Outstanding immediate docs items
- Expand DEPLOYMENT.md with environment and production checklist (secrets, TLS, allowed origins, resource sizing).
- Add CONTRIBUTING.md describing code style, tests, and PR process.
- Add a README to `backend/` and `frontend/` with component-level details (entrypoints, major modules).

## Contact / Support
Open issues or PRs in this repository for documentation updates. For quick changes, I can open a PR that adds/updates additional documentation files (CONTRIBUTING.md, backend/README.md, DEPLOYMENT.md updates).
