# API Schemas

Complete data structure reference for the PDF-to-Markdown API.

## Job Schema

Represents a PDF conversion job.

```json
{
  "job_id": "string (10 chars)",
  "status": "queued|running|complete|failed|stopped|cancelled",
  "owner_id": "string",
  "created_at": "ISO 8601 datetime",
  "started_at": "ISO 8601 datetime|null",
  "completed_at": "ISO 8601 datetime|null",
  "result": "JobResult|null",
  "error": "string|null"
}
```

**Example**:
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
  },
  "error": null
}
```

## JobResult Schema

Contains the results of a completed job.

```json
{
  "pages": "integer",
  "tokens": "TokenCounts",
  "extraction_method": "pdfplumber|pymupdf",
  "warnings": ["string"]
}
```

## TokenCounts Schema

Token counts for different encodings.

```json
{
  "openai_cl100k": "integer",
  "openai_p50k": "integer",
  "claude_estimate": "integer"
}
```

## Token Schema

Represents an authentication token.

```json
{
  "token_id": "string",
  "user_id": "string",
  "role": "admin|job_manager|job_writer|job_reader",
  "created_at": "ISO 8601 datetime",
  "expires_at": "ISO 8601 datetime",
  "last_used_at": "ISO 8601 datetime|null",
  "is_active": "boolean"
}
```

**Example**:
```json
{
  "token_id": "tok_abc123",
  "user_id": "app-service",
  "role": "job_writer",
  "created_at": "2025-12-29T10:00:00Z",
  "expires_at": "2026-12-29T10:00:00Z",
  "last_used_at": "2025-12-29T20:00:00Z",
  "is_active": true
}
```

## CreateTokenRequest Schema

Request to create a new token.

```json
{
  "user_id": "string (required)",
  "role": "job_manager|job_writer|job_reader (required)",
  "expires_days": "integer (optional, default: 365)"
}
```

**Example**:
```json
{
  "user_id": "app-service",
  "role": "job_writer",
  "expires_days": 365
}
```

## CreateTokenResponse Schema

Response when token is created.

```json
{
  "token": "string (full token value, shown only once)",
  "token_id": "string",
  "user_id": "string",
  "role": "string",
  "created_at": "ISO 8601 datetime",
  "expires_at": "ISO 8601 datetime"
}
```

**Example**:
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

## JobListResponse Schema

Response for listing jobs.

```json
{
  "jobs": ["Job"],
  "total": "integer",
  "limit": "integer",
  "offset": "integer"
}
```

**Example**:
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

## TokenListResponse Schema

Response for listing tokens.

```json
{
  "tokens": ["Token"],
  "total": "integer"
}
```

## HealthResponse Schema

Health check response.

```json
{
  "status": "healthy|unhealthy",
  "version": "string",
  "redis_connected": "boolean",
  "rate_limiting": "enabled|disabled|degraded",
  "timestamp": "ISO 8601 datetime"
}
```

**Example**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "redis_connected": true,
  "rate_limiting": "enabled",
  "timestamp": "2025-12-29T20:00:00Z"
}
```

## ReadinessResponse Schema

Readiness check response.

```json
{
  "ready": "boolean",
  "services": {
    "database": "connected|disconnected",
    "redis": "connected|disconnected",
    "storage": "available|unavailable"
  }
}
```

**Example**:
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

## ErrorResponse Schema

Standard error response format.

```json
{
  "detail": "string (human-readable error message)",
  "error_code": "string (machine-readable error code, optional)"
}
```

**Examples**:

```json
{
  "detail": "Job not found: abc123xyz9"
}
```

```json
{
  "detail": "Invalid file format. Expected PDF file.",
  "error_code": "INVALID_FILE_FORMAT"
}
```

```json
{
  "detail": "Rate limit exceeded: 100 requests per minute",
  "retry_after": 42
}
```

## Job Status Values

| Status | Description |
|--------|-------------|
| `queued` | Job is queued for processing |
| `running` | Job is currently being processed |
| `complete` | Job completed successfully |
| `failed` | Job failed with error |
| `stopped` | Job was stopped by user |
| `cancelled` | Job was cancelled by user |

## Role Values

| Role | Description |
|------|-------------|
| `admin` | Full system access |
| `job_manager` | Manage all jobs |
| `job_writer` | Create and manage own jobs |
| `job_reader` | Read-only access to granted jobs |

## Extraction Method Values

| Method | Description |
|--------|-------------|
| `pdfplumber` | Primary extraction using pdfplumber |
| `pymupdf` | Fallback extraction using PyMuPDF |

## Data Types

### ISO 8601 Datetime

All datetime values use ISO 8601 format with UTC timezone:

```
2025-12-29T20:00:00Z
```

### Job ID

10-character alphanumeric identifier:

```
abc123xyz9
```

### Token Format

Token string with `pdf2md_` prefix:

```
pdf2md_<base64_encoded_random_256_bits>
```

Example:
```
pdf2md_kF8j2NmP9qR3sT5vU7wX0yZ1aB4cD6eE8fG9hH1iJ3kL5mN7oP9qR1sT3uV5wX7yZ9
```

## Validation Rules

### User ID
- Required for token creation
- Maximum length: 64 characters
- Allowed characters: alphanumeric, dash, underscore

### Job ID
- Auto-generated
- Exactly 10 characters
- Alphanumeric only

### Token Expiration
- Minimum: 1 day
- Maximum: 3650 days (10 years)
- Default: 365 days (1 year)

### File Upload
- Maximum size: 100 MB
- Allowed content type: application/pdf
- Multipart form data required

## OpenAPI Specification

The complete OpenAPI 3.0 specification is available at:

```
https://your-domain.com/openapi.json
```

Interactive documentation:

```
https://your-domain.com/docs (Swagger UI)
https://your-domain.com/redoc (ReDoc)
```