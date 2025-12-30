# GCP Deployment

Deploy PDF-to-Markdown on Google Cloud Platform.

## Quick Start

```bash
# 1. Create GCS bucket
gsutil mb gs://pdf2md-bucket

# 2. Create Redis instance
gcloud redis instances create pdf2md-redis \
  --size=1 \
  --region=us-central1 \
  --tier=basic

# 3. Deploy to Cloud Run
gcloud run deploy pdf2md-app \
  --image gcr.io/PROJECT_ID/pdf2md:latest \
  --platform managed \
  --region us-central1 \
  --set-env-vars \
    GCS_BUCKET_NAME=pdf2md-bucket,\
    REDIS_URL=redis://REDIS_IP:6379/0,\
    RATE_LIMIT_BACKEND=redis,\
    RATE_LIMIT_FAIL_MODE=closed
```

## Configuration

```bash
# Service account for GCS
gcloud iam service-accounts create pdf2md-sa

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:pdf2md-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

# Get Redis IP
gcloud redis instances describe pdf2md-redis \
  --region=us-central1 \
  --format="get(host)"
```

## Secrets

Use Secret Manager:

```bash
echo -n "secret_value" | gcloud secrets create storage-key --data-file=-

gcloud secrets add-iam-policy-binding storage-key \
  --member="serviceAccount:pdf2md-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

See [Docker Deployment](docker.md) for container configuration details.