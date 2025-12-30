#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

strService="${1:-}"

if [[ -z "${strService}" ]]; then
    echo "📋 Showing logs for all services..."
    echo ""
    docker compose -f docker-compose.local.yml --env-file .env.local logs -f
else
    echo "📋 Showing logs for ${strService}..."
    echo ""
    docker compose -f docker-compose.local.yml --env-file .env.local logs -f "${strService}"
fi