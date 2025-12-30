#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

strUser="${1:-admin}"
strPassword="${2:-}"

if [[ -z "${strPassword}" ]]; then
  echo "Usage: ./scripts/make-htpasswd.sh <user> <password>"
  echo ""
  echo "Example:"
  echo "  ./scripts/make-htpasswd.sh admin 'my-strong-password'"
  exit 1
fi

mkdir -p nginx_auth

# Create bcrypt htpasswd using httpd container (no host dependencies)
docker run --rm httpd:2.4-alpine htpasswd -Bbn "${strUser}" "${strPassword}" > nginx_auth/redis-admin.htpasswd

echo ""
echo "✅ Created nginx_auth/redis-admin.htpasswd for user '${strUser}'"
echo ""
echo "🔐 This file protects /redis-admin/ endpoint with HTTP Basic Auth"
echo ""