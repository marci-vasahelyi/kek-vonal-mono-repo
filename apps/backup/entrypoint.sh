#!/bin/bash

# ============================================
# Backup Service Entrypoint
# ============================================
# Starts cron daemon and keeps container alive
#

set -e

echo "=========================================="
echo "🔧 Backup Service Starting"
echo "=========================================="
echo "Time: $(date)"
echo "Timezone: ${TZ}"
echo "Cron schedule: $(cat /etc/cron.d/backup-cron)"
echo "=========================================="

# Run backup immediately on startup for testing
echo "🧪 Running initial backup test..."
/app/backup.sh

# Start cron daemon
echo "⏰ Starting cron daemon..."
crond -f -l 2

