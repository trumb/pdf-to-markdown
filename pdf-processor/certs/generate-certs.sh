#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

strDomain="${1:-localhost}"
intDays=365

echo "🔐 Generating self-signed TLS certificates for ${strDomain}..."
echo ""

# Generate private key (2048-bit RSA)
echo "  → Generating private key..."
openssl genrsa -out privkey.pem 2048

# Generate certificate signing request
echo "  → Generating CSR..."
openssl req -new -key privkey.pem -out cert.csr \
    -subj "/C=US/ST=Local/L=Local/O=PDF2MD/CN=${strDomain}"

# Generate self-signed certificate
echo "  → Generating self-signed certificate (${intDays} days)..."
openssl x509 -req -days "${intDays}" -in cert.csr \
    -signkey privkey.pem -out fullchain.pem

# Generate DH parameters for Perfect Forward Secrecy
echo "  → Generating DH parameters (this may take a minute)..."
openssl dhparam -out dhparam.pem 2048

# Clean up CSR
rm cert.csr

# Set permissions
chmod 600 privkey.pem
chmod 644 fullchain.pem
chmod 644 dhparam.pem

echo ""
echo "✅ TLS certificates generated successfully!"
echo ""
echo "📁 Files created in deploy/certs/:"
echo "   - privkey.pem     (private key)"
echo "   - fullchain.pem   (certificate)"
echo "   - dhparam.pem     (DH parameters)"
echo ""
echo "⚠️  Certificate Details:"
openssl x509 -in fullchain.pem -noout -subject -dates
echo ""
echo "⚠️  Browser Warning:"
echo "   Self-signed certificates are NOT trusted by browsers."
echo "   You'll see a security warning when accessing https://${strDomain}:8443"
echo "   Click 'Advanced' → 'Proceed to site (unsafe)' to continue."
echo ""
echo "🚀 Next steps:"
echo "   1. Generate htpasswd: ./scripts/make-htpasswd.sh admin 'your-password'"
echo "   2. Start stack: ./scripts/up.sh"
echo ""