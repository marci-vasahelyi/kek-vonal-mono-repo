# Disaster Recovery Guide

This guide covers complete recovery scenarios for the KEK-VONAL infrastructure.

## 🚨 Emergency Recovery Checklist

If your server is completely lost or corrupted, follow these steps to restore everything:

### Prerequisites

- [ ] This monorepo (backed up locally or in Git)
- [ ] Latest database backup (from Google Cloud Storage or local)
- [ ] Access to a new/fresh server
- [ ] Domain DNS pointed to new server IP

## 📋 Complete Server Recovery

### Step 1: Prepare New Server

1. **Provision a new Ubuntu server** (Ubuntu 20.04 or later recommended)

2. **Set up SSH access:**
   ```bash
   # On your local machine
   ssh-copy-id -p ${SSH_PORT} ${SSH_USER}@NEW_SERVER_IP
   ```

3. **Connect to the server:**
   ```bash
   ssh -p ${SSH_PORT} ${SSH_USER}@NEW_SERVER_IP
   ```

### Step 2: Run Server Setup Script

On the new server:

```bash
# Transfer the setup script
scp -P ${SSH_PORT} scripts/deployment/setup-server.sh ${SSH_USER}@NEW_SERVER_IP:/tmp/

# SSH into the server
ssh -p ${SSH_PORT} ${SSH_USER}@NEW_SERVER_IP

# Run the setup script
sudo bash /tmp/setup-server.sh
```

This installs:
- Docker & Docker Compose
- Nginx
- Certbot for SSL
- Creates project directories

### Step 3: Transfer the Monorepo

From your local machine:

```bash
# Create project directory on server
ssh -p ${SSH_PORT} ${SSH_USER}@NEW_SERVER_IP "sudo mkdir -p /home/kek-vonal-crm && sudo chown -R marci:marci /home/kek-vonal-crm"

# Transfer the entire monorepo (excluding large files)
rsync -avz --progress \
  --exclude 'node_modules' \
  --exclude 'data/' \
  --exclude 'backups/' \
  --exclude 'vm-backup/' \
  --exclude '.git' \
  -e "ssh -p ${SSH_PORT}" \
  ./ ${SSH_USER}@NEW_SERVER_IP:/home/kek-vonal-crm/
```

### Step 4: Configure Environment

On the server:

```bash
cd /home/kek-vonal-crm

# Verify .env file is present
cat .env

# If not present, copy from backup
# Edit if server IP or domain has changed
nano .env
```

### Step 5: Set Up Nginx

```bash
# Copy nginx configuration
sudo cp infrastructure/nginx/sites-available/jegyzokonyv.kek-vonal.cc /etc/nginx/sites-available/

# Enable the site
sudo ln -s /etc/nginx/sites-available/jegyzokonyv.kek-vonal.cc /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# If using new domain, update the config first:
sudo nano /etc/nginx/sites-available/jegyzokonyv.kek-vonal.cc
# Change server_name to your domain

# Reload nginx
sudo systemctl reload nginx
```

### Step 6: Request SSL Certificate

```bash
# Get SSL certificate from Let's Encrypt
sudo certbot --nginx -d jegyzokonyv.kek-vonal.cc

# Follow the prompts:
# - Enter email address
# - Agree to terms
# - Choose whether to redirect HTTP to HTTPS (recommended: yes)

# Verify SSL renewal cronjob
sudo systemctl status certbot.timer
```

### Step 7: Start Docker Containers

```bash
cd /home/kek-vonal-crm

# Create data directory for database
mkdir -p data/database

# Start containers (database will be empty)
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Step 8: Restore Database

#### Option A: From Google Cloud Storage

```bash
# List available backups
gsutil ls gs://kek-vonal-backup-bucket/

# Download the latest backup
gsutil cp gs://kek-vonal-backup-bucket/directus_backup_YYYYMMDD.sql.gz ./backups/

# Restore from backup
./scripts/restore/db-restore.sh backups/directus_backup_YYYYMMDD.sql.gz
```

#### Option B: From Local Backup

```bash
# Transfer backup from your local machine
scp -P ${SSH_PORT} path/to/local/backup.sql.gz ${SSH_USER}@NEW_SERVER_IP:/home/kek-vonal-crm/backups/

# Restore from backup
./scripts/restore/db-restore.sh backups/backup.sql.gz
```

### Step 9: Verify Everything Works

```bash
# Check all containers are running
docker-compose ps

# Test Directus
curl http://localhost:8055/server/health

# Test via public domain
curl https://jegyzokonyv.kek-vonal.cc

# Test n8n
curl https://jegyzokonyv.kek-vonal.cc/n8n/
```

### Step 10: Set Up Automated Backups

```bash
# Test backup script
./scripts/backup/db-backup.sh

# Set up cron job for daily backups at 3 AM
crontab -e

# Add this line:
0 3 * * * cd /home/kek-vonal-crm && ./scripts/backup/db-backup.sh
```

## 🔄 Partial Recovery Scenarios

### Scenario: Database Corruption

```bash
# Stop Directus
docker-compose stop directus

# Restore database
./scripts/restore/db-restore.sh backups/latest_backup.sql.gz

# Restart
docker-compose up -d
```

### Scenario: Container Issues

```bash
# Remove all containers and volumes
docker-compose down -v

# Recreate everything
docker-compose up -d

# Restore database if needed
./scripts/restore/db-restore.sh backups/latest_backup.sql.gz
```

### Scenario: Nginx Configuration Issues

```bash
# Restore nginx config from backup
sudo cp infrastructure/nginx/sites-available/jegyzokonyv.kek-vonal.cc /etc/nginx/sites-available/

# Test config
sudo nginx -t

# Reload
sudo systemctl reload nginx
```

### Scenario: Lost SSL Certificates

```bash
# Request new certificate
sudo certbot --nginx -d jegyzokonyv.kek-vonal.cc

# Or renew if cert exists
sudo certbot renew
```

### Scenario: Docker Images Missing

```bash
cd /home/kek-vonal-crm

# Pull all images
docker-compose pull

# Restart
docker-compose up -d
```

## 📦 What to Backup Regularly

### Critical (Automated)
- ✅ **Database** - Daily via backup script → Google Cloud Storage
- ✅ **Application code** - In this Git repository

### Important (Manual/Periodic)
- 🔶 **Uploaded files** - `apps/directus/uploads/` (if not in object storage)
- 🔶 **n8n workflows** - Stored in database (included in DB backup)
- 🔶 **Environment file** - `.env` (keep secure backup separately)
- 🔶 **SSL certificates** - Auto-renewed by Let's Encrypt (can be regenerated)

### Nice to Have
- 🔷 **Nginx logs** - `/var/log/nginx/` (not critical for recovery)
- 🔷 **Docker logs** - Can be regenerated

## 🧪 Test Your Recovery Plan

**Recommendation**: Test recovery every 3-6 months

1. Spin up a test server
2. Follow recovery procedures
3. Verify all services work
4. Document any issues
5. Update this guide

## 📞 Recovery Support

If you encounter issues during recovery:

1. Check logs: `docker-compose logs -f`
2. Verify .env configuration
3. Check nginx error logs: `sudo tail -f /var/log/nginx/error.log`
4. Verify DNS is pointing to new server
5. Check firewall rules (ports 80, 443, 8055, 5678)

## ⏱️ Recovery Time Objectives

- **RTO (Recovery Time Objective)**: ~2 hours
  - Server setup: 30 minutes
  - File transfer: 15 minutes  
  - Configuration: 15 minutes
  - Database restore: 30 minutes
  - Testing: 30 minutes

- **RPO (Recovery Point Objective)**: 24 hours
  - Daily automated backups
  - Can be improved to hourly if needed

## 🔐 Security Considerations

- Keep `.env` file encrypted and separate from code repository
- Store backup credentials securely
- Use SSH keys instead of passwords
- Regularly update SSL certificates (automated with certbot)
- Keep Docker images updated

---

**Last Updated**: October 2025
**Next Review**: January 2026

