#!/bin/bash

# ============================================
# Database Restore Script
# ============================================
# This script restores the PostgreSQL database from a backup file
#
# Usage: ./db-restore.sh <backup_file.sql>
#

set -e  # Exit on error

# Check if backup file is provided
if [ -z "$1" ]; then
    echo "Error: No backup file specified"
    echo "Usage: $0 <backup_file.sql>"
    echo ""
    echo "Available backups:"
    ls -lh backups/*.sql* 2>/dev/null || echo "No backups found in ./backups/"
    exit 1
fi

BACKUP_FILE="$1"

# Check if file exists
if [ ! -f "${BACKUP_FILE}" ]; then
    echo "Error: Backup file '${BACKUP_FILE}' not found"
    exit 1
fi

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

DB_NAME="${POSTGRES_DB}"
DB_USER="${POSTGRES_USER}"

# If file is gzipped, decompress it
if [[ "${BACKUP_FILE}" == *.gz ]]; then
    echo "Decompressing backup file..."
    gunzip -k "${BACKUP_FILE}"
    BACKUP_FILE="${BACKUP_FILE%.gz}"
fi

echo "=========================================="
echo "Database Restore Process"
echo "=========================================="
echo "Backup file: ${BACKUP_FILE}"
echo "Database: ${DB_NAME}"
echo "User: ${DB_USER}"
echo ""

read -p "This will DROP and recreate the database. Are you sure? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

echo ""
echo "Step 1: Stopping Directus and Cache containers..."
docker stop directus cache || true

echo "Step 2: Dropping existing database..."
docker exec -it database psql -U ${DB_USER} -d postgres -c "DROP DATABASE IF EXISTS ${DB_NAME};"

echo "Step 3: Creating fresh database..."
docker exec -it database psql -U ${DB_USER} -d postgres -c "CREATE DATABASE ${DB_NAME};"

echo "Step 4: Copying backup file to container..."
docker cp "${BACKUP_FILE}" database:/tmp/restore.sql

echo "Step 5: Restoring database..."
docker exec -i database psql -U ${DB_USER} -d ${DB_NAME} -f /tmp/restore.sql

echo "Step 6: Cleaning up..."
docker exec database rm /tmp/restore.sql

echo "Step 7: Restarting all containers..."
docker-compose up -d

echo ""
echo "=========================================="
echo "Database restore completed successfully!"
echo "=========================================="
echo ""
echo "Containers are starting up. Check status with: docker-compose ps"

