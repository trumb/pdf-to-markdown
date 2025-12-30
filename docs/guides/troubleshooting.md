# Troubleshooting

Common issues and solutions.

## API Issues

### Cannot connect to API

**Symptoms**: Connection refused

**Solutions**:
```bash
# Check if services are running
docker-compose ps

# Check logs
docker-compose logs app

# Verify health
curl http://localhost/health
```

### 503 Service Unavailable

**Cause**: Redis unavailable in closed mode

**Solution**:
```bash
# Check Redis
docker logs pdf2md-redis
docker exec pdf2md-redis redis-cli ping

# Restart Redis
docker-compose restart redis
```

### 429 Too Many Requests

**Cause**: Rate limit exceeded

**Solution**:
- Wait for rate limit window to reset
- Check rate limit headers
- Use appropriate role for your needs

## Authentication Issues

### 401 Unauthorized

**Check**:
```bash
# Verify token format
echo $TOKEN | grep "pdf2md_"

# Test with correct header
curl https://localhost/health \
  -H "Authorization: Bearer $TOKEN"
```

### Token not working

**Solutions**:
1. Verify token hasn't expired
2. Check token is active
3. Ensure correct role permissions

## Docker Issues

### Container won't start

```bash
# Check logs
docker logs pdf2md-app

# Verify environment variables
docker exec pdf2md-app env | grep REDIS

# Check dependencies
docker-compose ps
```

### Redis connection failed

```bash
# Verify Redis is running
docker-compose ps redis

# Check network
docker network inspect pdf2md_pdf2md-internal

# Test connection
docker exec pdf2md-app ping redis
```

## Certificate Issues

### Certificate not trusted

**Development**: Use `-k` flag with curl
**Production**: Use valid certificate (Let's Encrypt)

### Certificate expired

```bash
# Check expiration
openssl x509 -in certs/cert.pem -noout -enddate

# Renew Let's Encrypt
sudo certbot renew
docker exec pdf2md-nginx nginx -s reload
```

## Performance Issues

### Slow PDF processing

**Check**:
- PDF file size
- Resource limits
- Subprocess timeout configuration

**Solutions**:
- Increase timeout: `PDF_PROCESSING_TIMEOUT=600`
- Increase memory: `PDF_MEMORY_LIMIT=4096`

### High memory usage

**Solutions**:
- Set container memory limits
- Adjust batch processing size
- Monitor with `docker stats`

## Getting Help

1. Check logs: `docker-compose logs -f`
2. Verify configuration: Environment variables
3. Test health endpoints: `/health`, `/ready`
4. Review documentation
5. Open GitHub issue with logs

See platform-specific troubleshooting in [Deployment Guides](../deployment/README.md).