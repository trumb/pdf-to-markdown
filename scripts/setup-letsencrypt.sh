#!/bin/bash
set -e

# Configuration
DOMAIN="${1:-api.pdf2md.com}"
EMAIL="${2:-admin@pdf2md.com}"
CERT_DIR="./certs"
LETSENCRYPT_DIR="./letsencrypt"

echo "🔐 Setting up Let's Encrypt for $DOMAIN..."
echo ""

# Check if domain is provided
if [ "$DOMAIN" = "api.pdf2md.com" ]; then
    echo "⚠️  Warning: Using default domain 'api.pdf2md.com'"
    echo "   Please provide your actual domain:"
    echo "   Usage: $0 your-domain.com your-email@domain.com"
    echo ""
    read -p "Continue with default? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if certbot is installed
if ! command -v certbot &> /dev/null; then
    echo "📦 Installing certbot..."
    if [ -f /etc/debian_version ]; then
        sudo apt-get update
        sudo apt-get install -y certbot
    elif [ -f /etc/redhat-release ]; then
        sudo yum install -y certbot
    else
        echo "❌ Unable to install certbot automatically"
        echo "   Please install certbot manually and re-run this script"
        exit 1
    fi
fi

# Create ACME challenge directory
mkdir -p acme-challenge

# Stop nginx temporarily
echo "🛑 Stopping nginx..."
docker-compose stop nginx || true

# Obtain certificate
echo "📜 Obtaining certificate from Let's Encrypt..."
echo "   Domain: $DOMAIN"
echo "   Email: $EMAIL"
echo ""

sudo certbot certonly --standalone \
    -d "$DOMAIN" \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --preferred-challenges http \
    --cert-path "$LETSENCRYPT_DIR/live/$DOMAIN/fullchain.pem" \
    --key-path "$LETSENCRYPT_DIR/live/$DOMAIN/privkey.pem"

# Create cert directory if it doesn't exist
mkdir -p "$CERT_DIR"

# Create symlinks
echo "🔗 Creating symlinks..."
ln -sf "../letsencrypt/live/$DOMAIN/fullchain.pem" "$CERT_DIR/fullchain.pem"
ln -sf "../letsencrypt/live/$DOMAIN/privkey.pem" "$CERT_DIR/privkey.pem"

# Generate DH parameters if they don't exist
if [ ! -f "$CERT_DIR/dhparam.pem" ]; then
    echo "🔐 Generating DH parameters (this may take a while)..."
    openssl dhparam -out "$CERT_DIR/dhparam.pem" 2048
fi

# Restart nginx
echo "🚀 Restarting nginx..."
docker-compose up -d nginx

# Verify certificate
echo ""
echo "✅ Let's Encrypt certificate installed!"
echo ""
echo "📜 Certificate Details:"
sudo certbot certificates -d "$DOMAIN"
echo ""
echo "📅 Auto-Renewal:"
echo "   Let's Encrypt certificates expire after 90 days."
echo "   Set up auto-renewal with:"
echo "   sudo cp infra/systemd/pdf2md-renew.* /etc/systemd/system/"
echo "   sudo systemctl enable pdf2md-renew.timer"
echo "   sudo systemctl start pdf2md-renew.timer"
echo ""
echo "🔄 Manual Renewal:"
echo "   sudo ./scripts/renew-certs.sh"
echo ""
echo "✅ Setup complete! Visit https://$DOMAIN"