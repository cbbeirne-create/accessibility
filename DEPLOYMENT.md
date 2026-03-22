# Accessibility Scanner - Production Deployment Guide

## Quick Start with Docker

### Prerequisites
- Docker 20.0+
- Docker Compose 2.0+
- 4GB+ RAM
- 10GB+ disk space

### 1. Deploy the Application

```bash
# Clone or extract the project
cd accessibility-scanner

# Make deployment script executable
chmod +x deploy.sh

# Deploy the application
./deploy.sh
```

### 2. Access the Application

- **Frontend**: http://localhost
- **Backend API**: http://localhost:8000  
- **API Documentation**: http://localhost:8000/api/docs
- **Health Check**: http://localhost:8000/api/health

### 3. Production Configuration

#### Environment Variables

Create `.env` files for production:

**Backend (.env)**:
```bash
MONGO_URL=mongodb://mongodb:27017
DB_NAME=accessibility_scanner
PLAYWRIGHT_BROWSERS_PATH=/home/scanner/.cache/ms-playwright

# Optional: External API Keys
WAVE_API_KEY=your_wave_api_key
EQUALWEB_API_KEY=your_equalweb_api_key
ACCESSIBE_API_KEY=your_accessibe_api_key
```

**Frontend (.env)**:
```bash
REACT_APP_BACKEND_URL=https://your-domain.com
```

#### SSL/HTTPS Setup

For production with SSL, update `docker-compose.yml`:

```yaml
frontend:
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./ssl:/etc/nginx/ssl
    - ./nginx-ssl.conf:/etc/nginx/conf.d/default.conf
```

## Architecture Overview

### Services
- **Frontend**: React SPA with Nginx (Port 80)
- **Backend**: FastAPI with Gunicorn (Port 8000) 
- **Database**: MongoDB 7.0 (Port 27017)

### Key Features
- Professional accessibility scanning with axe-core
- Visual evidence capture with Playwright
- PDF and JSON export functionality
- User tracking and scan history
- Comprehensive WCAG remediation guidance

### Health Monitoring

All services include health checks:
- `/health` - Frontend health
- `/api/health` - Backend and dependencies
- MongoDB ping monitoring

### Data Persistence

- MongoDB data: `mongodb_data` volume
- Scan reports: `./backend/reports` directory
- Application logs: Docker container logs

## Management Commands

```bash
# View logs
docker-compose logs -f [service_name]

# Restart specific service
docker-compose restart [service_name]

# Update application
docker-compose build --no-cache
docker-compose up -d

# Backup database
docker exec mongodb mongodump --db accessibility_scanner --out /backup

# Scale backend workers
docker-compose up -d --scale backend=3

# Stop all services
docker-compose down

# Remove all data (CAUTION)
docker-compose down -v
```

## Performance Tuning

### Backend Scaling
- Adjust Gunicorn workers in Dockerfile
- Scale backend containers with Docker Compose
- Monitor resource usage with health checks

### Database Optimization
- MongoDB indexes are automatically created
- Regular database backups recommended
- Monitor collection sizes and performance

### Security Best Practices
- Use environment variables for sensitive data
- Enable SSL/TLS in production
- Implement rate limiting if needed
- Regular security updates

## API Documentation

Once deployed, comprehensive API documentation is available at:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## Support

For issues or questions:
1. Check health endpoints for service status
2. Review Docker container logs
3. Verify environment configuration
4. Test with minimal scan first