# Auditly production deployment guide

Auditly is deployed as four logical services: the React/Vite frontend, the FastAPI API, a dedicated scan/scheduler worker, and MongoDB. Browser scanning is intentionally kept out of the API process.

## Production prerequisites

- Docker Engine 24+ and Docker Compose v2, or equivalent managed container platform.
- HTTPS termination in front of the frontend/API.
- At least 4 GB RAM for a small installation; increase memory as scan concurrency grows.
- A strong application secret and production email/payment credentials where those features are enabled.
- Recommended: S3-compatible object storage for screenshots (AWS S3, Cloudflare R2, Backblaze B2, etc.).

## Required environment

Create a `.env` alongside `docker-compose.yml`. Do not commit it.

```bash
ENVIRONMENT=production
SECRET_KEY=<at-least-32-random-characters>
FRONTEND_URL=https://auditly.example.com
CORS_ALLOWED_ORIGINS=https://auditly.example.com
COOKIE_SECURE=true

# Payments, if enabled
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_PRO_PRICE_ID=

# Email, if enabled
SENDGRID_API_KEY=
SENDER_EMAIL=noreply@auditly.example.com

# Optional external scanners
WAVE_API_KEY=
EQUALWEB_API_KEY=
ACCESSIBE_API_KEY=

# Recommended screenshot/object storage
S3_BUCKET=
S3_REGION=
S3_ENDPOINT_URL=
S3_PUBLIC_BASE_URL=

# Worker capacity. Start small and measure memory use.
MAX_CONCURRENT_SCANS=2

# Same-origin is recommended. Leave blank when Nginx proxies /api.
VITE_BACKEND_URL=
```

Generate `SECRET_KEY` with a cryptographically secure generator, for example:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

The API deliberately refuses to start in production if the secret is missing/weak or if CORS contains `*`.

## Start the stack

```bash
docker compose build
docker compose up -d
```

Local endpoints with the supplied Compose file:

- Frontend: `http://localhost`
- API: `http://localhost:8000`
- Liveness: `http://localhost:8000/api/health/live`
- Readiness: `http://localhost:8000/api/health/ready`

OpenAPI/Swagger documentation is disabled when `ENVIRONMENT=production`. It remains available in development.

## Architecture

```text
Browser
  │
  ├── /              → Nginx + Vite SPA
  └── /api/*         → FastAPI
                         │
                         ├── MongoDB (metadata, sessions, queue)
                         └── durable scan job queue
                                      │
                                      ▼
                              dedicated worker
                                      │
                              Playwright + axe-core
                                      │
                              S3/R2 screenshots (recommended)
```

MongoDB is intentionally not published on a host port by `docker-compose.yml`.

## HTTPS and cookies

Production refresh tokens are HttpOnly cookies. Put the public site behind HTTPS and set `COOKIE_SECURE=true`. TLS termination can live at a cloud load balancer, reverse proxy, CDN, or ingress controller. Do not expose a production login over plain HTTP.

If frontend and API are deployed on separate origins, set both `FRONTEND_URL` and `CORS_ALLOWED_ORIGINS` explicitly and review the cookie `SameSite`/domain configuration. Same-origin `/api` proxying is simpler and preferred.

## Browser-worker isolation

The scan worker opens untrusted third-party pages. Keep it isolated from sensitive infrastructure:

- run it as a non-root user (the supplied image does this);
- do not give the worker Docker socket or host filesystem mounts;
- limit outbound network access where your platform supports egress policies;
- deny private/link-local networks at the network/firewall layer as an additional SSRF control;
- keep worker secrets to the minimum required;
- scale workers separately from the API.

The application also performs DNS/IP and per-request SSRF checks, but infrastructure egress controls are recommended as a second layer, particularly against DNS rebinding and browser/network-stack edge cases.

## Object storage

When `S3_BUCKET` is configured, full-page and issue screenshots are stored outside MongoDB. The adapter supports standard S3 and S3-compatible endpoints. Without object storage, development installations retain a Base64 fallback in MongoDB; that fallback is not recommended for sustained production usage because screenshots can make documents large.

If `S3_PUBLIC_BASE_URL` is omitted, screenshots remain retrievable by the authenticated API using their storage keys. If you use a public base URL, ensure the bucket/content is appropriate for public access before setting it.

## Stripe

Configure the webhook endpoint as:

```text
https://auditly.example.com/api/subscription/webhook
```

Webhook signatures are verified and event IDs are stored to make processing idempotent. Failed processing removes the event marker so Stripe can safely retry it.

## Health and scaling

- `/api/health/live` checks only the API process.
- `/api/health/ready` checks MongoDB readiness.
- Health probes deliberately do not launch Chromium.

Scale API instances and scan workers independently. The scheduler uses Mongo leases and the queue uses atomic job claiming, so multiple worker replicas do not intentionally run the same due job.

Example:

```bash
docker compose up -d --scale worker=3
```

`MAX_CONCURRENT_SCANS` controls concurrent browser jobs *inside each worker container*. Keep the product of replicas × concurrency within available memory/CPU.

## Backups

Back up MongoDB and any object-storage bucket. A simple local Mongo backup example is:

```bash
docker compose exec mongodb mongodump --db accessibility_scanner --archive=/tmp/auditly.archive
```

For managed production infrastructure, prefer automated encrypted backups with tested restores and retention policies.

## Security checklist before launch

- `ENVIRONMENT=production`
- unique `SECRET_KEY` stored in the platform secret manager
- HTTPS enabled and `COOKIE_SECURE=true`
- explicit CORS origin(s), never `*`
- MongoDB not public
- worker cannot reach private infrastructure where egress controls are available
- Stripe webhook secret configured if billing is enabled
- verified SendGrid sender/domain if email is enabled
- object storage configured for scan evidence
- CI is passing
- database backups enabled and restore tested
- dependency/security update process established

## Score and compliance wording

The score shown by Auditly is the **Auditly Accessibility Health Score**, derived from automated findings. It is not a WCAG conformance percentage or certification. Automated testing cannot evaluate every WCAG success criterion, so production reports should be paired with appropriate manual testing when a formal accessibility assessment is required.
