#!/bin/bash

# Production deployment script for Accessibility Scanner
set -e

echo "🚀 Starting Accessibility Scanner deployment..."

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
mkdir -p ./backend/reports
mkdir -p ./logs

# Build and start services
echo "📦 Building Docker images..."
docker-compose build --no-cache

echo "🔄 Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 30

# Check service health
echo "🔍 Checking service health..."
for i in {1..10}; do
    if curl -s http://localhost:8000/api/health | grep -q "healthy"; then
        echo "✅ Backend service is healthy"
        break
    else
        echo "⏳ Waiting for backend service... ($i/10)"
        sleep 10
    fi
done

if curl -s http://localhost/health | grep -q "healthy"; then
    echo "✅ Frontend service is healthy"
else
    echo "⚠️  Frontend service might not be ready yet"
fi

echo ""
echo "🎉 Accessibility Scanner deployed successfully!"
echo ""
echo "🌐 Access the application at:"
echo "   Frontend: http://localhost"
echo "   Backend API: http://localhost:8000"
echo "   API Documentation: http://localhost:8000/api/docs"
echo "   Health Check: http://localhost:8000/api/health"
echo ""
echo "📊 Monitor logs with:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 Stop services with:"
echo "   docker-compose down"