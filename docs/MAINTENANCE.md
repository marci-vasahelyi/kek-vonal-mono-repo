# Maintenance Checklist

Essential maintenance tasks for the KEK-VONAL infrastructure.

## Quick Access

**SSH to Production**:
```bash
# Get credentials from .env file
ssh -p ${SSH_PORT} ${SSH_USER}@${SSH_HOST}
# Password: ${SSH_BACKUP_PASSWORD}
```

**View all services**:
```bash
docker-compose ps
```

---

## Weekly Tasks (15 min)

### 1. Check Service Health
```bash
# SSH to production (credentials in .env)
ssh -p ${SSH_PORT} ${SSH_USER}@${SSH_HOST}

# Check all containers are running
docker-compose ps
# Expected: 4 services (database, cache, directus, n8n) - all "Up"

# Check for any container restarts (restart count should be 0)
docker ps --format "table {{.Names}}\t{{.Status}}"

# Quick smoke test
curl -I https://jegyzokonyv.kek-vonal.cc
curl -I https://jegyzokonyv.kek-vonal.cc/n8n/
```

### 2. Check Disk Space
```bash
# On production server
df -h
# Alert if any partition > 80% full

# Check Docker disk usage
docker system df
```

### 3. Verify Backups Are Running
```bash
# Check recent LOCAL backups
ls -lh ~/kek-vonal-crm-new/db_backup/ | tail -5

# Check backup log for errors
tail -30 ~/kek-vonal-crm-new/db-save/backup.log

# Verify backups in Google Cloud Storage
~/kek-vonal-crm-new/db-save/google-cloud-sdk/bin/gsutil ls -lh gs://kek-vonal-backup-bucket/ | tail -10
# Expected: Recent backups visible (within last 24 hours)

# Check GCS backup count
~/kek-vonal-crm-new/db-save/google-cloud-sdk/bin/gsutil ls gs://kek-vonal-backup-bucket/ | wc -l
# Keep eye on storage usage

# Expected: No errors in log, backups within last 24 hours in both local and GCS
```

### 4. Check Application Logs
```bash
# Check for errors in last 24 hours
docker-compose logs --tail=100 directus | grep -i "error\|warn"
docker-compose logs --tail=100 n8n | grep -i "error\|warn"
docker-compose logs --tail=100 database | grep -i "error\|fatal"
```

---

## Monthly Tasks (30-45 min)

### 1. Test Database Restore from Google Cloud Storage (Critical!)
```bash
# On local machine, test restore from GCS backup
# This is THE MOST IMPORTANT monthly task!

# List available backups in GCS
gsutil ls -lh gs://kek-vonal-backup-bucket/

# Download latest backup from GCS
gsutil cp gs://kek-vonal-backup-bucket/directus_backup_LATEST.sql.gz ./backups/
# Replace LATEST with actual latest timestamp

# Alternative: Download from production server
# scp -P ${SSH_PORT} ${SSH_USER}@${SSH_HOST}:~/kek-vonal-crm-new/db_backup/directus_backup_*.sql.gz ./backups/

# Test restore locally
docker-compose up -d database
./scripts/restore/db-restore.sh backups/directus_backup_YYYYMMDD.sql.gz

# Verify restore worked
docker exec -it database psql -U directus -d directus -c "\dt"
# Should see all tables

docker exec -it database psql -U directus -d directus -c "SELECT COUNT(*) FROM directus_users;"
# Should show expected user count

# Access Directus locally to verify data integrity
open http://localhost:8055
# Verify:
# - Can log in with admin credentials
# - Can see data in collections
# - Data looks recent and correct

# If restore test succeeds, backups are good!
# If it fails, investigate IMMEDIATELY - your backups may be corrupted
```

### 2. Update Docker Images
```bash
# SSH to production
ssh -p ${SSH_PORT} ${SSH_USER}@${SSH_HOST}
cd ~/kek-vonal-crm-new

# Check for available updates
docker-compose pull

# If updates available, apply during low-traffic time:
docker-compose up -d

# Monitor for issues
docker-compose logs -f --tail=50
```

### 3. Update System Packages
```bash
# SSH to production
ssh -p ${SSH_PORT} ${SSH_USER}@${SSH_HOST}

# Update package list
sudo apt update

# Check available updates
apt list --upgradable

# Apply security updates
sudo apt upgrade -y

# Check if reboot required
[ -f /var/run/reboot-required ] && echo "Reboot required" || echo "No reboot needed"

# If reboot required, schedule during maintenance window
```

### 4. SSL Certificate Check
```bash
# Check certificate expiry
echo | openssl s_client -servername jegyzokonyv.kek-vonal.cc -connect jegyzokonyv.kek-vonal.cc:443 2>/dev/null | openssl x509 -noout -dates

# Certbot should auto-renew, but verify
sudo certbot certificates

# Test renewal (dry-run)
sudo certbot renew --dry-run
```

### 5. Database Maintenance
```bash
# SSH to production
ssh -p ${SSH_PORT} ${SSH_USER}@${SSH_HOST}

# Check database size
docker exec database psql -U directus -d directus -c "\l+"

# Vacuum and analyze (during low-traffic time)
docker exec database psql -U directus -d directus -c "VACUUM ANALYZE;"

# Check for bloat in large tables
docker exec database psql -U directus -d directus -c "
SELECT 
    schemaname || '.' || tablename AS table,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC 
LIMIT 10;"
```

### 6. Verify n8n Workflows
```bash
# Access n8n UI
open https://jegyzokonyv.kek-vonal.cc/n8n/

# Check workflow execution history
# - Go to Executions
# - Verify scheduled workflow ran in last hour
# - Check for any failed executions

# Verify Google Sheets exports
# - Open target spreadsheet: 1DNKX2j07xZLm_7VdaNCdKT4TnxCI-JlEwA5FzNgxSVQ
# - Verify recent data was added
```

### 7. Clean Up Old Backups and Files
```bash
# SSH to production
ssh -p ${SSH_PORT} ${SSH_USER}@${SSH_HOST}

# 1. Check LOCAL backups (older than 7 days are auto-cleaned by script)
cd ~/kek-vonal-crm-new
ls -lh db_backup/
du -sh db_backup/
# Verify only last 7 days of backups present

# 2. Check GOOGLE CLOUD STORAGE backups
~/kek-vonal-crm-new/db-save/google-cloud-sdk/bin/gsutil ls -lh gs://kek-vonal-backup-bucket/

# Count total backups in GCS
~/kek-vonal-crm-new/db-save/google-cloud-sdk/bin/gsutil ls gs://kek-vonal-backup-bucket/ | wc -l

# Check total GCS storage usage
~/kek-vonal-crm-new/db-save/google-cloud-sdk/bin/gsutil du -sh gs://kek-vonal-backup-bucket/

# 3. Remove backups older than 90 days from GCS
# List backups to delete first (dry run)
~/kek-vonal-crm-new/db-save/google-cloud-sdk/bin/gsutil ls gs://kek-vonal-backup-bucket/ | grep "202[0-9]" | head -20

# Delete old backups (adjust date pattern as needed)
# Example: Remove backups from before 90 days ago
# BACKUP_DATE_THRESHOLD=$(date -d '90 days ago' +%Y%m%d)
# gsutil rm gs://kek-vonal-backup-bucket/directus_backup_${BACKUP_DATE_THRESHOLD}*.sql.gz

# OR use lifecycle policy (recommended - set up once)
# See: https://cloud.google.com/storage/docs/lifecycle

# 4. Clean up Docker system
docker system prune -f
docker volume prune -f

# 5. Check for old log files
du -sh /var/log/
sudo journalctl --disk-usage
# If logs > 1GB, clean with: sudo journalctl --vacuum-time=30d

# 6. Clean temporary files
du -sh /tmp/
# Manually remove old temp files if needed
```

---

## Quarterly Tasks (1-2 hours)

### 1. Full Disaster Recovery Test
```bash
# Simulate complete disaster recovery on a fresh local environment
# 1. Start with empty data directory
# 2. Restore from GCS backup
# 3. Restore n8n workflows
# 4. Verify all functionality
# Document any issues found
```

### 2. Security Audit
```bash
# Check for exposed ports
sudo netmap -sT -O localhost

# Review nginx logs for suspicious activity
sudo tail -500 /var/log/nginx/access.log | grep -v "200\|304"

# Check Docker security
docker scan directus/directus:latest
```

### 3. Review and Update Documentation
- Update README.md with any infrastructure changes
- Review and update .env.example
- Document any new maintenance procedures
- Update disaster recovery documentation

---

## Annual Tasks

### 1. Credential Rotation
- Rotate database passwords
- Regenerate Directus KEY and SECRET
- Update n8n basic auth password
- Rotate email SMTP credentials
- Update all .env files

### 2. Infrastructure Review
- Review resource usage trends
- Consider scaling if needed
- Review backup retention policy
- Review monitoring and alerting setup

---

## Emergency Procedures

### Service Down
```bash
# Quick restart
ssh -p ${SSH_PORT} ${SSH_USER}@${SSH_HOST}
cd ~/kek-vonal-crm-new
docker-compose restart

# If that fails, full restart
docker-compose down
docker-compose up -d
```

### Database Corruption
```bash
# 1. Download latest backup from Google Cloud Storage
gsutil cp gs://kek-vonal-backup-bucket/directus_backup_LATEST.sql.gz ./backups/
# Replace LATEST with most recent timestamp

# 2. Restore from backup
./scripts/restore/db-restore.sh backups/directus_backup_YYYYMMDD.sql.gz

# 3. Verify restoration
docker exec -it database psql -U directus -d directus -c "\dt"
open http://localhost:8055

# If GCS backup unavailable, try local backup from production:
# scp -P ${SSH_PORT} ${SSH_USER}@${SSH_HOST}:~/kek-vonal-crm-new/db_backup/directus_backup_*.sql.gz ./backups/
```

### Disk Full
```bash
# Quick cleanup
docker system prune -a --volumes -f

# Remove old logs
sudo journalctl --vacuum-time=7d

# Check and remove old backups
rm ~/kek-vonal-crm-new/db_backup/directus_backup_*.sql.gz
# (Keep at least last 3)
```

---

## Monitoring Checklist

Copy this checklist for monthly reviews:

### Infrastructure Health
- [ ] All 4 containers running (database, cache, directus, n8n)
- [ ] No recent container restarts
- [ ] Disk usage < 80% on all partitions
- [ ] Docker disk usage reasonable
- [ ] No errors in application logs
- [ ] SSL certificate valid > 30 days

### Backups (Most Critical!)
- [ ] Local backups running daily (check logs)
- [ ] Latest local backup < 24 hours old
- [ ] Backups visible in Google Cloud Storage
- [ ] Latest GCS backup < 24 hours old
- [ ] Backup restore test from GCS PASSED
- [ ] GCS storage usage reasonable (< XX GB)
- [ ] Old backups cleaned up (local: 7 days, GCS: 90 days)

### Updates & Maintenance
- [ ] Docker images up to date
- [ ] System packages up to date
- [ ] Database vacuumed
- [ ] n8n workflows executing successfully
- [ ] Google Sheets receiving data
- [ ] Old logs cleaned up
- [ ] Temporary files cleaned up

### Documentation & Security
- [ ] Documentation is current
- [ ] All credentials secure (not in git)
- [ ] No suspicious access in logs

