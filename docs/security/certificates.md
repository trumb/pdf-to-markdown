# TLS Certificates

Complete guide to TLS certificate configuration for PDF-to-Markdown.

## Overview

PDF-to-Markdown supports multiple certificate options:
- Self-signed certificates (development)
- Let's Encrypt (production, free)
- Custom PKI (enterprise)
- Mutual TLS / mTLS (high security)

## TLS Configuration

### TLS Protocols

**Supported**:
- TLS 1.3 (Primary, recommended)
- TLS 1.2 (Fallback for compatibility)

**Not Supported**:
- TLS 1.1 (Deprecated)
- TLS 1.0 (Deprecated)
- SSL 3.0 (Insecure)
- SSL 2.0 (Insecure)

### Cipher Suites

nginx configuration uses Mozilla Modern compatibility:

```nginx
ssl_protocols TLSv1.3 TLSv1.2;
ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
ssl_prefer_server_ciphers off;
```

## Certificate Options

### Option 1: Self-Signed Certificates

**Best for**: Development, testing, internal networks

**Security Level**: Low (browser warnings)

**Generate Self-Signed Certificate**:

```bash
# Using provided script
./certs/generate-selfsigned.sh

# Manual generation
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout certs/selfsigned-key.pem \
  -out certs/selfsigned-cert.pem \
  -subj "/CN=localhost"
```

**nginx Configuration**:
```nginx
ssl_certificate /etc/nginx/certs/selfsigned-cert.pem;
ssl_certificate_key /etc/nginx/certs/selfsigned-key.pem;
```

**Limitations**:
- Browser security warnings
- Not trusted by clients
- Not suitable for production
- Manual trust configuration required

---

### Option 2: Let's Encrypt

**Best for**: Production deployments, public-facing services

**Security Level**: High (publicly trusted)

**Requirements**:
- Public domain name
- Port 80 accessible for validation
- Port 443 for HTTPS

**Setup Let's Encrypt**:

```bash
# Install certbot
sudo apt-get install certbot

# Obtain certificate
sudo certbot certonly --standalone \
  -d pdf2md.example.com \
  --email admin@example.com \
  --agree-tos

# Certificates stored in:
# /etc/letsencrypt/live/pdf2md.example.com/fullchain.pem
# /etc/letsencrypt/live/pdf2md.example.com/privkey.pem
```

**nginx Configuration**:
```nginx
ssl_certificate /etc/letsencrypt/live/pdf2md.example.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/pdf2md.example.com/privkey.pem;
```

**Auto-Renewal**:
```bash
# Test renewal
sudo certbot renew --dry-run

# Set up auto-renewal (systemd timer)
sudo systemctl enable certbot-renew.timer
sudo systemctl start certbot-renew.timer

# Verify timer
sudo systemctl list-timers certbot-renew
```

**Docker Integration**:
```yaml
# docker-compose.yml
services:
  nginx:
    volumes:
      - /etc/letsencrypt:/etc/letsencrypt:ro
    ports:
      - "80:80"   # For renewal validation
      - "443:443"
```

---

### Option 3: Custom PKI

**Best for**: Enterprise environments, internal CA

**Security Level**: High (enterprise controlled)

**Requirements**:
- Internal Certificate Authority
- Private key infrastructure
- Certificate distribution system

**Generate Certificate Signing Request (CSR)**:

```bash
# Generate private key
openssl genrsa -out certs/server-key.pem 2048

# Generate CSR
openssl req -new -key certs/server-key.pem \
  -out certs/server-csr.pem \
  -subj "/CN=pdf2md.internal.com/O=YourOrg"

# Submit CSR to your CA for signing
# Receive signed certificate: server-cert.pem
```

**nginx Configuration**:
```nginx
ssl_certificate /etc/nginx/certs/server-cert.pem;
ssl_certificate_key /etc/nginx/certs/server-key.pem;
ssl_client_certificate /etc/nginx/certs/ca-chain.pem;  # Optional for mTLS
```

**Certificate Chain**:
```bash
# Combine certificate with intermediate certs
cat server-cert.pem intermediate.pem > fullchain.pem
```

---

### Option 4: Mutual TLS (mTLS)

**Best for**: High-security environments, service-to-service

**Security Level**: Very High (client authentication required)

**Requirements**:
- Server certificates (from Option 2 or 3)
- Client certificates
- Certificate Authority chain

**Setup mTLS**:

**1. Generate Client Certificates**:
```bash
# Client private key
openssl genrsa -out certs/client-key.pem 2048

# Client CSR
openssl req -new -key certs/client-key.pem \
  -out certs/client-csr.pem \
  -subj "/CN=client-app/O=YourOrg"

# Sign with CA (or submit to CA)
openssl x509 -req -in certs/client-csr.pem \
  -CA certs/ca-cert.pem \
  -CAkey certs/ca-key.pem \
  -CAcreateserial \
  -out certs/client-cert.pem \
  -days 365
```

**2. Configure nginx for mTLS**:
```nginx
server {
    listen 443 ssl;
    
    # Server certificates
    ssl_certificate /etc/nginx/certs/server-cert.pem;
    ssl_certificate_key /etc/nginx/certs/server-key.pem;
    
    # Client certificate verification
    ssl_client_certificate /etc/nginx/certs/ca-cert.pem;
    ssl_verify_client on;
    ssl_verify_depth 2;
    
    # Rest of configuration...
}
```

**3. Client Usage**:
```bash
# curl with client certificate
curl https://pdf2md.example.com/health \
  --cert certs/client-cert.pem \
  --key certs/client-key.pem \
  --cacert certs/ca-cert.pem
```

**Optional**: Selective mTLS
```nginx
# Require mTLS only for certain paths
location /api/v1/admin {
    ssl_verify_client on;
}

location /api/v1/jobs {
    ssl_verify_client optional;
}
```

---

## Certificate Management

### Certificate Storage

**Development**:
```
certs/
├── selfsigned-cert.pem
├── selfsigned-key.pem
└── .gitignore  # Never commit private keys!
```

**Production**:
```
/etc/ssl/certs/pdf2md/
├── fullchain.pem  # Certificate + chain
├── privkey.pem    # Private key (600 permissions)
└── ca-chain.pem   # CA certificates (for mTLS)
```

### File Permissions

```bash
# Private keys: read-only by root
chmod 600 /etc/ssl/certs/pdf2md/privkey.pem
chown root:root /etc/ssl/certs/pdf2md/privkey.pem

# Certificates: readable by nginx user
chmod 644 /etc/ssl/certs/pdf2md/fullchain.pem
chown root:nginx /etc/ssl/certs/pdf2md/fullchain.pem
```

### Certificate Rotation

**Let's Encrypt**: Auto-renewal every 60 days
**Custom PKI**: Rotate before expiration (typically 1 year)

**Rotation Process**:
```bash
# 1. Obtain new certificate
certbot renew

# 2. Reload nginx (zero-downtime)
docker exec pdf2md-nginx nginx -s reload

# 3. Verify new certificate
openssl s_client -connect localhost:443 -servername pdf2md.example.com
```

### Certificate Monitoring

**Check Expiration**:
```bash
# Check certificate expiration
openssl x509 -in certs/cert.pem -noout -enddate

# Check via HTTPS
echo | openssl s_client -connect pdf2md.example.com:443 2>/dev/null | \
  openssl x509 -noout -enddate
```

**Automated Monitoring**:
```bash
# Add to cron
0 0 * * * /usr/local/bin/check-cert-expiry.sh
```

## Docker Configuration

### Standard TLS

```yaml
# docker-compose.yml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
      - "80:80"  # For Let's Encrypt validation
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro  # Let's Encrypt
    environment:
      - TLS_CERT_PATH=/etc/nginx/certs/fullchain.pem
      - TLS_KEY_PATH=/etc/nginx/certs/privkey.pem
```

### mTLS Configuration

```yaml
# docker-compose.yml
services:
  nginx:
    volumes:
      - ./certs/ca-cert.pem:/etc/nginx/certs/ca-cert.pem:ro
    environment:
      - MTLS_ENABLED=true
      - CLIENT_CA_PATH=/etc/nginx/certs/ca-cert.pem
```

## Testing

### Test TLS Connection

```bash
# Basic connectivity
curl -v https://pdf2md.example.com/health

# Check TLS version
curl --tlsv1.3 https://pdf2md.example.com/health
curl --tlsv1.2 https://pdf2md.example.com/health

# Check certificate
openssl s_client -connect pdf2md.example.com:443 -servername pdf2md.example.com
```

### Test mTLS

```bash
# With client certificate
curl https://pdf2md.example.com/health \
  --cert certs/client-cert.pem \
  --key certs/client-key.pem

# Without client certificate (should fail)
curl https://pdf2md.example.com/health
# Expected: SSL certificate problem / peer did not return a certificate
```

### SSL Labs Test

For public deployments:
```
https://www.ssllabs.com/ssltest/analyze.html?d=pdf2md.example.com
```

Target grade: **A+**

## Troubleshooting

### Issue: Certificate not trusted

**Cause**: Self-signed or unknown CA

**Solution**:
- Use Let's Encrypt for public services
- Add CA to system trust store
- Use `--insecure` flag (development only)

### Issue: Certificate expired

**Check**:
```bash
openssl x509 -in cert.pem -noout -dates
```

**Solution**: Renew certificate and reload nginx

### Issue: Private key mismatch

**Check**:
```bash
# Certificate modulus
openssl x509 -in cert.pem -noout -modulus | md5sum

# Key modulus (should match)
openssl rsa -in key.pem -noout -modulus | md5sum
```

### Issue: mTLS client rejected

**Check**:
```bash
# Verify client cert
openssl verify -CAfile ca-cert.pem client-cert.pem

# Check nginx logs
docker logs pdf2md-nginx | grep "ssl"
```

## Security Best Practices

1. **Never commit private keys** to source control
2. **Use strong keys**: Minimum 2048-bit RSA or 256-bit ECDSA
3. **Enable TLS 1.3** where possible
4. **Disable weak ciphers** and protocols
5. **Monitor certificate expiration**
6. **Rotate certificates** before expiration
7. **Use mTLS** for high-security environments
8. **Regular security audits** with SSL Labs

## Certificate Checklist

- [ ] TLS 1.3 enabled
- [ ] TLS 1.2 as fallback only
- [ ] Strong cipher suites configured
- [ ] Certificates not expired
- [ ] Auto-renewal configured (Let's Encrypt)
- [ ] Private keys secured (600 permissions)
- [ ] Certificate monitoring in place
- [ ] mTLS configured (if required)
- [ ] Client certificates distributed (if mTLS)
- [ ] SSL Labs grade A+ (public deployments)

---

For more security information, see [Security Overview](README.md).