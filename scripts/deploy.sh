#!/bin/bash
set -e

echo "🚀 Deploying PDF2MD stack..."
echo ""

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found"
    echo "   Please run this script from the project root directory"
    exit 1
fi

# Pull latest code
echo "📥 Pulling latest code from git..."
git pull origin main

# Backup database before deployment
echo "📦 Creating backup..."
./scripts/backup.sh

# Build new images
echo "🏗️  Building new Docker images..."
docker-compose build --no-cache

# Stop old containers
echo "🛑 Stopping old containers..."
docker-compose down

# Start new containers
echo "🚀 Starting new containers..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 15

# Check health endpoint
echo "🏥 Checking application health..."
MAX_RETRIES=10
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f http://localhost/health > /dev/null 2>&1; then
        echo "✅ Health check passed!"
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "   Attempt $RETRY_COUNT/$MAX_RETRIES..."
    sleep 3
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ Health check failed after $MAX_RETRIES attempts!"
    echo "🔄 Rolling back to previous version..."
    ./scripts/rollback.sh
    exit 1
fi

# Clean up old images
echo "🧹 Cleaning up old Docker images..."
docker image prune -f

# Show running containers
echo ""
echo "📊 Running containers:"
docker-compose ps

echo ""
echo "✅ Deployment successful!"
echo "🎉 PDF2MD stack is now running"
echo ""
echo "📍 Endpoints:"
echo "   - Health: http://localhost/health"
echo "   - API Docs: http://localhost/docs"
echo "   - HTTPS: https://localhost (if certificates configured)"
echo ""
echo "📝 Logs:"
echo "   docker-compose logs -f"