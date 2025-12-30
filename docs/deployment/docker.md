# Docker Deployment

Complete guide for deploying PDF-to-Markdown with Docker.

## Overview

Docker deployment provides:
- Complete containerized environment
- nginx reverse proxy with TLS
- Redis for distributed rate limiting
- Easy horizontal scaling
- Production-ready configuration

## Prerequisites

- Docker 20.10+
- docker-compose 2.0+
- 2 GB RAM minimum
- 10 GB disk space
- Domain name (for Let's Encrypt)

## Quick Start

```bash
# 1. Clone repository
git clone https://github.com/trumb/pdf-to-markdown.git
cd pdf-to-markdown

# 2. Copy environment template
cp .env.example .env

# 3. Generate self-signed certificate (development)
./certs/generate-selfsigned.sh

# 4. Start services
docker-compose up -d

# 5. Check health
curl http://localhost/health

# 6. Create admin token
docker exec -it pdf2md-app pdf2md admin create-token \
  --role admin --user-id admin

# 7. Test API
curl -X POST https://localhost/api/v1/convert \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test.pdf"
```

## Architecture

### Services

```yaml
pdf2md-nginx    # nginx reverse proxy (TLS termination)
pdf2md-app      # FastAPI application
pdf2md-redis    # Redis (rate limiting)
```

### Network Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTPS (443)
       ↓
┌──────────────┐
│  pdf2md-nginx│ (exposed: 80, 443)
│  TLS term.   │
└──────┬───────┘
       │ HTTP (internal)
       ↓
┌──────────────┐
│  pdf2md-app  │ (internal only)
│  Port 8000   │
└───┬──────┬───┘
    │      │
    │      └──────────┐
    ↓                 ↓
┌────────┐      ┌───────────┐
│ SQLite │      │pdf2md-redis│ (internal only)
│  DB    │      │ Port 6379 │
└────────┘      └───────────┘
```

## Configuration

### Environment Variables

Create `.env` file:

```bash
# Database
DATABASE_PATH=/data/pdf2md.db

# Redis - REQUIRED for multiple workers/instances
REDIS_URL=redis://redis:6379/0
RATE_LIMIT_BACKEND=redis
RATE_LIMIT_FAIL_MODE=closed  # closed (recommended) or open

# Cloud Storage (optional - choose one)
# Azure
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;...
AZURE_STORAGE_CONTAINER=pdf2md

# GCS
GOOGLE_APPLICATION_CREDENTIALS=/app/service-account-key.json
GCS_BUCKET_NAME=pdf2md-bucket

# AWS
AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY
AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_NAME=pdf2md-bucket

# Logging
LOG_LEVEL=INFO
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  app:
    build: .
    container_name: pdf2md-app
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./data:/data
      - ./secrets:/app/secrets:ro
    depends_on:
      redis:
        condition: service_healthy
    networks:
      - pdf2md-internal
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
  
  redis:
    image: redis:7-alpine
    container_name: pdf2md-redis
    restart: unless-stopped
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
    networks:
      - pdf2md-internal
    # No public ports - internal only
  
  nginx:
    image: nginx:alpine
    container_name: pdf2md-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
      - ./acme-challenge:/var/www/acme-challenge  # For Let's Encrypt
    depends_on:
      - app
    networks:
      - pdf2md-internal
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  pdf2md-internal:
    driver: bridge
```

## Redis Rate Limiting

### When Redis is Required

**Redis is REQUIRED for:**
- Multiple Uvicorn workers (workers > 1)
- Multiple API containers/replicas
- Any horizontal scaling scenario

**Without Redis**, rate limiting will be inconsistent across workers/containers.

### Enabling Redis Rate Limiting

```bash
# .env
RATE_LIMIT_BACKEND=redis
REDIS_URL=redis://redis:6379/0
RATE_LIMIT_FAIL_MODE=closed  # Recommended for production
```

### Redis Configuration in Docker

Redis runs as an internal service:

```yaml
# docker-compose.yml
redis:
  image: redis:7-alpine
  container_name: pdf2md-redis
  restart: unless-stopped
  command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 10s
    timeout: 3s
    retries: 3
  networks:
    - pdf2md-internal
  # IMPORTANT: No public ports in production
```

**Security**: Redis is only accessible within the `pdf2md-internal` network, never exposed publicly.

### Failure Modes

#### Closed Mode (Production Default)

```bash
RATE_LIMIT_FAIL_MODE=closed
```

**Behavior when Redis unavailable**:
- Requests **rejected** with HTTP 503
- Response: `{"detail": "Rate limiting service unavailable", "error_code": "RATE_LIMIT_UNAVAILABLE"}`
- Protects system from uncontrolled traffic

**Use for**: Production systems where controlled failure is preferred.

#### Open Mode (Development Only)

```bash
RATE_LIMIT_FAIL_MODE=open
```

**Behavior when Redis unavailable**:
- Requests **pass through** without rate limiting
- Warnings logged: `WARNING: Redis unavailable, rate limiting disabled`
- System unprotected but operational

**Use for**: Development, testing only.

### Verifying Redis Connectivity

**Health endpoint**:
```bash
curl http://localhost/health

# Response includes Redis status
{
  "status": "healthy",
  "redis_connected": true,
  "rate_limiting": "enabled"
}
```

**Check logs**:
```bash
docker logs pdf2md-app | grep -i redis

# Healthy:
INFO: Redis connected: redis://redis:6379/0
INFO: Rate limiting enabled (backend: redis, mode: closed)

# Problem:
ERROR: Cannot connect to Redis at redis://redis:6379/0
WARNING: Rate limiting degraded or disabled
```

### Monitoring Redis

**Connection status**:
```bash
docker exec pdf2md-redis redis-cli ping
# Expected: PONG
```

**Redis stats**:
```bash
docker exec pdf2md-redis redis-cli INFO stats
```

**Rate limit keys**:
```bash
docker exec pdf2md-redis redis-cli KEYS "rate_limit:*"
```

## TLS Configuration

### Option 1: Self-Signed Certificates (Development)

```bash
# Generate certificate
./certs/generate-selfsigned.sh

# Or manually
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout certs/selfsigned-key.pem \
  -out certs/selfsigned-cert.pem \
  -subj "/CN=localhost"
```

**nginx configuration**:
```nginx
ssl_certificate /etc/nginx/certs/selfsigned-cert.pem;
ssl_certificate_key /etc/nginx/certs/selfsigned-key.pem;
```

### Option 2: Let's Encrypt (Production)

**Prerequisites**:
- Public domain name
- Port 80 accessible for validation
- Port 443 for HTTPS

**Initial Setup**:

```bash
# 1. Stop nginx to free port 80
docker-compose stop nginx

# 2. Obtain certificate
sudo certbot certonly --standalone \
  -d pdf2md.example.com \
  --email admin@example.com \
  --agree-tos

# 3. Update docker-compose.yml
services:
  nginx:
    volumes:
      - /etc/letsencrypt:/etc/letsencrypt:ro

# 4. Update nginx.conf
ssl_certificate /etc/letsencrypt/live/pdf2md.example.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/pdf2md.example.com/privkey.pem;

# 5. Start nginx
docker-compose start nginx
```

**Auto-Renewal**:

```bash
# Test renewal
sudo certbot renew --dry-run

# Set up systemd timer
sudo systemctl enable certbot-renew.timer
sudo systemctl start certbot-renew.timer

# Reload nginx after renewal
sudo systemctl edit certbot-renew.service

# Add:
[Service]
ExecStartPost=/usr/bin/docker exec pdf2md-nginx nginx -s reload
```

### Option 3: mTLS (High Security)

Enable mutual TLS for client authentication:

```nginx
# nginx.conf
server {
    listen 443 ssl;
    
    # Server certificates
    ssl_certificate /etc/nginx/certs/server-cert.pem;
    ssl_certificate_key /etc/nginx/certs/server-key.pem;
    
    # Client certificate verification
    ssl_client_certificate /etc/nginx/certs/ca-cert.pem;
    ssl_verify_client on;
    ssl_verify_depth 2;
}
```

## Scaling

### Horizontal Scaling

**Scale to multiple instances**:

```yaml
# docker-compose.prod.yml
services:
  app:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 2G
    environment:
      - RATE_LIMIT_BACKEND=redis  # REQUIRED for multiple instances
      - REDIS_URL=redis://redis:6379/0
      - RATE_LIMIT_FAIL_MODE=closed
```

**Start scaled deployment**:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale app=3
```

**nginx automatically load balances** across app replicas.

### Resource Limits

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 512M
  
  redis:
    deploy:
      resources:
        limits:
          memory: 256M
```

## Monitoring

### Health Checks

```bash
# Overall health
curl http://localhost/health

# Readiness
curl http://localhost/ready

# nginx status
docker ps | grep pdf2md-nginx

# Redis connectivity
docker exec pdf2md-redis redis-cli ping
```

### Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app
docker-compose logs -f redis
docker-compose logs -f nginx

# Recent errors
docker-compose logs --tail=100 | grep ERROR
```

### Metrics

Access Prometheus metrics:
```bash
curl http://localhost/metrics
```

## Backup and Recovery

### Backup

```bash
# Create backup directory
mkdir -p backups

# Backup database
docker cp pdf2md-app:/data/pdf2md.db ./backups/pdf2md-$(date +%Y%m%d).db

# Backup configuration
tar czf backups/config-$(date +%Y%m%d).tar.gz \
  .env docker-compose.yml nginx/ certs/
```

### Restore

```bash
# Stop services
docker-compose down

# Restore database
cp backups/pdf2md-20251229.db ./data/pdf2md.db

# Restore configuration
tar xzf backups/config-20251229.tar.gz

# Start services
docker-compose up -d
```

## Troubleshooting

### Issue: Redis connection failed

**Symptoms**: HTTP 503 errors, logs show `ERROR: Cannot connect to Redis`

**Check**:
```bash
docker logs pdf2md-redis
docker exec pdf2md-redis redis-cli ping
```

**Solution**:
```bash
# Restart Redis
docker-compose restart redis

# Check Redis health
docker-compose ps redis
```

### Issue: Rate limits inconsistent

**Cause**: Using in-memory backend with multiple workers

**Solution**: Enable Redis backend:
```bash
# .env
RATE_LIMIT_BACKEND=redis
REDIS_URL=redis://redis:6379/0

# Restart
docker-compose restart app
```

### Issue: nginx cannot reach app

**Check**:
```bash
# Verify app is running
docker-compose ps app

# Check app health
docker exec pdf2md-app curl http://localhost:8000/health

# Check networks
docker network inspect pdf2md_pdf2md-internal
```

### Issue: Certificate expired

**Check expiration**:
```bash
openssl x509 -in certs/cert.pem -noout -enddate
```

**Renew Let's Encrypt**:
```bash
sudo certbot renew
docker exec pdf2md-nginx nginx -s reload
```

## Production Best Practices

1. **Always use Redis** for rate limiting in production
2. **Set fail mode to closed** for production safety
3. **Use Let's Encrypt** for TLS certificates
4. **Configure auto-renewal** for certificates
5. **Set resource limits** on containers
6. **Monitor Redis health** continuously
7. **Regular backups** of database and configuration
8. **Use environment-specific** .env files
9. **Never commit secrets** to source control
10. **Test failure scenarios** during deployment validation

## Security Checklist

- [ ] HTTPS enabled with valid certificates
- [ ] Redis not exposed publicly
- [ ] Rate limiting configured (closed mode)
- [ ] Admin tokens generated via CLI
- [ ] Secrets in .env (not in docker-compose.yml)
- [ ] Resource limits set
- [ ] Health checks configured
- [ ] Firewall rules configured
- [ ] Monitoring and alerting enabled
- [ ] Backup strategy implemented

---

For more deployment options, see [Deployment Overview](README.md).