#!/bin/bash
set -e

CERT_DIR="./certs"
DOMAIN="api.pdf2md.local"
DAYS=365

echo "🔐 Generating self-signed certificate for $DOMAIN..."

# Create cert directory if it doesn't exist
mkdir -p "$CERT_DIR"

# Generate private key
echo "  → Generating private key..."
openssl genrsa -out "$CERT_DIR/privkey.pem" 2048

# Generate certificate signing request
echo "  → Generating CSR..."
openssl req -new -key "$CERT_DIR/privkey.pem" -out "$CERT_DIR/cert.csr" \
    -subj "/C=US/ST=State/L=City/O=PDF2MD/CN=$DOMAIN"

# Generate self-signed certificate
echo "  → Generating self-signed certificate..."
openssl x509 -req -days $DAYS -in "$CERT_DIR/cert.csr" \
    -signkey "$CERT_DIR/privkey.pem" -out "$CERT_DIR/fullchain.pem"

# Generate DH parameters
echo "  → Generating DH parameters (this may take a while)..."
openssl dhparam -out "$CERT_DIR/dhparam.pem" 2048

# Clean up CSR
rm "$CERT_DIR/cert.csr"

# Set permissions
chmod 600 "$CERT_DIR/privkey.pem"
chmod 644 "$CERT_DIR/fullchain.pem"
chmod 644 "$CERT_DIR/dhparam.pem"

echo ""
echo "✅ Self-signed certificate generated successfully!"
echo ""
echo "📁 Files created:"
echo "   - $CERT_DIR/privkey.pem     (private key)"
echo "   - $CERT_DIR/fullchain.pem   (certificate)"
echo "   - $CERT_DIR/dhparam.pem     (DH parameters)"
echo ""
echo "⚠️  Certificate Details:"
openssl x509 -in "$CERT_DIR/fullchain.pem" -noout -subject -dates
echo ""
echo "⚠️  Browser Warning:"
echo "   Self-signed certificates are not trusted by browsers."
echo "   You'll see a security warning when accessing https://$DOMAIN"
echo "   Click 'Advanced' → 'Proceed to site (unsafe)' to continue."
echo ""
echo "🚀 Start the stack:"
echo "   docker-compose up -d"