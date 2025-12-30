# Secrets Management

Best practices for managing sensitive credentials and configuration.

## Overview

PDF-to-Markdown requires secure management of:
- API tokens
- Database credentials
- Cloud storage credentials (Azure, GCS, S3)
- Redis connection strings
- TLS certificates and private keys

## Core Principles

### 1. Never Commit Secrets

❌ **NEVER do this**:
```python
# DON'T: Hardcoded credentials
DATABASE_URL = "postgresql://user:password@localhost/db"
AZURE_STORAGE_KEY = "actual_key_here"
ADMIN_TOKEN = "pdf2md_hardcoded_token"
```

✅ **ALWAYS do this**:
```python
# DO: Environment variables
import os

DATABASE_URL = os.getenv("DATABASE_URL")
AZURE_STORAGE_KEY = os.getenv("AZURE_STORAGE_KEY")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
```

### 2. Use Environment Variables

All secrets should be passed via environment variables:

```bash
# .env (local development only - never commit!)
DATABASE_PATH=/data/pdf2md.db
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;...
REDIS_URL=redis://redis:6379/0
ADMIN_TOKEN=pdf2md_generated_token_here
```

### 3. Template Files Only

Commit template files, never actual secrets:

```bash
# .env.example (safe to commit)
DATABASE_PATH=/data/pdf2md.db
AZURE_STORAGE_CONNECTION_STRING=your_azure_connection_string
REDIS_URL=redis://redis:6379/0
ADMIN_TOKEN=generate_via_cli
```

## Environment Configuration

### Local Development

**Setup**:
```bash
# 1. Copy template
cp .env.example .env

# 2. Edit .env with actual values
nano .env

# 3. Ensure .env is in .gitignore
echo ".env" >> .gitignore
```

**.env Example**:
```bash
# Database
DATABASE_PATH=/data/pdf2md.db

# Cloud Storage (Azure)
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=myaccount;AccountKey=mykey==;EndpointSuffix=core.windows.net
AZURE_STORAGE_CONTAINER=pdf2md

# Redis
REDIS_URL=redis://localhost:6379/0
RATE_LIMIT_BACKEND=redis
RATE_LIMIT_FAIL_MODE=closed

# Logging
LOG_LEVEL=DEBUG
```

### Docker Deployment

**Option 1: Environment File**
```bash
# docker-compose.yml
services:
  app:
    env_file:
      - .env
```

**Option 2: Docker Secrets**
```bash
# Create secrets
echo "connection_string" | docker secret create azure_connection -

# docker-compose.yml
services:
  app:
    secrets:
      - azure_connection
    environment:
      AZURE_STORAGE_CONNECTION_STRING_FILE: /run/secrets/azure_connection

secrets:
  azure_connection:
    external: true
```

**Option 3: Environment Variables**
```bash
# docker-compose.yml
services:
  app:
    environment:
      - DATABASE_PATH=/data/pdf2md.db
      - AZURE_STORAGE_CONNECTION_STRING=${AZURE_CONNECTION}
      - REDIS_URL=redis://redis:6379/0
```

### Production Deployment

**Use Cloud Secrets Management**:

#### Azure Key Vault

```bash
# Store secret
az keyvault secret set \
  --vault-name pdf2md-vault \
  --name azure-storage-key \
  --value "your_storage_key"

# Retrieve in application
az keyvault secret show \
  --vault-name pdf2md-vault \
  --name azure-storage-key \
  --query value -o tsv
```

**Docker Integration**:
```bash
# Retrieve and inject at runtime
AZURE_KEY=$(az keyvault secret show --vault-name pdf2md-vault --name azure-storage-key --query value -o tsv)

docker run -e AZURE_STORAGE_KEY="$AZURE_KEY" pdf2md-app
```

#### AWS Secrets Manager

```bash
# Store secret
aws secretsmanager create-secret \
  --name pdf2md/azure-storage-key \
  --secret-string "your_storage_key"

# Retrieve in application
aws secretsmanager get-secret-value \
  --secret-id pdf2md/azure-storage-key \
  --query SecretString --output text
```

#### GCP Secret Manager

```bash
# Store secret
echo -n "your_storage_key" | \
  gcloud secrets create azure-storage-key --data-file=-

# Retrieve in application
gcloud secrets versions access latest \
  --secret=azure-storage-key
```

## Required Secrets

### Application Secrets

| Secret | Purpose | Generation Method |
|--------|---------|-------------------|
| `ADMIN_TOKEN` | Admin API access | `pdf2md admin create-token` |
| `DATABASE_PATH` | SQLite location | Configuration |
| `REDIS_URL` | Redis connection | Configuration |

### Cloud Storage Secrets

#### Azure Blob Storage

```bash
# Required
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
AZURE_STORAGE_CONTAINER=pdf2md

# Alternative: SAS token
AZURE_STORAGE_SAS_TOKEN=?sv=2020-08-04&ss=b&srt=sco&sp=rwdlac&se=...
```

#### Google Cloud Storage

```bash
# Option 1: Service account key file
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
GCS_BUCKET_NAME=pdf2md-bucket

# Option 2: Service account JSON
GCS_SERVICE_ACCOUNT_JSON='{"type":"service_account","project_id":"..."}'
```

#### AWS S3

```bash
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_NAME=pdf2md-bucket
```

## Token Management

### Creating Admin Tokens

**ONLY via CLI** (security measure):
```bash
# Generate admin token
pdf2md admin create-token --role admin --user-id admin

# Store in environment
export ADMIN_TOKEN="pdf2md_generated_token_here"

# Or add to .env
echo "ADMIN_TOKEN=pdf2md_generated_token_here" >> .env
```

### Rotating Tokens

```bash
# 1. Generate new token
NEW_TOKEN=$(pdf2md admin create-token --role admin --user-id admin | grep "pdf2md_" | awk '{print $1}')

# 2. Update .env
sed -i "s/ADMIN_TOKEN=.*/ADMIN_TOKEN=$NEW_TOKEN/" .env

# 3. Restart services
docker-compose restart

# 4. Revoke old token
curl -X DELETE https://your-domain.com/api/v1/admin/tokens/{old_token_id} \
  -H "Authorization: Bearer $NEW_TOKEN"
```

## Security Best Practices

### 1. .gitignore Configuration

```bash
# .gitignore
.env
.env.local
.env.production
*.key
*.pem
secrets/
*.sqlite
*.db
```

### 2. File Permissions

```bash
# Secure .env file
chmod 600 .env
chown your-user:your-user .env

# Secure private keys
chmod 600 certs/*.key
chmod 600 certs/*.pem
```

### 3. Secret Rotation Schedule

| Secret Type | Rotation Frequency |
|-------------|-------------------|
| Admin tokens | Every 90 days |
| Application tokens | Every 180 days |
| Database passwords | Every 90 days |
| Cloud storage keys | Every 180 days |
| TLS certificates | Before expiration |

### 4. Access Control

```bash
# Limit who can access secrets
# Azure Key Vault
az keyvault set-policy \
  --name pdf2md-vault \
  --object-id <user-id> \
  --secret-permissions get list

# AWS Secrets Manager
aws secretsmanager put-resource-policy \
  --secret-id pdf2md/secrets \
  --resource-policy file://policy.json
```

## Configuration Management

### Development

```bash
# Local development
cp .env.example .env
# Edit .env with development values
nano .env
```

### Staging

```bash
# Use separate .env file
cp .env.example .env.staging
# Edit with staging credentials
nano .env.staging

# Deploy with staging config
docker-compose --env-file .env.staging up
```

### Production

```bash
# Use cloud secrets manager
# Never store production secrets in files

# Inject secrets at runtime
AZURE_KEY=$(az keyvault secret show ...)
REDIS_URL=$(aws secretsmanager get-secret-value ...)

docker run \
  -e AZURE_STORAGE_KEY="$AZURE_KEY" \
  -e REDIS_URL="$REDIS_URL" \
  pdf2md-app
```

## Secrets in CI/CD

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy
        env:
          AZURE_STORAGE_KEY: ${{ secrets.AZURE_STORAGE_KEY }}
          REDIS_URL: ${{ secrets.REDIS_URL }}
        run: |
          docker build -t pdf2md-app .
          docker run -e AZURE_STORAGE_KEY -e REDIS_URL pdf2md-app
```

**Add secrets in GitHub**:
Settings → Secrets and variables → Actions → New repository secret

### Environment-Specific Secrets

```yaml
# Different secrets per environment
jobs:
  deploy-staging:
    environment: staging
    steps:
      - run: echo "${{ secrets.STAGING_KEY }}"
  
  deploy-production:
    environment: production
    steps:
      - run: echo "${{ secrets.PRODUCTION_KEY }}"
```

## Monitoring & Auditing

### Secret Access Logging

```python
import logging

logger = logging.getLogger(__name__)

def get_secret(secret_name: str) -> str:
    """Get secret with audit logging."""
    logger.info(f"Secret accessed: {secret_name}")
    value = os.getenv(secret_name)
    
    if value is None:
        logger.error(f"Secret not found: {secret_name}")
        raise ValueError(f"Required secret {secret_name} not configured")
    
    return value
```

### Failed Access Alerts

```python
# Monitor for missing secrets
if not os.getenv("ADMIN_TOKEN"):
    logger.critical("ADMIN_TOKEN not configured - application cannot start")
    sys.exit(1)
```

## Troubleshooting

### Issue: Secret not found

**Check**:
```bash
# Verify environment variable
echo $AZURE_STORAGE_KEY

# Check .env file
grep AZURE .env

# Verify in Docker
docker exec pdf2md-app env | grep AZURE
```

### Issue: Permission denied

**Check file permissions**:
```bash
ls -la .env
# Should be: -rw------- (600)

# Fix if needed
chmod 600 .env
```

### Issue: Wrong secret value

**Verify secret**:
```bash
# Azure
az keyvault secret show --vault-name pdf2md-vault --name secret-name

# AWS
aws secretsmanager get-secret-value --secret-id pdf2md/secret-name

# GCP
gcloud secrets versions access latest --secret=secret-name
```

## Emergency Procedures

### Secret Compromise

1. **Immediately rotate the compromised secret**
2. **Revoke old tokens/keys**
3. **Audit access logs for unauthorized use**
4. **Investigate breach source**
5. **Update security procedures**

```bash
# Example: Rotate Azure storage key
az storage account keys renew \
  --account-name myaccount \
  --key primary

# Update application configuration
az keyvault secret set \
  --vault-name pdf2md-vault \
  --name azure-storage-key \
  --value "new_key_value"

# Restart services
docker-compose restart
```

## Secrets Checklist

- [ ] No secrets in source code
- [ ] .env in .gitignore
- [ ] .env.example template provided
- [ ] File permissions secured (600)
- [ ] Secrets in cloud manager (production)
- [ ] Rotation schedule defined
- [ ] Access logging enabled
- [ ] Failed access alerts configured
- [ ] Emergency procedures documented
- [ ] Team trained on secret handling

---

**Remember**: Secrets management is critical. One exposed secret can compromise the entire system.

For more security information, see [Security Overview](README.md).