# Rate Limiting

PDF-to-Markdown implements role-based rate limiting to prevent abuse and ensure fair resource usage.

## Rate Limits by Role

| Role | Requests/Minute | Use Case |
|------|----------------|----------|
| **admin** | 1000 | System administration, monitoring |
| **job_manager** | 500 | Operations, job queue management |
| **job_writer** | 100 | Application services, document processing |
| **job_reader** | 50 | Reporting, read-only access |

## Rate Limiting Backends

### Single Worker Deployment (In-Memory)

For single-worker deployments, rate limiting uses in-memory storage:

```bash
# .env
RATE_LIMIT_BACKEND=memory
```

**Limitations**:
- Only works with single Uvicorn worker
- No persistence across restarts
- Not suitable for horizontal scaling

### Distributed Deployment (Redis)

**Redis is REQUIRED for:**
- Multiple Uvicorn workers
- Multiple API containers/replicas
- Any horizontal scaling scenario

**Configuration**:

```bash
# .env
RATE_LIMIT_BACKEND=redis
REDIS_URL=redis://redis:6379/0
RATE_LIMIT_FAIL_MODE=closed  # Recommended for production
```

## Redis Configuration

### Environment Variables

```bash
# Enable Redis-backed rate limiting
RATE_LIMIT_BACKEND=redis

# Redis connection
REDIS_URL=redis://redis:6379/0

# Failure mode
RATE_LIMIT_FAIL_MODE=closed  # or 'open'
```

### Docker Deployment

Redis runs as an internal service in Docker Compose:

```yaml
# docker-compose.yml
services:
  redis:
    image: redis:7-alpine
    container_name: pdf2md-redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
    networks:
      - pdf2md-internal
    # No public ports in production

  app:
    depends_on:
      redis:
        condition: service_healthy
    environment:
      RATE_LIMIT_BACKEND: redis
      REDIS_URL: redis://redis:6379/0
      RATE_LIMIT_FAIL_MODE: closed
```

**Security**: Redis is only accessible within the `pdf2md-internal` network, never exposed publicly.

### Failure Modes

#### Closed Mode (Recommended for Production)

```bash
RATE_LIMIT_FAIL_MODE=closed
```

**Behavior when Redis is unavailable**:
- Requests are **rejected** with explicit error
- Returns HTTP 503 Service Unavailable
- Protects system from uncontrolled traffic

**Response**:
```json
{
  "detail": "Rate limiting service unavailable",
  "error_code": "RATE_LIMIT_UNAVAILABLE"
}
```

**Use when**: Production systems where controlled failure is preferred over unchecked traffic.

#### Open Mode (Development Only)

```bash
RATE_LIMIT_FAIL_MODE=open
```

**Behavior when Redis is unavailable**:
- Requests **pass through** without rate limiting
- Logs warning messages
- System remains operational but unprotected

**Log Output**:
```
WARNING: Redis unavailable, rate limiting disabled
WARNING: Running without rate limiting protection
```

**Use when**: Development, testing, or when Redis is genuinely optional.

## Operational Guidance

### Verifying Redis Connectivity

**Health Endpoint**:
```bash
curl https://your-domain.com/health

# Response includes Redis status
{
  "status": "healthy",
  "redis_connected": true,
  "rate_limiting": "enabled"
}
```

**Check Logs**:
```bash
docker logs pdf2md-app | grep -i redis

# Healthy output:
INFO: Redis connected successfully
INFO: Rate limiting enabled (backend: redis)

# Problem output:
ERROR: Cannot connect to Redis at redis://redis:6379/0
WARNING: Rate limiting degraded or disabled
```

### Monitoring Signals

**Key metrics to watch**:

1. **Redis Connection Status**
   - Monitor `redis_connected` in health endpoint
   - Alert on connection failures

2. **Rate Limit Rejections**
   - Track HTTP 429 responses
   - Monitor per-user rate limit hits

3. **Redis Performance**
   ```bash
   docker exec pdf2md-redis redis-cli INFO stats
   ```

4. **Failed Request Count**
   - In closed mode: Track 503 responses
   - May indicate Redis outage

### Expected Log Messages

**Normal Operation**:
```
INFO: Starting PDF2MD API server
INFO: Redis connected: redis://redis:6379/0
INFO: Rate limiting enabled (backend: redis, mode: closed)
INFO: Rate limiter initialized for role: job_writer (100 req/min)
```

**Redis Outage (Closed Mode)**:
```
ERROR: Redis connection lost: redis://redis:6379/0
ERROR: Rate limiting service unavailable
WARNING: Rejecting requests until Redis recovers
```

**Redis Outage (Open Mode)**:
```
ERROR: Redis connection lost: redis://redis:6379/0
WARNING: Rate limiting disabled, requests passing through
WARNING: System unprotected - restore Redis immediately
```

## Scaling Considerations

### Horizontal Scaling Requirements

When scaling to multiple instances:

1. **Redis is mandatory** - In-memory backend will cause inconsistent limits
2. **Configure shared Redis** - All instances must use same Redis
3. **Use closed mode** - Prevent unchecked traffic during outages
4. **Monitor Redis** - Single point of failure for rate limiting

### Example Multi-Instance Setup

```yaml
# docker-compose.prod.yml
services:
  app:
    deploy:
      replicas: 3
    environment:
      RATE_LIMIT_BACKEND: redis
      REDIS_URL: redis://redis:6379/0
      RATE_LIMIT_FAIL_MODE: closed

  redis:
    deploy:
      resources:
        limits:
          memory: 256M
```

## Rate Limit Headers

Responses include rate limit information:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 75
X-RateLimit-Reset: 1703879400
```

## Rate Limit Exceeded Response

**HTTP 429 Too Many Requests**:

```json
{
  "detail": "Rate limit exceeded: 100 requests per minute",
  "retry_after": 42
}
```

**Headers**:
```
Retry-After: 42
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1703879400
```

## Testing Rate Limits

### Single Request Test

```bash
curl -i https://your-domain.com/api/v1/jobs \
  -H "Authorization: Bearer pdf2md_YOUR_TOKEN"

# Check headers
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
```

### Rate Limit Exhaustion Test

```bash
# Rapid requests to trigger limit
for i in {1..150}; do
  curl -s https://your-domain.com/api/v1/jobs \
    -H "Authorization: Bearer pdf2md_YOUR_TOKEN"
done

# Should eventually return 429
```

### Redis Failure Test

```bash
# Stop Redis to test failure mode
docker stop pdf2md-redis

# Make request
curl https://your-domain.com/api/v1/jobs \
  -H "Authorization: Bearer pdf2md_YOUR_TOKEN"

# Closed mode: Returns 503
# Open mode: Returns 200 with warning logs
```

## Troubleshooting

### Issue: Rate limits inconsistent across instances

**Cause**: Using in-memory backend with multiple workers/containers

**Solution**: Configure Redis backend:
```bash
RATE_LIMIT_BACKEND=redis
REDIS_URL=redis://redis:6379/0
```

### Issue: All requests failing with 503

**Cause**: Redis unavailable in closed mode

**Check**:
```bash
docker logs pdf2md-redis
docker exec pdf2md-redis redis-cli ping
```

**Solution**: Restore Redis or temporarily switch to open mode (not recommended)

### Issue: Rate limits not enforced

**Cause**: Redis unavailable in open mode

**Check logs**: Look for `WARNING: Rate limiting disabled`

**Solution**: Fix Redis connectivity

## Best Practices

1. **Always use Redis in production** with multiple instances
2. **Set fail mode to closed** for production safety
3. **Monitor Redis health** as part of system monitoring
4. **Test failure modes** during deployment validation
5. **Size Redis appropriately** for your request volume
6. **Use Redis persistence** for rate limit continuity across restarts

## Security Considerations

- Never expose Redis ports publicly
- Use Redis AUTH if running outside Docker network
- Monitor for rate limit bypass attempts
- Log all rate limit violations
- Consider IP-based limiting in addition to token-based