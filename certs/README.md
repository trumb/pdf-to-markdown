# Certificate Management

This directory contains TLS certificates for the PDF2MD API.

## Quick Start

### Development (Self-Signed)

```bash
# Generate self-signed certificate
chmod +x certs/generate-selfsigned.sh
./certs/generate-selfsigned.sh
```

### Production (Let's Encrypt)

```bash
# Setup Let's Encrypt
chmod +x scripts/setup-letsencrypt.sh
sudo ./scripts/setup-letsencrypt.sh
```

## Required Files

The following files must be present for nginx to start:

- `fullchain.pem` - Server certificate (public)
- `privkey.pem` - Private key (keep secure!)
- `dhparam.pem` - Diffie-Hellman parameters

## Certificate Types

### 1. Self-Signed (Development)

Good for:
- Local development
- Testing TLS configuration
- Internal networks

⚠️ **Not trusted** by browsers - you'll see security warnings

```bash
./certs/generate-selfsigned.sh
```

### 2. Let's Encrypt (Production)

Good for:
- Public-facing APIs
- Production deployments
- Automatic renewal

✅ **Trusted** by all major browsers

```bash
sudo ./scripts/setup-letsencrypt.sh
```

Requirements:
- Domain name pointing to your server
- Port 80 accessible (for ACME challenge)
- Valid email address

### 3. Custom PKI (Enterprise)

Good for:
- Corporate environments
- mTLS client authentication
- Custom certificate authorities

Place your certificates in this directory:
```
certs/
├── fullchain.pem  (your CA + server cert)
├── privkey.pem    (server private key)
├── ca-cert.pem    (CA certificate for mTLS)
└── dhparam.pem    (DH parameters)
```

## File Permissions

⚠️ **Security**: Private keys must have restrictive permissions

```bash
chmod 600 certs/privkey.pem
chmod 644 certs/fullchain.pem
chmod 644 certs/dhparam.pem
```

## Auto-Renewal

Let's Encrypt certificates expire after 90 days. Auto-renewal is handled by:

```bash
# Systemd timer (runs daily)
sudo systemctl enable pdf2md-renew.timer
sudo systemctl start pdf2md-renew.timer

# Manual renewal
sudo ./scripts/renew-certs.sh
```

## Verification

### Check Certificate

```bash
# View certificate details
openssl x509 -in certs/fullchain.pem -text -noout

# Check expiry date
openssl x509 -in certs/fullchain.pem -noout -dates
```

### Test TLS Configuration

```bash
# Test TLS 1.3
openssl s_client -connect localhost:443 -tls1_3

# Test with curl
curl -v https://localhost/health

# Check certificate chain
curl -v https://localhost 2>&1 | grep -A 10 "Server certificate"
```

## mTLS (Optional)

For client certificate authentication:

1. Create `ca-cert.pem` with your CA certificate
2. Enable mTLS in `nginx/conf.d/mtls.conf`
3. Restart nginx

Clients must present valid certificates signed by your CA.

## Troubleshooting

### nginx won't start

```bash
# Check certificate files exist
ls -la certs/

# Verify nginx config
docker-compose exec nginx nginx -t
```

### Certificate expired

```bash
# Renew Let's Encrypt
sudo ./scripts/renew-certs.sh

# Or regenerate self-signed
./certs/generate-selfsigned.sh
docker-compose restart nginx
```

### Browser security warnings

If using self-signed certificates:
1. Click "Advanced"
2. Click "Proceed to site (unsafe)"
3. Or add certificate to your OS trust store

## Security Notes

- Never commit `privkey.pem` to git
- Use strong passwords if encrypting keys
- Rotate certificates before expiry
- Monitor certificate expiry dates
- Use proper file permissions (600 for private keys)
- Consider using mTLS for API-to-API communication

## Certificate Expiry Calendar

Set reminders:
- **Self-signed**: Check annually
- **Let's Encrypt**: Auto-renewed at 60 days (30 days before expiry)
- **Custom PKI**: Check with your CA

## Support

For issues:
1. Check nginx logs: `docker-compose logs nginx`
2. Verify certificate: `openssl x509 -in certs/fullchain.pem -text -noout`
3. Test TLS: `openssl s_client -connect localhost:443`