#!/bin/bash
set -e

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

echo "📦 Creating backup: $TIMESTAMP"
echo ""

# Backup database
if [ -f "./data/pdf2md.db" ]; then
    echo "  → Backing up database..."
    cp ./data/pdf2md.db "$BACKUP_DIR/pdf2md-$TIMESTAMP.db"
    echo "     ✓ Database backed up"
else
    echo "  ⚠️  Database not found, skipping"
fi

# Backup certificates
if [ -d "./certs" ]; then
    echo "  → Backing up certificates..."
    tar -czf "$BACKUP_DIR/certs-$TIMESTAMP.tar.gz" ./certs 2>/dev/null || true
    echo "     ✓ Certificates backed up"
fi

# Backup environment files
if [ -f ".env" ]; then
    echo "  → Backing up environment..."
    cp .env "$BACKUP_DIR/env-$TIMESTAMP"
    echo "     ✓ Environment backed up"
fi

# Keep only last 7 days of backups
echo "  → Cleaning old backups (keeping last 7 days)..."
find "$BACKUP_DIR" -type f -mtime +7 -delete

# Show backup size
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)

echo ""
echo "✅ Backup complete!"
echo ""
echo "📊 Backup Summary:"
echo "   - Timestamp: $TIMESTAMP"
echo "   - Location: $BACKUP_DIR"
echo "   - Total size: $BACKUP_SIZE"
echo ""
echo "📁 Backup files:"
ls -lh "$BACKUP_DIR" | tail -n 5