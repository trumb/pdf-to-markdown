# Role-Based Access Control (RBAC)

Complete reference for the 4-tier RBAC system.

## Overview

PDF-to-Markdown implements a hierarchical role-based access control system with four distinct roles, each with specific permissions and use cases.

## Roles

### admin

**Full system access and control**

**Capabilities:**
- Create, revoke, disable, and manage all non-admin tokens
- View all jobs regardless of ownership
- Control all jobs (stop, cancel, throttle)
- View all API usage and statistics
- Configure system settings
- Access all endpoints without restriction

**Limitations:**
- Admin tokens can ONLY be created via CLI (not API)
- Cannot revoke other admin tokens (security measure)
- Cannot be created through the API

**Rate Limit**: 1000 requests/minute

**Use Cases:**
- System administrators
- DevOps engineers
- Security team members
- Platform operations

**Creating Admin Tokens:**
```bash
# CLI only - for security
pdf2md admin create-token --role admin --user-id admin-alice

# Output
Token created successfully:
pdf2md_kF8j2NmP9qR3sT5vU7wX...

User ID: admin-alice
Role: admin
Expires: 2026-12-29
```

---

### job_manager

**Manage all jobs without token administration**

**Capabilities:**
- View all jobs (regardless of owner)
- Control all jobs:
  - Stop running jobs
  - Cancel queued jobs
  - Throttle job processing speed
- Create new conversion jobs
- Download results from any job

**Limitations:**
- Cannot create, revoke, or manage tokens
- Cannot grant job access to other users
- Cannot perform admin operations

**Rate Limit**: 500 requests/minute

**Use Cases:**
- Operations teams managing job queues
- System monitoring services
- Job orchestration systems
- Queue management tools

**Creating job_manager Tokens:**
```bash
# CLI (as admin)
pdf2md admin create-token --role job_manager --user-id ops-team

# API (as admin)
curl -X POST https://your-domain.com/api/v1/admin/tokens \
  -H "Authorization: Bearer <admin-token>" \
  -d '{"user_id": "ops-team", "role": "job_manager"}'
```

---

### job_writer

**Create and manage own jobs**

**Capabilities:**
- Create new conversion jobs
- View own jobs and jobs with granted access
- Manage own jobs:
  - Stop own running jobs
  - Cancel own queued jobs
- Grant job_reader access to own jobs
- Download results from own jobs or granted jobs

**Limitations:**
- Cannot view or control other users' jobs
- Cannot throttle jobs (even own jobs)
- Cannot manage tokens
- Cannot grant access to jobs they don't own

**Rate Limit**: 100 requests/minute

**Use Cases:**
- Application services
- API consumers
- Document processing systems
- Automated workflows
- User-facing applications

**Creating job_writer Tokens:**
```bash
# CLI (as admin)
pdf2md admin create-token --role job_writer --user-id app-service

# API (as admin)
curl -X POST https://your-domain.com/api/v1/admin/tokens \
  -H "Authorization: Bearer <admin-token>" \
  -d '{"user_id": "app-service", "role": "job_writer", "expires_days": 365}'
```

---

### job_reader

**Read-only access to granted jobs**

**Capabilities:**
- View jobs with explicitly granted access
- Download results from granted jobs
- Check job status for granted jobs

**Limitations:**
- Cannot create jobs
- Cannot modify or control any jobs
- Cannot grant access to others
- Cannot view jobs without explicit access grant
- Read-only access only

**Rate Limit**: 50 requests/minute

**Use Cases:**
- Reporting services
- Auditors
- Downstream consumers
- Monitoring dashboards
- Analytics systems

**Creating job_reader Tokens:**
```bash
# CLI (as admin)
pdf2md admin create-token --role job_reader --user-id reporting-service

# API (as admin)
curl -X POST https://your-domain.com/api/v1/admin/tokens \
  -H "Authorization: Bearer <admin-token>" \
  -d '{"user_id": "reporting-service", "role": "job_reader"}'
```

---

## Permission Matrix

| Operation | admin | job_manager | job_writer | job_reader |
|-----------|-------|-------------|------------|------------|
| **Job Operations** |
| Create job | ✅ | ✅ | ✅ | ❌ |
| View own jobs | ✅ | ✅ | ✅ | N/A |
| View all jobs | ✅ | ✅ | ❌ | ❌ |
| View granted jobs | ✅ | ✅ | ✅ | ✅ |
| Stop own jobs | ✅ | ✅ | ✅ | ❌ |
| Stop any job | ✅ | ✅ | ❌ | ❌ |
| Cancel own jobs | ✅ | ✅ | ✅ | ❌ |
| Cancel any job | ✅ | ✅ | ❌ | ❌ |
| Throttle any job | ✅ | ✅ | ❌ | ❌ |
| Download own results | ✅ | ✅ | ✅ | N/A |
| Download granted results | ✅ | ✅ | ✅ | ✅ |
| Download any results | ✅ | ✅ | ❌ | ❌ |
| **Access Control** |
| Grant job access | ✅ | ✅ | ✅ (own) | ❌ |
| **Token Management** |
| Create tokens | ✅ | ❌ | ❌ | ❌ |
| View tokens | ✅ | ❌ | ❌ | ❌ |
| Revoke tokens | ✅ | ❌ | ❌ | ❌ |
| Disable tokens | ✅ | ❌ | ❌ | ❌ |

## Access Delegation

### Granting Access

job_writer users can grant job_reader access to their jobs:

```bash
# Grant access to a job
curl -X POST https://your-domain.com/api/v1/jobs/abc123xyz9/grant-access \
  -H "Authorization: Bearer <job_writer_token>" \
  -d '{"user_id": "reporting-service"}'
```

**Access Grant Rules:**
- Only job owners can grant access
- job_manager and admin can grant access to any job
- job_writer can only grant access to own jobs
- Only job_reader role can be granted (not job_writer or higher)
- Grants are permanent until job deletion

### Access Scenarios

**Scenario 1: Application with Reporting**
```
1. app-service (job_writer) creates conversion jobs
2. app-service grants access to reporting-service (job_reader)
3. reporting-service can view job status and download results
```

**Scenario 2: Multi-tenant System**
```
1. tenant-a-service (job_writer) creates jobs
2. tenant-b-service (job_writer) cannot see tenant-a jobs
3. ops-team (job_manager) can see and manage all jobs
```

## RBAC Implementation

### Token Validation

Every API request:
1. Validates token format
2. Checks token exists and is active
3. Verifies token hasn't expired
4. Loads associated role
5. Enforces role permissions

### Authorization Checks

```python
# Pseudocode for authorization
def check_permission(token, operation, resource):
    role = get_role(token)
    
    if role == "admin":
        return True  # Admin can do everything
    
    if operation == "view_job":
        if role == "job_manager":
            return True  # Can view all jobs
        if role in ["job_writer", "job_reader"]:
            return is_owner(token, resource) or has_granted_access(token, resource)
    
    if operation == "control_job":
        if role == "job_manager":
            return True  # Can control all jobs
        if role == "job_writer":
            return is_owner(token, resource)
    
    return False
```

## Security Considerations

### Principle of Least Privilege

Always use the minimum required role:

| Use Case | Recommended Role |
|----------|------------------|
| Production app creating PDFs | job_writer |
| Read-only monitoring | job_reader |
| Operations/support team | job_manager |
| Platform administration | admin |

### Token Security

1. **Admin Tokens**: CLI-only creation prevents accidental exposure
2. **Token Rotation**: Rotate tokens before expiration
3. **Token Revocation**: Immediately revoke compromised tokens
4. **Monitoring**: Track token usage for anomalies

### Common Mistakes

❌ **Don't:**
- Use admin tokens for application services
- Share tokens between different services
- Hard-code tokens in applications
- Give job_writer access when job_reader is sufficient

✅ **Do:**
- Create separate tokens for each service
- Use environment variables for tokens
- Set appropriate expiration times
- Monitor token usage

## Role Selection Guide

### When to Use admin

**Use admin when:**
- Managing system configuration
- Creating/revoking tokens
- Troubleshooting access issues
- Emergency operations

**Don't use admin for:**
- Regular application operations
- Automated services
- Third-party integrations

### When to Use job_manager

**Use job_manager when:**
- Managing job queues
- Monitoring all system jobs
- Operations team dashboards
- System health monitoring

**Don't use job_manager for:**
- Regular job creation services
- Read-only reporting
- User-facing applications

### When to Use job_writer

**Use job_writer when:**
- Application services creating jobs
- User-facing conversion services
- Automated workflows
- Integration services

**Don't use job_writer for:**
- Read-only monitoring
- Reporting dashboards
- Audit services

### When to Use job_reader

**Use job_reader when:**
- Read-only reporting
- Analytics dashboards
- Audit systems
- Monitoring tools

**Don't use job_reader for:**
- Services that need to create jobs
- Interactive applications

## Examples

### Example 1: Application Service

```bash
# Create job_writer token for app
TOKEN=$(pdf2md admin create-token --role job_writer --user-id my-app)

# App creates and manages own jobs
curl -X POST https://your-domain.com/api/v1/convert \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@document.pdf"
```

### Example 2: Operations Dashboard

```bash
# Create job_manager token for ops
TOKEN=$(pdf2md admin create-token --role job_manager --user-id ops-dashboard)

# Dashboard views all jobs
curl https://your-domain.com/api/v1/jobs \
  -H "Authorization: Bearer $TOKEN"

# Can control any job
curl -X POST https://your-domain.com/api/v1/jobs/abc123xyz9/throttle \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"throttle_percent": 50}'
```

### Example 3: Reporting Service

```bash
# Create job_reader token for reporting
READER_TOKEN=$(pdf2md admin create-token --role job_reader --user-id reporting)

# App grants access to its jobs
curl -X POST https://your-domain.com/api/v1/jobs/abc123xyz9/grant-access \
  -H "Authorization: Bearer $WRITER_TOKEN" \
  -d '{"user_id": "reporting"}'

# Reporting service can now view job
curl https://your-domain.com/api/v1/jobs/abc123xyz9 \
  -H "Authorization: Bearer $READER_TOKEN"
```

## Troubleshooting

### Access Denied Errors

**403 Forbidden**: Insufficient permissions

**Check:**
1. Verify token role matches operation requirements
2. Confirm job ownership for job_writer operations
3. Verify access grants for job_reader operations

### Token Creation Fails

**Admin Token Creation via API**: Not allowed

**Solution**: Create admin tokens via CLI only

### Can't See Jobs

**job_writer/job_reader**: Can only see own or granted jobs

**Solution**:
- Use job_manager for viewing all jobs
- Request access grant from job owner
- Use admin token for full visibility

---

For more security information, see [Security Overview](README.md).