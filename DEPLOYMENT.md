# Accessibility Scanner - Production Deployment Guide

## Quick Start with Docker

### Prerequisites
- Docker 20.0+
- Docker Compose 2.0+
- 4GB+ RAM (8GB recommended for Playwright workers)
- 10GB+ disk space (more if storing reports/screenshots)

### 1. Deploy the Application (example)

```bash
# Clone the project
git clone https://github.com/cbbeirne-create/accessibility.git
cd accessibility

# Create a branch for any local changes
git checkout -b deploy/local

# Make deployment script executable
chmod +x deploy.sh

# Example (dependent on your environment) - deploy with docker-compose
./deploy.sh
# or
docker-compose up -d --build
```

### 2. Access the Application

- Frontend: https://your-domain.com (or http://localhost for local testing)
- Backend API: https://your-domain.com/api or http://localhost:8000
- API Documentation: https://your-domain.com/api/docs
- Health Check: https://your-domain.com/api/health

---

## Production Configuration (checklist)
Follow this checklist when preparing a production deployment.

1. Secrets & configuration
   - Do NOT commit `.env` files to source control.
   - Use a secrets manager (AWS Secrets Manager, HashiCorp Vault, GitHub Actions secrets, Kubernetes Secrets) to inject runtime secrets.
   - Required secrets:
     - MONGO_URL
     - DB_NAME
     - SECRET_KEY (strong, random; rotate periodically)
     - STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET (if billing enabled)
     - SENDGRID_API_KEY (email)
     - PLAYWRIGHT_BROWSERS_PATH (optional persistent cache path)
2. TLS/HTTPS
   - Terminate SSL at the edge (load balancer or reverse proxy like Nginx / Cloudflare).
   - Use Let’s Encrypt or your CA-managed certificates.
   - Ensure backend and frontend URLs use HTTPS in production env vars (FRONTEND_URL).
3. Network & firewall
   - Restrict MongoDB access to the application network only.
   - Only expose required ports (80/443 to frontend, backend behind internal LB at 8000).
4. CORS & allowed origins
   - Replace permissive CORS (allow_origins=["*"]) with a specific list of allowed origins in production.
5. Rate limiting and abuse protection
   - Add an API gateway or reverse proxy layer to implement rate limits and IP throttling if public.
6. Monitoring & alerting
   - Instrument app logs and metrics (structured logs, request ids) and export to a logging/metrics backend (e.g. ELK, Datadog, Prometheus + Grafana).
   - Alert on failed health checks, high error rates, or scan worker failures.
7. Backups & retention
   - Schedule MongoDB backups (mongodump or managed backups). Keep off-site copies and retention policy.
   - Store backups in a secure, access-controlled location (S3 bucket with versioning and lifecycle rules).
8. Resource sizing
   - Playwright browsers are CPU and memory hungry. For production scanning at scale, run Playwright in separate worker containers with dedicated CPU/memory. Recommend per worker: 1-2 vCPU, 2-4GB RAM minimal; increase for heavy pages/screenshots.
9. Security hardening
   - Run containers as non-root users.
   - Keep base images up to date and pin base image versions where possible.
   - Enable dependency vulnerability scanning (Dependabot, Snyk, etc.).
10. CI / CD
   - Require passing CI checks and code review before merging to protected main branch.

---

## Environment files
Create environment files or wire secrets from your platform. Example (backend `.env`):

```bash
MONGO_URL=mongodb://mongodb:27017
DB_NAME=accessibility_scanner
SECRET_KEY=replace-with-secure-random
FRONTEND_URL=https://your-domain.com
PLAYWRIGHT_BROWSERS_PATH=/home/scanner/.cache/ms-playwright

# Optional: External API Keys
WAVE_API_KEY=
EQUALWEB_API_KEY=
ACCESSIBE_API_KEY=
# Stripe / SendGrid
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=
SENDGRID_API_KEY=
SENDER_EMAIL=
```

Frontend `.env` (CRA):

```bash
REACT_APP_BACKEND_URL=https://your-domain.com
```

Notes:
- Avoid storing secrets in plaintext in your repository. Use your platform's secret injection
mechanism or Docker/Kubernetes secrets.

---

## Docker & Playwright considerations
- Use multi-stage Docker builds for smaller production images.
- Run Playwright with a persistent browsers cache (PLAYWRIGHT_BROWSERS_PATH) mounted to host or a persistent volume to avoid re-downloading browsers on each container start.
- For Playwright in Docker, ensure necessary OS dependencies are installed (see Playwright docs).
- Run Playwright workers separately from the API server when scanning at scale to isolate resource usage.

Example docker-compose snippet (production-like, use secrets):

```yaml
services:
  frontend:
    image: your-frontend-image:latest
    ports:
      - "80:80"
      - "443:443"
    environment:
      - REACT_APP_BACKEND_URL=${REACT_APP_BACKEND_URL}
    volumes:
      - ./ssl:/etc/nginx/ssl:ro
    deploy:
      resources:
        limits:
          cpus: '0.50'
          memory: 512M

  backend:
    image: your-backend-image:latest
    environment:
      - MONGO_URL=${MONGO_URL}
      - DB_NAME=${DB_NAME}
      - SECRET_KEY=${SECRET_KEY}
    ports:
      - "8000:8000"
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
    restart: "on-failure"

  playwright-worker:
    image: your-backend-image:latest
    command: ["python", "-m", "backend.services.worker"]
    environment:
      - PLAYWRIGHT_BROWSERS_PATH=/home/scanner/.cache/ms-playwright
    volumes:
      - playwright_cache:/home/scanner/.cache/ms-playwright
    deploy:
      replicas: 1
      resources:
        limits:
          cpus: '1.0'
          memory: 2G

volumes:
  playwright_cache:
```

---

## Backups & restores (examples)
- Backup with mongodump:

```bash
docker exec mongodb_container_name mongodump --archive=/backup/backup-$(date +%F).gz --gzip --db=${DB_NAME}
# copy backup from container to host
docker cp mongodb_container_name:/backup/backup-$(date +%F).gz ./backups/
```

- Restore with mongorestore:

```bash
docker cp ./backups/backup-2023-01-01.gz mongodb_container_name:/backup/
docker exec -i mongodb_container_name mongorestore --archive=/backup/backup-2023-01-01.gz --gzip --db=${DB_NAME}
```

---

## Health checks & monitoring
- Backend health endpoint: `/api/health` (returns database & playwright status)
- Integrate health checks into your load balancer/cluster orchestration (Kubernetes liveness/readiness or Docker healthcheck)
- Capture logs (stdout/stderr) and ship to a log backend; consider structured JSON logs for easier parsing.

---

## Security checklist before going live
- Set a strong SECRET_KEY and rotate periodically.
- Replace placeholder Stripe/price ids and confirm webhook secret configuration.
- Restrict CORS to allowed origins.
- Configure rate-limiting and authentication protections on public endpoints.
- Run dependency vulnerability scans and fix critical/high issues.

---

## Support & troubleshooting
If deployment fails or behaves unexpectedly:
1. Check container logs: `docker-compose logs -f <service>`
2. Verify environment variables and secrets are present in the runtime environment
3. Check health endpoint `/api/health` for dependency errors
4. Verify MongoDB connectivity and indexes


