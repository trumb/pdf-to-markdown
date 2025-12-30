# API Endpoints Reference

Complete reference for all PDF-to-Markdown API endpoints.

## Job Management Endpoints

### POST /api/v1/convert {#post-convert}

Submit a PDF file for conversion to Markdown.

**Authentication**: Required (job_writer, job_manager, admin)

**Request**:
```bash
curl -X POST https://your-domain.com/api/v1/convert \
  -H "Authorization: Bearer pdf2md_YOUR_TOKEN" \
  -F "file=@document.pdf" \
  -F "output_format=markdown" \
  -F "token_encoding=openai"
```

**Parameters**:
- `file` (required): PDF file to convert
- `output_format` (optional): Output format (default: "markdown")
- `token_encoding` (optional): Token encoding ("openai", "claude", default: "openai")

**Response** (202 Accepted):
```json
{
  "job_id": "abc123xyz9",
  "status": "queued",
  "created_at": "2025-12-29T20:00:00Z",
  "message": "Job queued for processing"
}
```

---

### GET /api/v1/jobs {#get-jobs}

List jobs accessible to the authenticated user.

**Authentication**: Required (all roles)

**Request**:
```bash
curl https://your-domain.com/api/v1/jobs \
  -H "Authorization: Bearer pdf2md_YOUR_TOKEN"
```

**Query Parameters**:
- `status` (optional): Filter by status (queued, running, complete, failed)
- `limit` (optional): Max results (default: 50, max: 100)
- `offset` (optional): Pagination offset (default: 0)

**Response** (200 OK):
```json
{
  "jobs": [
    {
      "job_id": "abc123xyz9",
      "status": "complete",
      "created_at": "2025-12-29T20:00:00Z",
      "completed_at": "2025-12-29T20:01:30Z",
      "owner_id": "user-alice"
    }
  ],
  "total": 42,
  "limit": 50,
  "offset": 0
}
```

---

### GET /api/v1/jobs/{id} {#get-job}

Get detailed status of a specific job.

**Authentication**: Required (owner, job_manager, admin, or granted access)

**Request**:
```bash
curl https://your-domain.com/api/v1/jobs/abc123xyz9 \
  -H "Authorization: Bearer pdf2md_YOUR_TOKEN"
```

**Response** (200 OK):
```json
{
  "job_id": "abc123xyz9",
  "status": "complete",
  "owner_id": "user-alice",
  "created_at": "2025-12-29T20:00:00Z",
  "started_at": "2025-12-29T20:00:05Z",
  "completed_at": "2025-12-29T20:01:30Z",
  "result": {
    "pages": 10,
    "tokens": {
      "openai_cl100k": 5000,
      "openai_p50k": 5100,
      "claude_estimate": 5500
    },
    "extraction_method": "pdfplumber",
    "warnings": []
  }
}
```

---

### GET /api/v1/jobs/{id}/result {#get-result}

Download the converted Markdown result.

**Authentication**: Required (owner, job_manager, admin, or granted access)

**Request**:
```bash
curl https://your-domain.com/api/v1/jobs/abc123xyz9/result \
  -H "Authorization: Bearer pdf2md_YOUR_TOKEN" \
  -o result.md
```

**Response** (200 OK):
```
Content-Type: text/markdown
Content-Disposition: attachment; filename="result_abc123xyz9.md"

---
source_file: "document.pdf"
converted_at: "2025-12-29T20:01:30Z"
pages: 10
tokens:
  openai_cl100k: 5000
---

# Document Title

Content here...
```

---

### POST /api/v1/jobs/{id}/stop {#post-stop}

Stop a running job.

**Authentication**: Required (owner, job_manager, admin)

**Request**:
```bash
curl -X POST https://your-domain.com/api/v1/jobs/abc123xyz9/stop \
  -H "Authorization: Bearer pdf2md_YOUR_TOKEN"
```

**Response** (200 OK):
```json
{
  "job_id": "abc123xyz9",
  "status": "stopped",
  "message": "Job stopped successfully"
}
```

---

### POST /api/v1/jobs/{id}/cancel {#post-cancel}

Cancel a queued or running job.

**Authentication**: Required (owner, job_manager, admin)

**Request**:
```bash
curl -X POST https://your-domain.com/api/v1/jobs/abc123xyz9/cancel \
  -H "Authorization: Bearer pdf2md_YOUR_TOKEN"
```

**Response** (200 OK):
```json
{
  "job_id": "abc123xyz9",
  "status": "cancelled",
  "message": "Job cancelled successfully"
}
```

---

### POST /api/v1/jobs/{id}/throttle {#post-throttle}

Throttle job processing speed.

**Authentication**: Required (job_manager, admin)

**Request**:
```bash
curl -X POST https://your-domain.com/api/v1/jobs/abc123xyz9/throttle \
  -H "Authorization: Bearer pdf2md_YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"throttle_percent": 50}'
```

**Response** (200 OK):
```json
{
  "job_id": "abc123xyz9",
  "throttle_percent": 50,
  "message": "Job throttled to 50% speed"
}
```

---

### POST /api/v1/jobs/{id}/grant-access {#post-grant}

Grant job_reader access to a job.

**Authentication**: Required (owner, job_manager, admin)

**Request**:
```bash
curl -X POST https://your-domain.com/api/v1/jobs/abc123xyz9/grant-access \
  -H "Authorization: Bearer pdf2md_YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-bob"}'
```

**Response** (200 OK):
```json
{
  "job_id": "abc123xyz9",
  "granted_to": "user-bob",
  "message": "Access granted successfully"
}
```

---

## Admin Endpoints

### POST /api/v1/admin/tokens {#post-token}

Create a new authentication token.

**Authentication**: Required (admin)

**Request**:
```bash
curl -X POST https://your-domain.com/api/v1/admin/tokens \
  -H "Authorization: Bearer pdf2md_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "app-service",
    "role": "job_writer",
    "expires_days": 365
  }'
```

**Response** (201 Created):
```json
{
  "token": "pdf2md_kF8j2NmP9qR3sT5vU7wX...",
  "token_id": "tok_abc123",
  "user_id": "app-service",
  "role": "job_writer",
  "created_at": "2025-12-29T20:00:00Z",
  "expires_at": "2026-12-29T20:00:00Z"
}
```

---

### GET /api/v1/admin/tokens {#get-tokens}

List all authentication tokens.

**Authentication**: Required (admin)

**Request**:
```bash
curl https://your-domain.com/api/v1/admin/tokens \
  -H "Authorization: Bearer pdf2md_ADMIN_TOKEN"
```

**Response** (200 OK):
```json
{
  "tokens": [
    {
      "token_id": "tok_abc123",
      "user_id": "app-service",
      "role": "job_writer",
      "created_at": "2025-12-29T10:00:00Z",
      "expires_at": "2026-12-29T10:00:00Z",
      "last_used_at": "2025-12-29T20:00:00Z",
      "is_active": true
    }
  ],
  "total": 15
}
```

---

### DELETE /api/v1/admin/tokens/{id} {#delete-token}

Revoke an authentication token.

**Authentication**: Required (admin)

**Request**:
```bash
curl -X DELETE https://your-domain.com/api/v1/admin/tokens/tok_abc123 \
  -H "Authorization: Bearer pdf2md_ADMIN_TOKEN"
```

**Response** (200 OK):
```json
{
  "token_id": "tok_abc123",
  "message": "Token revoked successfully"
}
```

---

### PATCH /api/v1/admin/tokens/{id} {#patch-token}

Update token status (enable/disable).

**Authentication**: Required (admin)

**Request**:
```bash
curl -X PATCH https://your-domain.com/api/v1/admin/tokens/tok_abc123 \
  -H "Authorization: Bearer pdf2md_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'
```

**Response** (200 OK):
```json
{
  "token_id": "tok_abc123",
  "is_active": false,
  "message": "Token updated successfully"
}
```

---

## Health Check Endpoints

### GET /health {#get-health}

Check API health status.

**Authentication**: Not required

**Request**:
```bash
curl https://your-domain.com/health
```

**Response** (200 OK):
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "redis_connected": true,
  "rate_limiting": "enabled",
  "timestamp": "2025-12-29T20:00:00Z"
}
```

---

### GET /ready {#get-ready}

Check if API is ready to accept requests.

**Authentication**: Not required

**Request**:
```bash
curl https://your-domain.com/ready
```

**Response** (200 OK):
```json
{
  "ready": true,
  "services": {
    "database": "connected",
    "redis": "connected",
    "storage": "available"
  }
}
```

---

## Common Error Responses

### 400 Bad Request

```json
{
  "detail": "Invalid file format. Expected PDF file.",
  "error_code": "INVALID_FILE_FORMAT"
}
```

### 401 Unauthorized

```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden

```json
{
  "detail": "Insufficient permissions for this operation"
}
```

### 404 Not Found

```json
{
  "detail": "Job not found: abc123xyz9"
}
```

### 429 Too Many Requests

```json
{
  "detail": "Rate limit exceeded: 100 requests per minute",
  "retry_after": 42
}
```

### 500 Internal Server Error

```json
{
  "detail": "Internal server error",
  "error_code": "INTERNAL_ERROR"
}
```

### 503 Service Unavailable

```json
{
  "detail": "Rate limiting service unavailable",
  "error_code": "RATE_LIMIT_UNAVAILABLE"
}
```

---

## HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful request |
| 201 | Created | Resource created |
| 202 | Accepted | Job queued |
| 400 | Bad Request | Invalid parameters |
| 401 | Unauthorized | Invalid/missing token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

---

## Next Steps

- See [Schemas](schemas.md) for complete data structures
- See [Authentication](authentication.md) for token management
- See [Rate Limiting](rate-limiting.md) for rate limit configuration