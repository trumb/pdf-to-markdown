#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "🚀 Starting PDF2MD Local Stack..."
echo ""

# Check if certificates exist
if [[ ! -f "certs/fullchain.pem" ]] || [[ ! -f "certs/privkey.pem" ]] || [[ ! -f "certs/dhparam.pem" ]]; then
    echo "⚠️  TLS certificates not found!"
    echo "    Run: ./certs/generate-certs.sh"
    exit 1
fi

# Check if htpasswd exists
if [[ ! -f "nginx_auth/redis-admin.htpasswd" ]]; then
    echo "⚠️  Redis Admin htpasswd not found!"
    echo "    Run: ./scripts/make-htpasswd.sh admin 'your-password'"
    exit 1
fi

# Start services
docker compose -f docker-compose.local.yml --env-file .env.local up -d --build

echo ""
echo "✅ Stack is starting..."
echo ""
echo "📍 Endpoints:"
echo "   - HTTP:  http://localhost:8080 (redirects to HTTPS)"
echo "   - HTTPS: https://localhost:8443"
echo "   - API:   https://localhost:8443/api/docs"
echo "   - Downloads: https://localhost:8443/downloads/"
echo "   - Redis Admin: https://localhost:8443/redis-admin/ (Basic Auth)"
echo ""
echo "📋 Check logs:"
echo "   ./scripts/logs.sh"
echo ""
echo "🛑 Stop stack:"
echo "   ./scripts/down.sh"
echo ""