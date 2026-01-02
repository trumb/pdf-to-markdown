#!/bin/sh
set -e

echo "🔧 Fixing permissions for pdf2md user..."

# Ensure data directory exists with correct ownership
if [ -d "/app/data" ]; then
    chown -R pdf2md:pdf2md /app/data
    echo "✓ Fixed /app/data permissions"
fi

# Ensure results directory exists with correct ownership
if [ -d "/var/lib/pdf2md/results" ]; then
    chown -R pdf2md:pdf2md /var/lib/pdf2md/results
    echo "✓ Fixed /var/lib/pdf2md/results permissions"
fi

# Ensure uploads directory exists
mkdir -p /app/data/uploads
chown -R pdf2md:pdf2md /app/data/uploads

echo "✅ Permission fixes complete"
echo "🚀 Starting PDF2MD API..."

# Switch to pdf2md user and run the application
exec su-exec pdf2md "$@"