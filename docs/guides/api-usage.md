# API Usage

REST API usage examples.

## Authentication

All requests require Bearer token:

```bash
curl https://your-domain.com/api/v1/endpoint \
  -H "Authorization: Bearer pdf2md_YOUR_TOKEN"
```

## Convert PDF

```bash
curl -X POST https://your-domain.com/api/v1/convert \
  -H "Authorization: Bearer pdf2md_YOUR_TOKEN" \
  -F "file=@document.pdf"

# Response:
{
  "job_id": "abc123xyz9",
  "status": "queued",
  "created_at": "2025-12-29T20:00:00Z"
}
```

## Check Job Status

```bash
curl https://your-domain.com/api/v1/jobs/abc123xyz9 \
  -H "Authorization: Bearer pdf2md_YOUR_TOKEN"

# Response:
{
  "job_id": "abc123xyz9",
  "status": "complete",
  "result": {
    "pages": 10,
    "tokens": {
      "openai_cl100k": 5000
    }
  }
}
```

## Download Result

```bash
curl https://your-domain.com/api/v1/jobs/abc123xyz9/result \
  -H "Authorization: Bearer pdf2md_YOUR_TOKEN" \
  -o result.md
```

See [API Reference](../api/README.md) for complete endpoint documentation.