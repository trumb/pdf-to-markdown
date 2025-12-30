#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "🛑 Stopping PDF2MD Local Stack..."
echo ""

docker compose -f docker-compose.local.yml --env-file .env.local down

echo ""
echo "✅ Stack stopped"
echo ""
echo "🗑️  To remove volumes (data + results):"
echo "   docker compose -f docker-compose.local.yml down -v"
echo ""