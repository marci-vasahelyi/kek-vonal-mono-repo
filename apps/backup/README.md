# Database Backup Service

Automated PostgreSQL backup service running as a Docker container with cron scheduling.

## Features

- ✅ **Automated daily backups** - Runs at 3 AM every day
- ✅ **Immediate startup backup** - Tests backup on container start
- ✅ **Google Cloud Storage** - Optional automated uploads to GCS
- ✅ **Visible failures** - Clear error messages in logs and exit codes
- ✅ **Automatic cleanup** - Removes backups older than retention period
- ✅ **Database health checks** - Verifies connection before backup
- ✅ **Detailed logging** - All operations logged to `/var/log/backup.log`

## How It Works

1. **Container starts** → Runs immediate test backup
2. **Cron daemon starts** → Schedules daily backup at 3 AM
3. **Each backup**:
   - Connects to PostgreSQL database
   - Dumps database to SQL file
   - Compresses with gzip
   - (Optional) Uploads to Google Cloud Storage
   - Cleans up old backups

## Configuration

All configuration is done via environment variables in `.env`:

```bash
# Required
POSTGRES_DB=directus
POSTGRES_USER=directus
POSTGRES_PASSWORD=your_password
DB_HOST=192.168.1.100
DB_PORT=5432

# Optional
GCS_BUCKET=gs://kek-vonal-backup-bucket  # For GCS uploads
BACKUP_RETENTION_DAYS=7                   # Local backup retention
```

## Usage

### Start the backup service

```bash
docker-compose up -d backup
```

### View backup logs

```bash
# Live logs
docker-compose logs -f backup

# Last 50 lines
docker-compose logs --tail=50 backup

# Inside container
docker exec backup tail -f /var/log/backup.log
```

### Manually trigger a backup

```bash
docker exec backup /app/backup.sh
```

### Check backup files

```bash
# List local backups
ls -lh backups/

# Check backup count
docker exec backup ls -1 /backups/*.sql.gz | wc -l
```

### Stop the backup service

```bash
docker-compose stop backup
```

## Google Cloud Storage Setup (Optional)

To enable automatic uploads to GCS:

### Option 1: Service Account Key (Recommended for Production)

1. **Create a service account** in Google Cloud Console
2. **Download the JSON key file**
3. **Mount the key in docker-compose.yml**:

```yaml
backup:
  volumes:
    - ./backups:/backups
    - /path/to/your-service-account-key.json:/gcloud-key.json:ro
  environment:
    - GOOGLE_APPLICATION_CREDENTIALS=/gcloud-key.json
```

4. **Activate the service account** (one-time):

```bash
docker exec backup gcloud auth activate-service-account \
  --key-file=/gcloud-key.json
```

### Option 2: Application Default Credentials (Development)

If running on a GCP VM with proper IAM roles:

```bash
# The backup service will automatically use the VM's service account
# No additional configuration needed
```

## Monitoring

### Check if backups are running

```bash
# Check container status
docker-compose ps backup

# Check last backup time
docker exec backup ls -lt /backups | head -5

# Check for errors
docker exec backup grep ERROR /var/log/backup.log | tail -10
```

### Verify backup integrity

```bash
# Test restore locally
./scripts/restore/db-restore.sh backups/directus_backup_YYYYMMDD_HHMMSS.sql.gz
```

## Troubleshooting

### Container keeps restarting

```bash
# Check logs
docker-compose logs backup

# Common issues:
# - Database not accessible (wrong DB_HOST)
# - Missing environment variables
# - Permission issues with /backups volume
```

### Backups not running

```bash
# Verify cron is active
docker exec backup ps aux | grep crond

# Check crontab
docker exec backup cat /etc/cron.d/backup-cron

# Manually test backup
docker exec backup /app/backup.sh
```

### GCS uploads failing

```bash
# Check authentication
docker exec backup gcloud auth list

# Test GCS access
docker exec backup gsutil ls ${GCS_BUCKET}

# Re-authenticate if needed
docker exec backup gcloud auth activate-service-account \
  --key-file=/gcloud-key.json
```

## Schedule

Default schedule (configurable in `apps/backup/crontab`):

```
0 3 * * *  # Daily at 3:00 AM
```

To change schedule:
1. Edit `apps/backup/crontab`
2. Rebuild: `docker-compose build backup`
3. Restart: `docker-compose restart backup`

## File Structure

```
apps/backup/
├── Dockerfile          # Container definition
├── backup.sh           # Main backup script
├── entrypoint.sh       # Container startup script
├── crontab             # Cron schedule
└── README.md           # This file
```

## Error Handling

The backup service uses strict error handling:

- **Exit code 0** - Success
- **Exit code 1** - Failure (container will log error and continue)
- All errors are logged to `/var/log/backup.log`
- Failed backups don't overwrite previous successful backups

## Best Practices

1. **Test restores regularly** - Backups are useless if they can't be restored
2. **Monitor backup logs** - Check weekly for any warnings
3. **Verify GCS uploads** - Ensure backups reach cloud storage
4. **Keep 3-2-1 rule** - 3 copies, 2 different media, 1 offsite (GCS)
5. **Test disaster recovery** - Practice full restore at least quarterly

## Integration with CI/CD

The backup service starts automatically with `docker-compose up -d` and requires no manual intervention. It's designed to be part of your infrastructure stack.

## Security

- Database credentials are passed via environment variables (never hardcoded)
- GCS credentials are mounted as read-only files
- Backup files contain sensitive data - secure the `backups/` directory
- Use proper file permissions: `chmod 700 backups/`

## Support

For issues or questions about the backup service, check:
- Container logs: `docker-compose logs backup`
- Backup log: `docker exec backup cat /var/log/backup.log`
- Test manually: `docker exec backup /app/backup.sh`

