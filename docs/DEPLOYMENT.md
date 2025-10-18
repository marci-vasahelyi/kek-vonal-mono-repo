# Deployment Guide

Complete guide for deploying and managing the KEK-VONAL infrastructure.

## 🎯 Deployment Overview

This infrastructure uses Docker Compose for container orchestration and Nginx as a reverse proxy. All services are configured through a single `.env` file.

## 🖥️ Current Production Environment

- **Server**: 217.13.111.12
- **SSH Port**: 2222
- **User**: marci
- **Domain**: jegyzokonyv.kek-vonal.cc
- **Project Path**: `/home/kek-vonal-crm/`

## 🚀 Deployment Methods

### Method 1: Update Existing Deployment

For updating an already-running system:

```bash
# SSH into server
ssh -p 2222 marci@217.13.111.12

# Navigate to project
cd /home/kek-vonal-crm

# Pull latest changes (if using git)
git pull

# Or sync specific files
rsync -avz -e "ssh -p 2222" ./docker-compose.yml marci@217.13.111.12:/home/kek-vonal-crm/

# Run deployment script
./scripts/deployment/deploy.sh
```

### Method 2: Fresh Deployment

For deploying to a new server or complete reinstall:

See [DISASTER-RECOVERY.md](DISASTER-RECOVERY.md) for complete step-by-step instructions.

### Method 3: Manual Deployment

If you prefer manual control:

```bash
# Stop current containers
docker-compose down

# Pull latest images
docker-compose pull

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

## 📦 Service Configuration

### Directus CMS

**Port**: 8055  
**URL**: https://jegyzokonyv.kek-vonal.cc  
**Admin**: Set in `.env` as `ADMIN_EMAIL` and `ADMIN_PASSWORD`

**Key Files**:
- Extensions: `apps/directus/extensions/`
- Uploads: `apps/directus/uploads/`

**Configuration**: All in `.env` file
- Database connection
- Email settings (using Brevo/Sendinblue)
- Admin credentials
- API keys

### n8n Automation

**Port**: 5678  
**URL**: https://jegyzokonyv.kek-vonal.cc/n8n/  
**Auth**: Basic authentication (credentials in `.env`)

**Key Features**:
- Workflow automation
- Webhook endpoints
- Database integration

**Data**: Stored in Docker volume `n8n_data`

### PostgreSQL Database

**Port**: 5432 (internal only, not exposed publicly)  
**Image**: postgis/postgis:13-master (includes GIS extensions)  
**Network**: 192.168.1.100 (static IP in Docker network)

**Data Location**: `./data/database/`  
**Backups**: Automated daily via cron

### Redis Cache

**Port**: 6379 (localhost only)  
**Purpose**: Caching layer for Directus  
**Configuration**: Minimal, uses defaults

## 🔧 Configuration Management

### Environment Variables

All configuration is in `.env` file. Key sections:

1. **Server Configuration**
   ```env
   PUBLIC_DOMAIN=jegyzokonyv.kek-vonal.cc
   PUBLIC_URL=https://jegyzokonyv.kek-vonal.cc
   ```

2. **Database**
   ```env
   POSTGRES_USER=directus
   POSTGRES_PASSWORD=your_secure_password
   POSTGRES_DB=directus
   ```

3. **Directus**
   ```env
   DIRECTUS_KEY=generated_key
   DIRECTUS_SECRET=generated_secret
   ADMIN_EMAIL=your@email.com
   ADMIN_PASSWORD=secure_password
   ```

4. **Email (Brevo/Sendinblue)**
   ```env
   EMAIL_SMTP_HOST=smtp-relay.brevo.com
   EMAIL_SMTP_PORT=587
   EMAIL_SMTP_USER=your@email.com
   EMAIL_SMTP_PASSWORD=your_smtp_password
   ```

### Nginx Configuration

**File**: `infrastructure/nginx/sites-available/jegyzokonyv.kek-vonal.cc`

**Routing**:
- `/` → Directus (port 8055)
- `/n8n/` → n8n (port 5678)

**SSL**: Managed by Let's Encrypt (certbot)

**Key Features**:
- HTTP → HTTPS redirect
- WebSocket support for n8n
- Proxy headers for real IP forwarding

## 🔄 Update Procedures

### Updating Docker Images

```bash
cd /home/kek-vonal-crm

# Pull latest images
docker-compose pull

# Recreate containers with new images
docker-compose up -d

# Verify updates
docker-compose ps
docker images
```

### Updating Configuration

1. **Update .env file**:
   ```bash
   nano .env
   # Make changes
   ```

2. **Restart affected services**:
   ```bash
   # Restart specific service
   docker-compose restart directus
   
   # Or restart all
   docker-compose restart
   ```

### Updating Nginx

```bash
# Edit configuration
sudo nano /etc/nginx/sites-available/jegyzokonyv.kek-vonal.cc

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### Updating Directus Extensions

```bash
# Copy new extensions to apps/directus/extensions/
rsync -avz -e "ssh -p 2222" ./apps/directus/extensions/ marci@217.13.111.12:/home/kek-vonal-crm/apps/directus/extensions/

# Restart Directus
docker-compose restart directus
```

## 🔐 SSL Certificate Management

Certificates are auto-renewed by certbot.

### Manual Renewal

```bash
# Test renewal
sudo certbot renew --dry-run

# Force renewal
sudo certbot renew --force-renewal

# Check expiration
sudo certbot certificates
```

### Certificate Renewal Failures

If automatic renewal fails:

```bash
# Check certbot status
sudo systemctl status certbot.timer

# Check logs
sudo journalctl -u certbot

# Manually request new certificate
sudo certbot --nginx -d jegyzokonyv.kek-vonal.cc
```

## 📊 Monitoring and Health Checks

### Check Service Status

```bash
# Docker containers
docker-compose ps

# Container resource usage
docker stats

# Service health
curl http://localhost:8055/server/health
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f directus
docker-compose logs -f n8n
docker-compose logs -f database

# Last 100 lines
docker-compose logs --tail=100 directus

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Disk Usage

```bash
# Check disk space
df -h

# Docker disk usage
docker system df

# Clean up unused Docker resources
docker system prune -a
```

## 🔧 Common Deployment Tasks

### Restart All Services

```bash
cd /home/kek-vonal-crm
docker-compose restart
```

### Restart Single Service

```bash
docker-compose restart directus
```

### View Service Logs

```bash
docker-compose logs -f --tail=50 directus
```

### Execute Command in Container

```bash
# Database shell
docker exec -it database psql -U directus -d directus

# Directus shell
docker exec -it directus /bin/sh
```

### Backup Before Deployment

```bash
# Always backup before major changes
./scripts/backup/db-backup.sh

# Verify backup was created
ls -lh backups/
```

## 🚨 Rollback Procedures

If a deployment fails:

```bash
# Stop new containers
docker-compose down

# Restore from backup
./scripts/restore/db-restore.sh backups/directus_backup_BEFORE_UPDATE.sql.gz

# Revert docker-compose.yml if needed
git checkout HEAD~1 docker-compose.yml

# Start with previous config
docker-compose up -d
```

## 📋 Pre-Deployment Checklist

Before deploying updates:

- [ ] Backup current database
- [ ] Test changes in development/staging
- [ ] Verify .env configuration
- [ ] Check disk space
- [ ] Notify users of potential downtime
- [ ] Have rollback plan ready
- [ ] Document changes made

## 🎯 Post-Deployment Checklist

After deployment:

- [ ] Verify all containers running: `docker-compose ps`
- [ ] Check application responds: `curl https://jegyzokonyv.kek-vonal.cc`
- [ ] Test Directus admin panel
- [ ] Test n8n workflows
- [ ] Check logs for errors
- [ ] Verify email functionality
- [ ] Test database connectivity
- [ ] Update deployment log

## 🔍 Troubleshooting Deployments

### Container Won't Start

```bash
# Check logs
docker-compose logs <service_name>

# Check for port conflicts
sudo netstat -tlnp | grep :8055

# Verify .env file
cat .env | grep -v '^#'
```

### Database Connection Issues

```bash
# Check database is running
docker-compose ps database

# Check database logs
docker-compose logs database

# Test connection
docker exec database psql -U directus -d directus -c "SELECT version();"
```

### Permission Issues

```bash
# Fix file permissions
sudo chown -R marci:marci /home/kek-vonal-crm

# Fix directory permissions
chmod 755 scripts/backup/*.sh
chmod 755 scripts/restore/*.sh
chmod 755 scripts/deployment/*.sh
```

## 📞 Support

For deployment issues:
- Check logs: `docker-compose logs -f`
- Review [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Contact: marcigdd@gmail.com

---

**Last Updated**: October 2025

