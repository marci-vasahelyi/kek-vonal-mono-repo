# Dashboard Deployment Guide

## Overview

This guide covers deploying the Streamlit dashboard to production with Nginx reverse proxy.

## Architecture

```
Internet → Nginx (443) → /dashboard/ → Streamlit (8501)
                      → /n8n/      → n8n (5678)
                      → /          → Directus (8055)
```

## What Was Changed

### 1. Docker Setup

**File**: `docker-compose.yml`
- Added `dashboard` service
- Builds from `apps/dashboard/Dockerfile`
- Exposes port 8501
- Connects to PostgreSQL via Docker network

**File**: `apps/dashboard/Dockerfile`
- Python 3.12 slim base image
- Installs dependencies from `requirements.txt`
- Runs Streamlit with `--server.baseUrlPath=/dashboard` for reverse proxy support

### 2. Nginx Configuration

**File**: `infrastructure/nginx/sites-available/jegyzokonyv.kek-vonal.cc`
- Added `/dashboard/` location block
- Configured WebSocket support (required for Streamlit)
- Similar config to `/n8n/` location

```nginx
location /dashboard/ {
    proxy_pass http://localhost:8501/;
    include proxy_params;
    
    # WebSocket headers (required for Streamlit)
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    
    # Additional headers
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # Disable buffering for real-time updates
    proxy_buffering off;
    
    # Timeout settings
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
}
```

### 3. Git Configuration

**File**: `.gitignore`
- Added `docker-compose.override.yml` (local development only)

**Action**: Removed `docker-compose.override.yml` from git tracking
- This file is for local development only
- Allows running n8n without `/n8n/` path locally
- Production uses main `docker-compose.yml` only

### 4. Deployment Script

**File**: `scripts/deployment/deploy-to-production.sh`

Automated deployment script that:
1. Backs up current Nginx config
2. Clones/updates monorepo on server
3. Copies `.env` file to production
4. Stops old services
5. Migrates PostgreSQL data from old repo
6. Updates Nginx configuration
7. Tests Nginx config (rolls back on failure)
8. Starts new services with dashboard
9. Verifies all services are healthy

## Manual Deployment Steps

If you prefer manual deployment:

### Step 1: SSH to Server

```bash
ssh -p ${SSH_PORT} ${SSH_USER}@${SSH_HOST}
```

### Step 2: Backup Nginx Config

```bash
sudo cp /etc/nginx/sites-available/jegyzokonyv.kek-vonal.cc \
       /etc/nginx/sites-available/jegyzokonyv.kek-vonal.cc.backup.$(date +%Y%m%d_%H%M%S)
```

### Step 3: Clone/Update Repo

```bash
cd /home
git clone git@github.com:marci-vasahelyi/kek-vonal-mono-repo.git kek-vonal-mono-repo
# OR if exists:
cd /home/kek-vonal-mono-repo
git pull origin main
```

### Step 4: Copy .env File

From local machine:
```bash
scp -P ${SSH_PORT} .env ${SSH_USER}@${SSH_HOST}:/home/kek-vonal-mono-repo/.env
```

### Step 5: Stop Old Services

```bash
cd /home/kek-vonal-crm-new
docker-compose down
```

### Step 6: Migrate PostgreSQL Data

```bash
sudo cp -r /home/kek-vonal-crm-new/data/database /home/kek-vonal-mono-repo/data/
sudo chown -R $(id -u):$(id -g) /home/kek-vonal-mono-repo/data/database
```

### Step 7: Update Nginx Config

```bash
sudo cp /home/kek-vonal-mono-repo/infrastructure/nginx/sites-available/jegyzokonyv.kek-vonal.cc \
        /etc/nginx/sites-available/jegyzokonyv.kek-vonal.cc

# Test config
sudo nginx -t

# If test passes, reload
sudo systemctl reload nginx
```

### Step 8: Start Services

```bash
cd /home/kek-vonal-mono-repo

# Build dashboard image
docker-compose build --no-cache dashboard

# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

### Step 9: Verify Deployment

```bash
# Check Directus
curl -f http://localhost:8055/_health

# Check n8n
curl -f http://localhost:5678/healthz

# Check Dashboard
curl -f http://localhost:8501/_stcore/health

# Check Nginx
sudo nginx -t
```

## Automated Deployment

Use the provided script:

```bash
cd /path/to/kek-vonal-mono-repo
./scripts/deployment/deploy-to-production.sh
```

The script requires `sshpass` to be installed:
```bash
# macOS
brew install hudochenkov/sshpass/sshpass

# Linux
sudo apt-get install sshpass
```

## Accessing the Dashboard

After deployment, the dashboard will be available at:

**Production**: https://jegyzokonyv.kek-vonal.cc/dashboard/

## Troubleshooting

### Dashboard Not Loading

1. Check if dashboard container is running:
   ```bash
   docker ps | grep dashboard
   ```

2. Check dashboard logs:
   ```bash
   docker logs dashboard
   ```

3. Verify Nginx config:
   ```bash
   sudo nginx -t
   curl -I http://localhost:8501/_stcore/health
   ```

### WebSocket Connection Issues

If dashboard loads but doesn't update:
- Check Nginx WebSocket headers are configured
- Verify `proxy_http_version 1.1` is set
- Check browser console for WebSocket errors

### Database Connection Issues

If dashboard shows "Loading data..." forever:
- Check `.env` has correct `DB_HOST=192.168.1.100`
- Verify database container is running
- Check dashboard can reach database:
  ```bash
  docker exec -it dashboard ping 192.168.1.100
  ```

## Rollback Procedure

If deployment fails:

1. **Stop new services:**
   ```bash
   cd /home/kek-vonal-mono-repo
   docker-compose down
   ```

2. **Restore Nginx config:**
   ```bash
   sudo cp /etc/nginx/sites-available/jegyzokonyv.kek-vonal.cc.backup.* \
           /etc/nginx/sites-available/jegyzokonyv.kek-vonal.cc
   sudo nginx -t
   sudo systemctl reload nginx
   ```

3. **Restart old services:**
   ```bash
   cd /home/kek-vonal-crm-new
   docker-compose up -d
   ```

## Post-Deployment

After successful deployment:

1. Test all services manually in browser
2. Monitor logs for errors
3. The old repo at `/home/kek-vonal-crm-new` can be archived (but don't delete immediately)
4. Update DNS/firewall if needed
5. Monitor service health for 24 hours

## Maintenance

- Dashboard runs in Docker, managed by `docker-compose`
- Restarts automatically on failure (`restart: always`)
- Logs available via `docker logs dashboard`
- Updates deployed via `git pull` + `docker-compose up -d --build dashboard`

