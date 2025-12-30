# API Reference

Complete reference for the PDF-to-Markdown REST API.

## Base URL

```
https://your-domain.com/api/v1
```

## Authentication

All API requests require Bearer token authentication:

```bash
Authorization: Bearer pdf2md_YOUR_TOKEN
```

See [Authentication Guide](authentication.md) for token management.

## Rate Limiting

Rate limits vary by role and are enforced using Redis for distributed deployments:

| Role | Requests/Minute |
|------|----------------|
| admin | 1000 |
| job_manager | 500 |
| job_writer | 100 |
| job_reader | 50 |

See [Rate Limiting Guide](rate-limiting.md) for configuration details.

## Endpoints

### Job Management

- [POST /api/v1/convert](endpoints.md#post-convert) - Submit PDF for conversion
- [GET /api/v1/jobs](endpoints.md#get-jobs) - List jobs
- [GET /api/v1/jobs/{id}](endpoints.md#get-job) - Get job status
- [GET /api/v1/jobs/{id}/result](endpoints.md#get-result) - Download result
- [POST /api/v1/jobs/{id}/stop](endpoints.md#post-stop) - Stop job
- [POST /api/v1/jobs/{id}/cancel](endpoints.md#post-cancel) - Cancel job
- [POST /api/v1/jobs/{id}/throttle](endpoints.md#post-throttle) - Throttle job
- [POST /api/v1/jobs/{id}/grant-access](endpoints.md#post-grant) - Grant job access

### Admin Operations

- [POST /api/v1/admin/tokens](endpoints.md#post-token) - Create token
- [GET /api/v1/admin/tokens](endpoints.md#get-tokens) - List tokens
- [DELETE /api/v1/admin/tokens/{id}](endpoints.md#delete-token) - Revoke token
- [PATCH /api/v1/admin/tokens/{id}](endpoints.md#patch-token) - Update token

### Health Checks

- [GET /health](endpoints.md#get-health) - Health check
- [GET /ready](endpoints.md#get-ready) - Readiness check

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Invalid/missing token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

## Request/Response Format

All requests and responses use JSON format unless otherwise specified.

See [Schemas](schemas.md) for complete data structures.

## Examples

See [Usage Examples](../guides/api-usage.md) for detailed code samples in multiple languages.

## OpenAPI/Swagger

Interactive API documentation is available at:

```
https://your-domain.com/docs
```

Alternative ReDoc documentation:

```
https://your-domain.com/redoc
```