# Auditly — Production Deployment Guide

Auditly is composed of four runtime services: the React frontend, the FastAPI API, a dedicated Playwright scan worker, and MongoDB. Browser scans are queued durably in MongoDB and executed by workers rather than inside API requests.

## Prerequisites

- Docker Engine 24+
- Docker Compose v2
- At least 4 GB RAM for a small deployment; 8 GB+ is preferable when running multiple scan workers
- A public HTTPS domain and reverse proxy/load balancer for production
- Stripe and SendGrid credentials if billing/email features are enabled
- Optional S3-compatible object storage for screenshot evidence

## 1. Configure environment

Copy the repository template and replace the development values:

```bash
cp .env.example .env
```

Generate a strong application secret, for example:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

For production, the minimum security-sensitive values are:

```bash
ENVIRONMENT=production
SECRET_KEY=<at-least-32-random-characters>
FRONTEND_URL=https://app.example.com
ALLOWED_ORIGINS=https://app.example.com
REFRESH_COOKIE_SECURE=true
REACT_APP_BACKEND_URL=https://api.example.com
```

`SECRET_KEY` has no fallback. The API intentionally refuses to start if it is missing or too short. Production also refuses wildcard CORS, a non-HTTPS frontend URL, or insecure refresh cookies.

### Billing

```bash
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_PRO_PRICE_ID=
```

Configure Stripe to deliver subscription/invoice webhooks to:

```text
https://api.example.com/api/subscription/webhook
```

Webhook event IDs are stored and deduplicated, so Stripe retries are safe.

### Email

```bash
SENDGRID_API_KEY=
SENDER_EMAIL=noreply@example.com
```

Password reset, verification, and team invitation links are never written to application logs.

### Screenshot evidence storage (recommended for production)

Without an object-store bucket, screenshots remain inline in MongoDB for backwards-compatible development. For production, configure an S3-compatible bucket so large PNG evidence does not consume MongoDB document space:

```bash
EVIDENCE_S3_BUCKET=auditly-evidence
EVIDENCE_S3_PREFIX=auditly-evidence
AWS_REGION=eu-west-1
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
# For R2/MinIO/etc. only:
S3_ENDPOINT_URL=
```

Objects are uploaded with server-side AES-256 encryption when this mode is enabled.

## 2. Build and start

```bash
docker compose up -d --build
```

Services:

- `frontend`: static React application served by Nginx
- `backend`: FastAPI/Gunicorn API and lightweight scheduler
- `worker`: dedicated Playwright/axe-core job worker
- `mongodb`: internal database, not published to the host network

The production backend image runs as a non-root user. Chromium's sandbox is not disabled. A pinned axe-core 4.8.2 bundle is downloaded at image-build time and injected locally during production scans, avoiding a runtime CDN dependency.

## 3. TLS and network boundary

The Compose file exposes the frontend on port 80 and API on port 8000 for local/self-hosted use. In production, place both behind a TLS-terminating reverse proxy/load balancer such as Cloudflare, Caddy, Traefik, Nginx, an AWS ALB, or the equivalent on your hosting platform.

Do **not** publish MongoDB port 27017. The supplied Compose configuration deliberately leaves Mongo reachable only over the internal Docker network.

Only public HTTP/HTTPS targets on the configured allowed ports can be scanned. The scanner rejects localhost, private, link-local, reserved, multicast and metadata-address targets and applies the same policy to browser subrequests.

## 4. Health checks

- `GET /api/health/live` — process liveness only
- `GET /api/health/ready` — readiness including MongoDB connectivity
- `GET /api/health` — backwards-compatible readiness alias

Health probes intentionally do not launch Chromium.

API documentation is available in non-production environments at `/api/docs` and `/api/redoc`; it is disabled when `ENVIRONMENT=production`.

## 5. Scaling scans

Scale browser capacity independently from API traffic:

```bash
docker compose up -d --scale worker=3
```

The Mongo-backed queue uses leases and retries. A worker crash does not lose a queued scan, and a completed scan is not re-run merely because a worker died before acknowledging the job. Scheduled jobs are also claimed with leases, preventing multiple API instances from executing the same due schedule.

The API can likewise be replicated behind a load balancer. The built-in sensitive-route rate limiter is process-local; for a large horizontally scaled deployment, replace its backing store with Redis or an edge/WAF rate limiter while retaining the endpoint policy.

## 6. Database indexes and upgrades

The API and scan worker call `ensure_indexes()` at startup, so security, tenancy, TTL, queue, and idempotency indexes are applied to existing databases as well as fresh Docker volumes.

Refresh-token documents use a Mongo TTL index and are automatically expired. Stripe events and scheduled scan result notifications have uniqueness constraints for idempotency.

Before a production upgrade:

```bash
docker compose pull
docker compose build --no-cache
docker compose up -d
```

Review logs after startup:

```bash
docker compose logs -f backend worker
```

## 7. Backups

Back up MongoDB on a schedule appropriate to your retention requirements. Example for a local container:

```bash
docker compose exec mongodb mongodump --db accessibility_scanner --archive=/tmp/auditly.archive --gzip
```

Copy the archive to durable storage and periodically test restoration. If screenshot evidence uses S3-compatible storage, configure versioning/lifecycle/backup policies there separately.

## 8. Security checklist before public launch

- Production `SECRET_KEY` generated and stored in the platform secret store
- HTTPS enforced for frontend and API
- `REFRESH_COOKIE_SECURE=true`
- `ALLOWED_ORIGINS` contains only intended frontend origins
- MongoDB is not internet-accessible
- Stripe webhook secret configured and endpoint registered
- SendGrid sender verified
- Object storage configured for evidence if scans may generate large screenshots
- Infrastructure/edge rate limiting configured for scaled deployments
- Regular dependency/container updates enabled
- Database and object-store backups tested
- Monitoring/error reporting connected to your chosen provider

## 9. Operational notes

Auditly's score is the **Auditly Accessibility Health Score**. It summarizes automated findings and is not a WCAG conformance percentage or certification. Automated testing cannot detect every accessibility issue; manual review remains necessary.

Useful commands:

```bash
# Service status
docker compose ps

# Logs
docker compose logs -f backend worker frontend

# Restart scan workers
docker compose restart worker

# Scale workers
docker compose up -d --scale worker=3

# Stop without deleting data
docker compose down

# Destructive: stop and delete the MongoDB volume
docker compose down -v
```
