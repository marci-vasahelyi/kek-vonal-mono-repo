#!/bin/bash

# ============================================
# Database Backup Script (Docker Service)
# ============================================
# Runs inside a Docker container with access to:
# - PostgreSQL database (via network)
# - Google Cloud SDK (for GCS uploads)
# - Shared backup volume
#

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Configuration from environment variables
DB_HOST="${DB_HOST:-database}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${POSTGRES_DB}"
DB_USER="${POSTGRES_USER}"
PGPASSWORD="${POSTGRES_PASSWORD}"
BACKUP_DIR="${BACKUP_DIR:-/backups}"
GCS_BUCKET="${GCS_BUCKET}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_backup_${DATE}.sql"
LOG_FILE="/var/log/backup.log"

# Export PGPASSWORD for pg_dump
export PGPASSWORD

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"
}

# Error handler
error_exit() {
    log "❌ ERROR: $1"
    log "========== BACKUP FAILED at $(date) =========="
    exit 1
}

# Main backup process
log "=========================================="
log "🚀 Starting database backup process"
log "=========================================="
log "Database: ${DB_NAME}@${DB_HOST}:${DB_PORT}"
log "Backup Directory: ${BACKUP_DIR}"
log "GCS Bucket: ${GCS_BUCKET}"
log "Retention: ${RETENTION_DAYS} days"

# Step 1: Ensure backup directory exists
log "📁 Step 1/5: Ensuring backup directory exists..."
mkdir -p "${BACKUP_DIR}" || error_exit "Failed to create backup directory"
log "✅ Backup directory ready: ${BACKUP_DIR}"

# Step 2: Test database connection
log "🔌 Step 2/5: Testing database connection..."
pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -t 10 || error_exit "Database not accessible"
log "✅ Database connection successful"

# Step 3: Perform the backup
log "💾 Step 3/5: Dumping database..."
pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
    --verbose \
    --no-owner \
    --no-acl \
    -f "${BACKUP_FILE}" 2>> "${LOG_FILE}" || error_exit "pg_dump failed"

# Verify backup file exists and has content
if [ ! -s "${BACKUP_FILE}" ]; then
    error_exit "Backup file is empty or does not exist"
fi

BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
log "✅ Database dumped successfully (${BACKUP_SIZE})"

# Step 4: Compress the backup
log "🗜️  Step 4/5: Compressing backup..."
gzip -f "${BACKUP_FILE}" || error_exit "Compression failed"
COMPRESSED_SIZE=$(du -h "${BACKUP_FILE}.gz" | cut -f1)
log "✅ Backup compressed (${COMPRESSED_SIZE})"

# Step 5: Upload to Google Cloud Storage
if [ -n "${GCS_BUCKET}" ]; then
    log "☁️  Step 5/5: Uploading to Google Cloud Storage..."
    
    # Check if gcloud is authenticated
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &>/dev/null; then
        log "⚠️  WARNING: No active gcloud authentication. Skipping GCS upload."
        log "   To enable: mount service account key and run 'gcloud auth activate-service-account'"
    else
        gsutil cp "${BACKUP_FILE}.gz" "${GCS_BUCKET}/" 2>&1 | tee -a "${LOG_FILE}" || {
            log "⚠️  WARNING: Failed to upload to GCS, but local backup succeeded"
            log "========== BACKUP COMPLETED (with GCS upload warning) at $(date) =========="
            exit 0  # Don't fail on GCS errors if local backup succeeded
        }
        log "✅ Backup uploaded to ${GCS_BUCKET}/"
    fi
else
    log "⏭️  Step 5/5: Skipping GCS upload (not configured)"
fi

# Step 6: Cleanup old backups
log "🧹 Cleaning up backups older than ${RETENTION_DAYS} days..."
OLD_BACKUPS=$(find "${BACKUP_DIR}" -type f -name "*.sql.gz" -mtime +${RETENTION_DAYS} | wc -l)
find "${BACKUP_DIR}" -type f -name "*.sql.gz" -mtime +${RETENTION_DAYS} -delete 2>&1 | tee -a "${LOG_FILE}"
log "✅ Removed ${OLD_BACKUPS} old backup(s)"

# Success!
log "=========================================="
log "✅ BACKUP COMPLETED SUCCESSFULLY"
log "=========================================="
log "Backup file: ${BACKUP_FILE}.gz (${COMPRESSED_SIZE})"
log "Local backups: $(ls -1 ${BACKUP_DIR}/*.sql.gz 2>/dev/null | wc -l) file(s)"
log "Next backup: Tomorrow at $(grep backup /etc/cron.d/backup-cron | awk '{print $2":"$1}')"
log "=========================================="

exit 0

