# PDF2MD Local Docker Stack (pdf-processor)

Local development deployment of the PDF-to-Markdown system with TLS/mTLS support and Redis Commander admin interface.

## Architecture

```
Public:
  https://localhost:8443  (nginx - TLS 1.3/1.2)
  http://localhost:8080   (redirects to HTTPS)

Internal:
  pdf2md-api:8000         (FastAPI)
  pdf2md-redis:6379       (Redis with ACL auth)
  pdf2md-redis-commander:8081 (Admin UI)
```

## Prerequisites

- Docker & Docker Compose
- Bash (for scripts)
- OpenSSL (for certificate generation)

## Quick Start

### 1. Generate TLS Certificates

```bash
cd certs
bash generate-certs.sh localhost
```

### 2. Generate HTTP Basic Auth for Redis Commander

```bash
bash scripts/make-htpasswd.sh admin 'your-strong-password'
```

### 3. Start the Stack

```bash
bash scripts/up.sh
```

### 4. Access Endpoints

| Endpoint | URL | Auth |
|----------|-----|------|
| Welcome | https://localhost:8443/ | None |
| API Docs | https://localhost:8443/api/docs | Bearer token |
| Downloads | https://localhost:8443/downloads/ | None |
| Redis Admin | https://localhost:8443/redis-admin/ | Basic Auth (admin/password) |

## Configuration Files

- **`.env.local`** - Environment variables (Redis passwords, etc.)
- **`docker-compose.local.yml`** - Service definitions
- **`redis/redis.conf`** - Redis server configuration
- **`redis/users.acl`** - Redis ACL (app user + admin user)
- **`nginx/conf.d/pdf2md.conf`** - nginx routing with TLS

## Security Features

### TLS Configuration
- **Primary**: TLS 1.3
- **Fallback**: TLS 1.2 only
- **Ciphers**: Mozilla Intermediate compatibility
- **DH Parameters**: 2048-bit for Perfect Forward Secrecy

### Redis Security
- **App User** (`pdf2md`): Restricted to `rate_limit:*` keys only
- **Admin User** (`redis_admin`): Full access for Redis Commander
- **No default user access** - all connections require authentication

### nginx Security
- HTTP → HTTPS redirect
- Security headers (X-Frame-Options, X-Content-Type-Options, etc.)
- Basic Auth for `/redis-admin/` endpoint
- Read-only mode for Redis Commander

## Helper Scripts

```bash
# Start stack
./scripts/up.sh

# Stop stack
./scripts/down.sh

# View logs (all services)
./scripts/logs.sh

# View logs (specific service)
./scripts/logs.sh api
./scripts/logs.sh nginx
./scripts/logs.sh redis

# Generate new htpasswd
./scripts/make-htpasswd.sh <username> '<password>'
```

## Networks

- **edge**: nginx, api, redis-commander (internet-facing)
- **internal**: api, redis, redis-commander (isolated)

Only nginx publishes ports to the host.

## Volumes

- **pdf-processor_data**: Application data (/var/lib/pdf2md)
- **pdf-processor_results**: Converted markdown files

## Troubleshooting

### nginx won't start
- Check logs: `docker logs pdf2md-nginx`
- Verify certs exist: `ls -la certs/`
- Verify htpasswd exists: `ls -la nginx_auth/`

### API won't start
- Check logs: `docker logs pdf2md-api`
- Verify Redis is healthy: `docker ps`
- Check Redis connection: `docker exec pdf2md-redis redis-cli -a <password> PING`

### Browser shows certificate warning
This is expected with self-signed certificates. Click "Advanced" → "Proceed to site (unsafe)".

For production, use Let's Encrypt certificates.

## Production Deployment

For production deployment:
1. Replace self-signed certs with Let's Encrypt
2. Update passwords in `.env.local`
3. Enable HSTS in `nginx/snippets/security-headers.conf`
4. Use separate secrets management (Azure Key Vault, AWS Secrets Manager, etc.)
5. Consider enabling mTLS for service-to-service auth

## Optional: mTLS Endpoint

To enable the mTLS endpoint (port 8444):
1. Generate CA certificate: `openssl genrsa -out certs/ca-key.pem 2048`
2. Uncomment mTLS server block in `nginx/conf.d/pdf2md.conf`
3. Recreate nginx container

## Environment Variables

Key variables in `.env.local`:

```bash
# Redis Authentication
REDIS_APP_PASSWORD=change-me-app-redis-local
REDIS_ADMIN_PASSWORD=change-me-admin-redis-local

# Redis Connection (API)
REDIS_URL=redis://pdf2md:${REDIS_APP_PASSWORD}@redis:6379/0

# Rate Limiting
RATE_LIMIT_BACKEND=redis
RATE_LIMIT_FAIL_MODE=closed
```

## Container Names

- `pdf2md-nginx` - nginx reverse proxy
- `pdf2md-api` - FastAPI application
- `pdf2md-redis` - Redis server
- `pdf2md-redis-commander` - Redis admin UI

## Health Checks

All containers have health checks configured:
- nginx: HTTP GET on port 8080
- api: Python import test on /health endpoint
- redis: `redis-cli ping`
- redis-commander: HTTP GET on port 8081

## License

MIT License - See LICENSE file in root directory