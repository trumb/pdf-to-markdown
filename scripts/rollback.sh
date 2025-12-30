#!/bin/bash
set -e

echo "🔄 Rolling back to previous version..."
echo ""

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found"
    echo "   Please run this script from the project root directory"
    exit 1
fi

# Stop current containers
echo "🛑 Stopping current containers..."
docker-compose down

# Checkout previous commit
echo "⏪ Reverting to previous git commit..."
git reset --hard HEAD~1

# Rebuild images
echo "🏗️  Rebuilding Docker images..."
docker-compose build

# Start containers
echo "🚀 Starting containers..."
docker-compose up -d

# Wait for services
echo "⏳ Waiting for services to start..."
sleep 10

# Check health
echo "🏥 Checking application health..."
if curl -f http://localhost/health > /dev/null 2>&1; then
    echo "✅ Rollback successful!"
    echo ""
    echo "📊 Running containers:"
    docker-compose ps
else
    echo "❌ Health check failed after rollback"
    echo "   Manual intervention required"
    echo ""
    echo "📝 Check logs:"
    echo "   docker-compose logs"
    exit 1
fi

echo ""
echo "✅ Rollback complete"
echo "⚠️  Note: You may need to restore database from backup"
echo "   Run: cp backups/pdf2md-<timestamp>.db data/pdf2md.db"