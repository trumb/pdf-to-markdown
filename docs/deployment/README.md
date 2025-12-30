# Deployment Guide

Complete deployment options for PDF-to-Markdown.

## Deployment Options

PDF-to-Markdown can be deployed in various configurations to meet different needs:

### 🖥️ Local Development
**Best for**: Development, testing, experimentation

- Quick setup with Python virtual environment
- Local database and storage
- Self-signed certificates
- Single-worker configuration

See [Local Deployment](local.md)

### 🐳 Docker
**Best for**: Production, staging, consistent environments

- Complete container setup with nginx
- Redis for rate limiting
- TLS/mTLS support
- Horizontal scaling ready

See [Docker Deployment](docker.md)

### ☁️ Cloud Platforms

#### Azure
- Azure Container Instances or App Service
- Azure Blob Storage integration
- Azure Key Vault for secrets
- Application Insights monitoring

See [Azure Deployment](azure.md)

#### Google Cloud Platform
- Cloud Run or GKE
- Google Cloud Storage integration
- Secret Manager for secrets
- Cloud Logging and Monitoring

See [GCP Deployment](gcp.md)

#### Amazon Web Services
- ECS or EKS
- S3 Storage integration
- Secrets Manager for secrets
- CloudWatch monitoring

See [AWS Deployment](aws.md)

### 🏢 Enterprise
**Best for**: Large organizations, high-availability

- Kubernetes orchestration
- Multi-region deployment
- Custom PKI integration
- Enterprise monitoring and logging

See [Enterprise Deployment](enterprise.md)

## Quick Start Matrix

| Feature | Local | Docker | Cloud | Enterprise |
|---------|-------|--------|-------|------------|
| **Setup Time** | 5 min | 15 min | 30 min | 1-2 days |
| **Complexity** | Low | Medium | Medium | High |
| **Scalability** | Single | Medium | High | Very High |
| **Cost** | Free | Low | Medium | High |
| **HA Support** | No | Limited | Yes | Yes |
| **Production Ready** | No | Yes | Yes | Yes |

## Prerequisites

### All Deployments
- Python 3.11+
- Git

### Docker Deployments
- Docker 20.10+
- docker-compose 2.0+

### Cloud Deployments
- Cloud account and credentials
- Domain name (recommended)
- TLS certificates or Let's Encrypt

### Enterprise Deployments
- Kubernetes cluster
- Load balancer
- Persistent storage
- Monitoring infrastructure

## Configuration

### Environment Variables

All deployments use environment variables for configuration:

```bash
# Database
DATABASE_PATH=/data/pdf2md.db

# Cloud Storage
AZURE_STORAGE_CONNECTION_STRING=...
GCS_BUCKET_NAME=...
AWS_ACCESS_KEY_ID=...
S3_BUCKET_NAME=...

# Redis (for scaling)
REDIS_URL=redis://redis:6379/0
RATE_LIMIT_BACKEND=redis
RATE_LIMIT_FAIL_MODE=closed

# Logging
LOG_LEVEL=INFO
```

See [Configuration Reference](../guides/configuration.md) for complete list.

### Secrets Management

Different approaches for different environments:

| Environment | Secrets Method |
|-------------|----------------|
| Local | .env file |
| Docker | .env file or Docker secrets |
| Azure | Azure Key Vault |
| GCP | Secret Manager |
| AWS | Secrets Manager |
| Enterprise | Vault, Key Management System |

See [Secrets Management](../security/secrets-management.md) for details.

## Deployment Checklist

### Pre-Deployment

- [ ] Choose deployment platform
- [ ] Obtain domain name (if needed)
- [ ] Set up cloud account (if needed)
- [ ] Generate/obtain TLS certificates
- [ ] Prepare secrets and credentials
- [ ] Review security requirements

### Deployment

- [ ] Follow platform-specific guide
- [ ] Configure environment variables
- [ ] Set up TLS/mTLS
- [ ] Configure Redis (for scaling)
- [ ] Set up cloud storage
- [ ] Create admin tokens
- [ ] Test health endpoints

### Post-Deployment

- [ ] Verify API functionality
- [ ] Test authentication
- [ ] Test PDF conversion
- [ ] Configure monitoring
- [ ] Set up logging
- [ ] Configure backups
- [ ] Document deployment
- [ ] Train team

## Architecture Overview

### Basic Architecture (Single Instance)

```
┌────────────────┐
│    Client      │
└───────┬────────┘
        │ HTTPS
        ↓
┌────────────────┐
│     nginx      │
│  (TLS term.)   │
└───────┬────────┘
        │
        ↓
┌────────────────┐
│   FastAPI App  │
│   (Uvicorn)    │
└───────┬────────┘
        │
        ↓
┌────────────────┐
│   SQLite DB    │
└────────────────┘
```

### Scaled Architecture (Multiple Instances)

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTPS
       ↓
┌──────────────┐
│ Load Balancer│
└──────┬───────┘
       │
   ┌───┴───┬────────┬────────┐
   ↓       ↓        ↓        ↓
┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐
│App 1│ │App 2│ │App 3│ │App N│
└──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘
   │       │        │        │
   └───────┴────────┴────────┘
           │
      ┌────┴────┬─────────┐
      ↓         ↓         ↓
   ┌──────┐ ┌──────┐ ┌─────────┐
   │Redis │ │  DB  │ │ Storage │
   └──────┘ └──────┘ └─────────┘
```

## Monitoring

### Health Checks

```bash
# Health endpoint
curl http://localhost/health

# Readiness endpoint
curl http://localhost/ready
```

### Metrics

All deployments expose metrics for monitoring:

- Request count and latency
- Job processing metrics
- Rate limit statistics
- Error rates
- Redis connectivity

### Logging

Structured JSON logging to stdout:

```json
{
  "timestamp": "2025-12-29T20:00:00Z",
  "level": "INFO",
  "message": "PDF conversion complete",
  "job_id": "abc123xyz9",
  "duration_ms": 1500
}
```

## Scaling Strategies

### Vertical Scaling
- Increase CPU/memory for single instance
- Limited by hardware
- Quick and simple

### Horizontal Scaling
- Multiple app instances
- Requires Redis for rate limiting
- Requires shared database
- Requires load balancer

### Auto-Scaling
- Cloud platform auto-scaling
- Scale based on metrics
- CPU, memory, request count
- Cost-effective for variable load

## Backup and Recovery

### Database Backup

```bash
# Backup SQLite database
cp /data/pdf2md.db /backups/pdf2md-$(date +%Y%m%d).db

# Restore from backup
cp /backups/pdf2md-20251229.db /data/pdf2md.db
```

### Configuration Backup

```bash
# Backup configuration
tar czf config-backup.tar.gz .env docker-compose.yml certs/
```

### Disaster Recovery

1. Document deployment process
2. Maintain backup of secrets
3. Regular backup testing
4. Recovery time objective (RTO) planning
5. Recovery point objective (RPO) planning

## Troubleshooting

### Common Issues

**API not accessible**
- Check firewall rules
- Verify port bindings
- Check TLS configuration

**Jobs not processing**
- Check worker status
- Verify storage connectivity
- Check resource limits

**Rate limiting issues**
- Verify Redis connectivity
- Check rate limit configuration
- Review logs for errors

See platform-specific guides for detailed troubleshooting.

## Security Considerations

- Always use HTTPS in production
- Configure rate limiting appropriately
- Use strong admin tokens
- Enable mTLS for high-security environments
- Regular security updates
- Monitor failed authentication attempts

See [Security Documentation](../security/README.md) for complete security guidance.

## Support

- **Documentation**: [All guides](../README.md)
- **Issues**: [GitHub Issues](https://github.com/trumb/pdf-to-markdown/issues)
- **Security**: See [SECURITY.md](../../SECURITY.md)

---

**Choose your deployment path**:
- [Local Development](local.md)
- [Docker](docker.md)
- [Azure](azure.md)
- [GCP](gcp.md)
- [AWS](aws.md)
- [Enterprise](enterprise.md)