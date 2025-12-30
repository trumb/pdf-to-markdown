# Cloud Storage Configuration

Configure multi-cloud storage for PDF-to-Markdown.

## Overview

Automatic fallback order:
1. Azure Blob Storage (Priority 1)
2. Google Cloud Storage (Priority 2)
3. AWS S3 (Priority 3)
4. Local Filesystem (Development)

## Azure Blob Storage

```bash
# .env
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...
AZURE_STORAGE_CONTAINER=pdf2md
```

## Google Cloud Storage

```bash
# .env
GOOGLE_APPLICATION_CREDENTIALS=/app/service-account-key.json
GCS_BUCKET_NAME=pdf2md-bucket
```

## AWS S3

```bash
# .env
AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY
AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_NAME=pdf2md-bucket
```

## Local Storage (Development)

No configuration needed - automatically used if no cloud storage configured.

See [Security](../security/secrets-management.md) for credential management.