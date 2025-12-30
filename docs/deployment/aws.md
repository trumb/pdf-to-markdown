# AWS Deployment

Deploy PDF-to-Markdown on Amazon Web Services.

## Quick Start

```bash
# 1. Create S3 bucket
aws s3 mb s3://pdf2md-bucket

# 2. Create ElastiCache Redis
aws elasticache create-cache-cluster \
  --cache-cluster-id pdf2md-redis \
  --engine redis \
  --cache-node-type cache.t3.micro \
  --num-cache-nodes 1

# 3. Deploy to ECS
aws ecs create-cluster --cluster-name pdf2md-cluster

aws ecs register-task-definition \
  --cli-input-json file://task-definition.json

aws ecs create-service \
  --cluster pdf2md-cluster \
  --service-name pdf2md-service \
  --task-definition pdf2md-task \
  --desired-count 2 \
  --launch-type FARGATE
```

## Task Definition

```json
{
  "family": "pdf2md-task",
  "containerDefinitions": [{
    "name": "pdf2md-app",
    "image": "your-ecr-repo/pdf2md:latest",
    "environment": [
      {"name": "S3_BUCKET_NAME", "value": "pdf2md-bucket"},
      {"name": "REDIS_URL", "value": "redis://REDIS_ENDPOINT:6379/0"},
      {"name": "RATE_LIMIT_BACKEND", "value": "redis"},
      {"name": "RATE_LIMIT_FAIL_MODE", "value": "closed"}
    ]
  }]
}
```

## Secrets

Use Secrets Manager:

```bash
aws secretsmanager create-secret \
  --name pdf2md/storage-key \
  --secret-string "your_key"

# Grant access
aws secretsmanager put-resource-policy \
  --secret-id pdf2md/storage-key \
  --resource-policy file://policy.json
```

See [Docker Deployment](docker.md) for container configuration details.