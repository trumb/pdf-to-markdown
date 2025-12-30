#!/bin/bash
set -e

LOG_FILE="/var/log/pdf2md-cert-renewal.log"

echo "[$(date)] 🔄 Renewing Let's Encrypt certificates..." | tee -a "$LOG_FILE"

# Renew certificates
if sudo certbot renew --quiet; then
    echo "[$(date)] ✅ Certificates renewed successfully" | tee -a "$LOG_FILE"
    
    # Restart nginx to load new certificates
    docker-compose restart nginx
    echo "[$(date)] 🔄 nginx restarted" | tee -a "$LOG_FILE"
else
    echo "[$(date)] ⚠️  Certificate renewal failed or not needed" | tee -a "$LOG_FILE"
fi

echo "[$(date)] ✅ Certificate renewal complete" | tee -a "$LOG_FILE"