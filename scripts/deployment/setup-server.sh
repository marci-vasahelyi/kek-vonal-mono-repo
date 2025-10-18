#!/bin/bash

# ============================================
# Server Setup Script
# ============================================
# This script sets up a fresh server with all required dependencies
# and deploys the application
#
# Usage: Run this on the target server
#

set -e  # Exit on error

echo "=========================================="
echo "KEK-VONAL Server Setup Script"
echo "=========================================="
echo ""

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
    echo "Please run with sudo"
    exit 1
fi

echo "Step 1: Updating system packages..."
apt-get update
apt-get upgrade -y

echo "Step 2: Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl enable docker
    systemctl start docker
else
    echo "Docker already installed"
fi

echo "Step 3: Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
else
    echo "Docker Compose already installed"
fi

echo "Step 4: Installing Nginx..."
if ! command -v nginx &> /dev/null; then
    apt-get install -y nginx
    systemctl enable nginx
else
    echo "Nginx already installed"
fi

echo "Step 5: Installing Certbot for SSL..."
if ! command -v certbot &> /dev/null; then
    apt-get install -y certbot python3-certbot-nginx
else
    echo "Certbot already installed"
fi

echo "Step 6: Creating project directory..."
PROJECT_DIR="/home/kek-vonal-crm"
mkdir -p ${PROJECT_DIR}

echo ""
echo "=========================================="
echo "Server setup completed!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Copy your monorepo to ${PROJECT_DIR}"
echo "2. Copy .env file with your configurations"
echo "3. Copy nginx configuration to /etc/nginx/sites-available/"
echo "4. Run: sudo ln -s /etc/nginx/sites-available/jegyzokonyv.kek-vonal.cc /etc/nginx/sites-enabled/"
echo "5. Request SSL certificate: sudo certbot --nginx -d jegyzokonyv.kek-vonal.cc"
echo "6. Navigate to project directory and run: docker-compose up -d"
echo ""

