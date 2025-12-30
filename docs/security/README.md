# Security Overview

PDF-to-Markdown implements enterprise-grade security features to protect your data and infrastructure.

## Security Features

### 🔐 Authentication & Authorization

- **Token-Based Authentication**: All API requests require bearer tokens
- **4-Tier RBAC**: admin, job_manager, job_writer, job_reader roles
- **bcrypt Hashing**: Tokens stored as bcrypt hashes
- **Token Expiration**: Configurable token lifetimes

See [RBAC Documentation](rbac.md) for complete details.

### 🛡️ PDF Sandboxing

- **Process Isolation**: All PDF processing in isolated subprocesses
- **Resource Limits**: Memory and CPU limits enforced
- **Timeout Protection**: Automatic termination of long-running conversions
- **Malicious PDF Protection**: Subprocess isolation prevents system compromise

See [Sandboxing Documentation](sandboxing.md) for technical details.

### 🔒 Transport Security

- **TLS 1.3**: Primary encryption protocol
- **TLS 1.2**: Fallback for compatibility
- **mTLS Support**: Mutual TLS for client verification
- **Certificate Options**: Self-signed, custom PKI, Let's Encrypt

See [Certificate Documentation](certificates.md) for setup guides.

### 🔑 Secrets Management

- **Environment Variables**: Secure credential storage
- **No Hardcoded Secrets**: Zero secrets in source code
- **Docker Secrets**: Support for Docker secrets
- **Cloud Secrets**: Integration with Azure Key Vault, AWS Secrets Manager

See [Secrets Management](secrets-management.md) for best practices.

### 🚦 Rate Limiting

- **Role-Based Limits**: Different limits per role
- **Redis Backend**: Distributed rate limiting for scaling
- **Failure Modes**: Configurable closed/open failure behavior
- **DDoS Protection**: Prevent abuse and resource exhaustion

See [API Rate Limiting](../api/rate-limiting.md) for configuration.

## Security Architecture

```
┌─────────────────────────────────────────────┐
│           Client Application                │
└────────────────┬────────────────────────────┘
                 │ HTTPS (TLS 1.3)
                 │ Bearer Token Auth
                 ↓
┌─────────────────────────────────────────────┐
│              nginx Reverse Proxy            │
│  - TLS Termination                          │
│  - Request Validation                       │
│  - mTLS (optional)                          │
└────────────────┬────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────┐
│          FastAPI Application                │
│  - Token Verification                       │
│  - RBAC Enforcement                         │
│  - Rate Limiting (Redis)                    │
└────────────────┬────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────┐
│        PDF Processing Sandbox               │
│  - Isolated Subprocess                      │
│  - Resource Limits                          │
│  - Timeout Protection                       │
└─────────────────────────────────────────────┘
```

## Security Checklist

### Deployment Security

- [ ] Generate strong admin tokens via CLI only
- [ ] Configure TLS 1.3 with valid certificates
- [ ] Enable mTLS for high-security environments
- [ ] Set rate limit fail mode to "closed" in production
- [ ] Use environment variables for all secrets
- [ ] Enable Redis authentication if exposed
- [ ] Configure firewall rules appropriately
- [ ] Implement log monitoring and alerting
- [ ] Regular security updates for dependencies
- [ ] Backup database and certificates

### Operational Security

- [ ] Rotate tokens periodically
- [ ] Monitor failed authentication attempts
- [ ] Review access logs regularly
- [ ] Test backup and recovery procedures
- [ ] Maintain security documentation
- [ ] Train team on security practices
- [ ] Implement incident response plan
- [ ] Regular security audits

### Development Security

- [ ] Never commit secrets to source control
- [ ] Use `.env.example` templates only
- [ ] Review code for security issues
- [ ] Keep dependencies updated
- [ ] Run security scans in CI/CD
- [ ] Follow principle of least privilege
- [ ] Validate all input data
- [ ] Sanitize error messages

## Security Best Practices

### Token Management

1. **Create tokens with appropriate roles**
   - Use job_reader for read-only access
   - Use job_writer for application services
   - Reserve admin for system administrators

2. **Set reasonable expiration periods**
   - Short-lived for high-security environments
   - Long-lived for stable production services
   - Rotate before expiration

3. **Revoke compromised tokens immediately**
   ```bash
   # Revoke token
   curl -X DELETE https://your-domain.com/api/v1/admin/tokens/{token_id} \
     -H "Authorization: Bearer <admin-token>"
   ```

### Network Security

1. **Use TLS in production**
   - Never run without HTTPS in production
   - Use valid certificates (Let's Encrypt free)
   - Configure strong cipher suites

2. **Isolate internal services**
   - Redis should not be publicly accessible
   - Use internal Docker networks
   - Implement firewall rules

3. **Enable mTLS for sensitive deployments**
   - Require client certificates
   - Validate certificate chains
   - Use certificate revocation lists

### Data Protection

1. **Encrypt data in transit**
   - All API communication over HTTPS
   - TLS 1.3 for maximum security

2. **Protect data at rest**
   - Use encrypted storage volumes
   - Secure database backups
   - Encrypt cloud storage

3. **Implement data retention policies**
   - Auto-delete old jobs
   - Purge expired tokens
   - Secure deletion of sensitive data

## Threat Model

### Threats Mitigated

1. **Malicious PDF Files**
   - **Threat**: PDF exploits targeting system
   - **Mitigation**: Subprocess isolation

2. **Unauthorized Access**
   - **Threat**: Unauthorized API access
   - **Mitigation**: Token authentication + RBAC

3. **Token Theft**
   - **Threat**: Stolen authentication tokens
   - **Mitigation**: bcrypt hashing, expiration, revocation

4. **DDoS Attacks**
   - **Threat**: Resource exhaustion
   - **Mitigation**: Rate limiting, Redis backend

5. **Man-in-the-Middle**
   - **Threat**: Traffic interception
   - **Mitigation**: TLS 1.3, mTLS optional

6. **Privilege Escalation**
   - **Threat**: Users gaining elevated access
   - **Mitigation**: RBAC enforcement, admin CLI-only

### Residual Risks

1. **Compromised Admin Token**
   - Create strong admin tokens
   - Rotate regularly
   - Monitor usage

2. **Insider Threats**
   - Audit logging
   - Access reviews
   - Principle of least privilege

3. **Zero-Day Vulnerabilities**
   - Keep dependencies updated
   - Subscribe to security advisories
   - Test patches before deployment

## Compliance Considerations

### GDPR Compliance

- Implement data retention policies
- Provide data export capabilities
- Enable secure data deletion
- Maintain audit logs

### SOC 2 Compliance

- Document security controls
- Implement monitoring and alerting
- Regular security assessments
- Incident response procedures

### HIPAA Compliance (if applicable)

- Enable mTLS for all connections
- Encrypt data at rest and in transit
- Implement comprehensive audit logging
- Business associate agreements

## Security Contacts

### Reporting Security Issues

**Do not** open public issues for security vulnerabilities.

Instead, email security issues to: [CONFIGURE YOUR SECURITY EMAIL]

Include:
- Description of vulnerability
- Steps to reproduce
- Potential impact
- Suggested fixes (if any)

### Security Advisories

Subscribe to security advisories for dependencies:
- [FastAPI Security](https://github.com/tiangolo/fastapi/security)
- [Pydantic Security](https://github.com/pydantic/pydantic/security)
- [Python Security](https://www.python.org/news/security/)

## Security Resources

- [RBAC System](rbac.md) - Role-based access control
- [PDF Sandboxing](sandboxing.md) - Process isolation
- [Certificates](certificates.md) - TLS configuration
- [Secrets Management](secrets-management.md) - Credential handling
- [Rate Limiting](../api/rate-limiting.md) - Request throttling

---

**Security is a continuous process. Review and update security measures regularly.**