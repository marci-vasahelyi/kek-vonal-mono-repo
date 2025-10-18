#!/bin/bash

# ============================================
# Database Backup Script
# ============================================
# This script backs up the PostgreSQL database to local storage
# and uploads it to Google Cloud Storage
#

set -e  # Exit on error

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Variables
BACKUP_DIR="${BACKUP_DIR:-./backups}"
DB_NAME="${POSTGRES_DB}"
DB_USER="${POSTGRES_USER}"
DATE=$(date +"%Y%m%d%H%M")
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_backup_${DATE}.sql"
GCS_BUCKET="${GCS_BUCKET}"
LOG_FILE="${BACKUP_DIR}/backup.log"

# Start logging
{
echo "========== $(date) =========="
echo "Starting database backup process..."
echo "Variables:"
echo "  Backup Directory: ${BACKUP_DIR}"
echo "  Database Name: ${DB_NAME}"
echo "  Google Cloud Storage Bucket: ${GCS_BUCKET}"
echo "===================================="

# Ensure the backup directory exists
echo "Step 1: Ensuring backup directory exists..."
mkdir -p "${BACKUP_DIR}" || {
    echo "$(date) - ERROR: Failed to create backup directory";
    exit 1;
}
echo "$(date) - Backup directory exists: ${BACKUP_DIR}"

# Perform the backup
echo "Step 2: Performing database backup..."
docker exec -t database pg_dump -U ${DB_USER} -d ${DB_NAME} > "${BACKUP_FILE}" || {
    echo "$(date) - ERROR: Failed to perform database backup";
    exit 1;
}
echo "$(date) - Database backup created successfully: ${BACKUP_FILE}"

# Compress the backup
echo "Step 3: Compressing the backup file..."
gzip "${BACKUP_FILE}" || {
    echo "$(date) - ERROR: Failed to compress backup file";
    exit 1;
}
echo "$(date) - Backup file compressed: ${BACKUP_FILE}.gz"

# Transfer to Google Cloud Storage (if configured)
if [ ! -z "${GCS_BUCKET}" ] && [ "${GCS_BUCKET}" != "gs://kek-vonal-backup-bucket" ]; then
    echo "Step 4: Transferring the backup to Google Cloud Storage..."
    echo "$(date) - Running gsutil command..."
    TRANSFER_OUTPUT=$(gsutil cp "${BACKUP_FILE}.gz" "${GCS_BUCKET}" 2>&1)
    if [ $? -ne 0 ]; then
        echo "$(date) - ERROR: Failed to transfer backup to Google Cloud Storage"
        echo "Error Output from gsutil:"
        echo "${TRANSFER_OUTPUT}"
        exit 1
    else
        echo "$(date) - Backup transferred to Google Cloud Storage successfully."
        echo "gsutil Output:"
        echo "${TRANSFER_OUTPUT}"
    fi
else
    echo "Step 4: Skipping GCS upload (not configured or using default value)"
fi

# Remove old backups (older than BACKUP_RETENTION_DAYS days)
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
echo "Step 5: Removing backups older than ${RETENTION_DAYS} days..."
OLD_BACKUP_REMOVAL_OUTPUT=$(find "${BACKUP_DIR}" -type f -name "*.sql.gz" -mtime +${RETENTION_DAYS} -exec rm {} \; 2>&1)
if [ $? -ne 0 ]; then
    echo "$(date) - WARNING: Failed to remove old backups"
    echo "Error Output:"
    echo "${OLD_BACKUP_REMOVAL_OUTPUT}"
else
    echo "$(date) - Old backups removed successfully."
fi

# Process completed
echo "========== Backup process completed successfully at $(date). =========="
} >> "${LOG_FILE}" 2>&1

echo "Backup completed! Check ${LOG_FILE} for details."
