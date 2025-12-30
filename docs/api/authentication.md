# Authentication

PDF-to-Markdown uses token-based authentication with role-based access control (RBAC).

## Token Format

Tokens follow this format:

```
pdf2md_<base64_encoded_random_256_bits>
```

**Example**: `pdf2md_kF8j2NmP9qR3sT5vU7wX0yZ1aB4cD6eE8fG9hH1iJ3kL5mN7oP9qR1sT3uV5wX7yZ9`

## Obtaining Tokens

### Admin Tokens (CLI Only)

Admin tokens can only be created via CLI for security:

```bash
pdf2md admin create-token --role admin --user-id admin-alice
```

**Output**:
```
Token created successfully:
pdf2md_kF8j2NmP9qR3sT5vU7wX...

User ID: admin-alice
Role: admin
Expires: 2026-12-29
```

### Other Tokens (CLI or API)

Non-admin tokens can be created via CLI or API:

**CLI**:
```bash
pdf2md admin create-token --role job_writer --user-id app-service --expires-days 365
```

**API**:
```bash
curl -X POST https://your-domain.com/api/v1/admin/tokens \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "app-service",
    "role": "job_writer",
    "expires_days": 365
  }'
```

## Using Tokens

Include tokens in the `Authorization` header:

```bash
curl https://your-domain.com/api/v1/jobs \
  -H "Authorization: Bearer pdf2md_YOUR_TOKEN"
```

## Token Roles

| Role | Description |
|------|-------------|
| **admin** | Full system access, manage tokens, view all jobs |
| **job_manager** | Control all jobs, cannot manage tokens |
| **job_writer** | Create and manage own jobs, grant reader access |
| **job_reader** | Read-only access to granted jobs |

See [RBAC Documentation](../security/rbac.md) for complete permissions.

## Token Management

### List Tokens

```bash
GET /api/v1/admin/tokens
```

**Response**:
```json
{
  "tokens": [
    {
      "id": "tok_abc123",
      "user_id": "app-service",
      "role": "job_writer",
      "created_at": "2025-12-29T10:00:00Z",
      "expires_at": "2026-12-29T10:00:00Z",
      "last_used_at": "2025-12-29T20:00:00Z",
      "is_active": true
    }
  ]
}
```

### Revoke Token

```bash
DELETE /api/v1/admin/tokens/{token_id}
```

### Disable Token

```bash
PATCH /api/v1/admin/tokens/{token_id}
-d '{"is_active": false}'
```

## Token Security

### Storage

- **DO NOT** commit tokens to source control
- Store tokens in environment variables or secrets management
- Use different tokens for different environments

### Best Practices

1. **Rotation**: Rotate tokens periodically
2. **Expiration**: Set appropriate expiration dates
3. **Least Privilege**: Use minimum required role
4. **Monitoring**: Monitor token usage via logs

### Token Hashing

Tokens are stored as bcrypt hashes in the database. The plain-text token is only shown once during creation.

## Error Responses

### 401 Unauthorized

**Missing token**:
```json
{
  "detail": "Not authenticated"
}
```

**Invalid token**:
```json
{
  "detail": "Invalid authentication credentials"
}
```

**Expired token**:
```json
{
  "detail": "Token has expired"
}
```

### 403 Forbidden

**Insufficient permissions**:
```json
{
  "detail": "Insufficient permissions for this operation"
}
```

## Example: Creating and Using a Token

```bash
# 1. Create token (as admin)
TOKEN=$(pdf2md admin create-token --role job_writer --user-id my-app | grep "pdf2md_" | awk '{print $1}')

# 2. Store securely
export PDF2MD_TOKEN="$TOKEN"

# 3. Use token
curl -X POST https://your-domain.com/api/v1/convert \
  -H "Authorization: Bearer $PDF2MD_TOKEN" \
  -F "file=@document.pdf"
```

## Troubleshooting

### Token Not Working

1. Verify token is complete (starts with `pdf2md_`)
2. Check token hasn't expired
3. Verify token is active
4. Ensure role has required permissions

### Rate Limiting

If receiving 429 errors, you're hitting rate limits. See [Rate Limiting](rate-limiting.md) for details.