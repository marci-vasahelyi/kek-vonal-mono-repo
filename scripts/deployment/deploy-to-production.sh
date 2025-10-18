#!/bin/bash

# ============================================================
# Production Deployment Script for Kék Vonal Monorepo
# ============================================================
# This script deploys the monorepo to production with:
# - Nginx config backup and update
# - PostgreSQL data migration from old repo
# - Service restart and verification
# ============================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo -e "${RED}Error: .env file not found${NC}"
    exit 1
fi

# Configuration
SSH_CONNECTION="${SSH_USER}@${SSH_HOST} -p ${SSH_PORT}"
OLD_REPO_PATH="/home/kek-vonal-crm-new"
NEW_REPO_PATH="/home/kek-vonal-mono-repo"
NGINX_CONFIG_PATH="/etc/nginx/sites-available/jegyzokonyv.kek-vonal.cc"
REPO_URL="git@github.com:marci-vasahelyi/kek-vonal-mono-repo.git"

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}  Kék Vonal - Production Deployment${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# Step 1: Backup current Nginx config
echo -e "${YELLOW}[1/8] Backing up current Nginx configuration...${NC}"
sshpass -p "${SSH_BACKUP_PASSWORD}" ssh ${SSH_CONNECTION} << 'EOF'
    sudo cp /etc/nginx/sites-available/jegyzokonyv.kek-vonal.cc /etc/nginx/sites-available/jegyzokonyv.kek-vonal.cc.backup.$(date +%Y%m%d_%H%M%S)
    echo "✓ Nginx config backed up"
EOF
echo -e "${GREEN}✓ Nginx backup complete${NC}"
echo ""

# Step 2: Clone new repo (if not exists)
echo -e "${YELLOW}[2/8] Cloning monorepo to production server...${NC}"
sshpass -p "${SSH_BACKUP_PASSWORD}" ssh ${SSH_CONNECTION} << EOF
    if [ -d "${NEW_REPO_PATH}" ]; then
        echo "Repository already exists at ${NEW_REPO_PATH}"
        cd ${NEW_REPO_PATH}
        git pull origin main
        echo "✓ Repository updated"
    else
        cd /home
        git clone ${REPO_URL} kek-vonal-mono-repo
        echo "✓ Repository cloned"
    fi
EOF
echo -e "${GREEN}✓ Repository ready${NC}"
echo ""

# Step 3: Copy .env file to server
echo -e "${YELLOW}[3/8] Copying .env file to production...${NC}"
sshpass -p "${SSH_BACKUP_PASSWORD}" scp -P ${SSH_PORT} .env ${SSH_CONNECTION}:${NEW_REPO_PATH}/.env
echo -e "${GREEN}✓ .env file copied${NC}"
echo ""

# Step 4: Stop old services
echo -e "${YELLOW}[4/8] Stopping old services...${NC}"
sshpass -p "${SSH_BACKUP_PASSWORD}" ssh ${SSH_CONNECTION} << EOF
    cd ${OLD_REPO_PATH}
    docker-compose down || echo "Old services already stopped"
    echo "✓ Old services stopped"
EOF
echo -e "${GREEN}✓ Old services stopped${NC}"
echo ""

# Step 5: Copy PostgreSQL data
echo -e "${YELLOW}[5/8] Migrating PostgreSQL data...${NC}"
sshpass -p "${SSH_BACKUP_PASSWORD}" ssh ${SSH_CONNECTION} << EOF
    # Create data directory in new repo if it doesn't exist
    mkdir -p ${NEW_REPO_PATH}/data
    
    # Copy PostgreSQL data from old repo
    if [ -d "${OLD_REPO_PATH}/data/database" ]; then
        echo "Copying PostgreSQL data..."
        sudo cp -r ${OLD_REPO_PATH}/data/database ${NEW_REPO_PATH}/data/
        sudo chown -R \$(id -u):\$(id -g) ${NEW_REPO_PATH}/data/database
        echo "✓ PostgreSQL data copied"
    else
        echo "Warning: No database data found in old repo"
    fi
EOF
echo -e "${GREEN}✓ Data migration complete${NC}"
echo ""

# Step 6: Update Nginx configuration
echo -e "${YELLOW}[6/8] Updating Nginx configuration...${NC}"
sshpass -p "${SSH_BACKUP_PASSWORD}" ssh ${SSH_CONNECTION} << EOF
    sudo cp ${NEW_REPO_PATH}/infrastructure/nginx/sites-available/jegyzokonyv.kek-vonal.cc ${NGINX_CONFIG_PATH}
    
    # Test Nginx configuration
    echo "Testing Nginx configuration..."
    sudo nginx -t
    
    if [ \$? -eq 0 ]; then
        echo "✓ Nginx configuration is valid"
        sudo systemctl reload nginx
        echo "✓ Nginx reloaded"
    else
        echo "✗ Nginx configuration test failed! Rolling back..."
        sudo cp ${NGINX_CONFIG_PATH}.backup.* ${NGINX_CONFIG_PATH}
        sudo systemctl reload nginx
        exit 1
    fi
EOF
echo -e "${GREEN}✓ Nginx configuration updated${NC}"
echo ""

# Step 7: Start new services
echo -e "${YELLOW}[7/8] Starting new services...${NC}"
sshpass -p "${SSH_BACKUP_PASSWORD}" ssh ${SSH_CONNECTION} << EOF
    cd ${NEW_REPO_PATH}
    
    # Build and start services
    docker-compose build --no-cache dashboard
    docker-compose up -d
    
    echo "Waiting for services to start..."
    sleep 10
    
    # Check service status
    echo ""
    echo "Service Status:"
    docker-compose ps
EOF
echo -e "${GREEN}✓ Services started${NC}"
echo ""

# Step 8: Verification
echo -e "${YELLOW}[8/8] Verifying deployment...${NC}"
sshpass -p "${SSH_BACKUP_PASSWORD}" ssh ${SSH_CONNECTION} << 'EOF'
    echo "Checking service health..."
    
    # Check Directus
    if curl -f http://localhost:8055/_health &>/dev/null; then
        echo "✓ Directus is healthy"
    else
        echo "✗ Directus health check failed"
    fi
    
    # Check n8n
    if curl -f http://localhost:5678/healthz &>/dev/null; then
        echo "✓ n8n is healthy"
    else
        echo "✗ n8n health check failed"
    fi
    
    # Check Dashboard
    if curl -f http://localhost:8501/_stcore/health &>/dev/null; then
        echo "✓ Dashboard is healthy"
    else
        echo "✗ Dashboard health check failed"
    fi
    
    # Check Nginx
    if sudo nginx -t &>/dev/null; then
        echo "✓ Nginx is healthy"
    else
        echo "✗ Nginx configuration has issues"
    fi
EOF

echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${GREEN}✓ Deployment complete!${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""
echo -e "Services should be accessible at:"
echo -e "  ${GREEN}Directus:${NC}  https://jegyzokonyv.kek-vonal.cc/"
echo -e "  ${GREEN}n8n:${NC}       https://jegyzokonyv.kek-vonal.cc/n8n/"
echo -e "  ${GREEN}Dashboard:${NC} https://jegyzokonyv.kek-vonal.cc/dashboard/"
echo ""
echo -e "${YELLOW}Important:${NC}"
echo -e "  1. Test all services manually"
echo -e "  2. If everything works, the Nginx config is already updated"
echo -e "  3. Old Nginx config backup: ${NGINX_CONFIG_PATH}.backup.*"
echo -e "  4. Old repo is still at: ${OLD_REPO_PATH}"
echo ""

