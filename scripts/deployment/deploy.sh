#!/bin/bash

# ============================================
# Deployment Script
# ============================================
# This script deploys or updates the application
#

set -e  # Exit on error

echo "=========================================="
echo "KEK-VONAL Deployment Script"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please create .env file from .env.example"
    exit 1
fi

echo "Step 1: Pulling latest Docker images..."
docker-compose pull

echo "Step 2: Stopping containers..."
docker-compose down

echo "Step 3: Starting containers..."
docker-compose up -d

echo "Step 4: Waiting for services to start..."
sleep 10

echo "Step 5: Checking container status..."
docker-compose ps

echo ""
echo "=========================================="
echo "Deployment completed!"
echo "=========================================="
echo ""
echo "Services:"
echo "  - Directus: http://localhost:8055"
echo "  - n8n: http://localhost:5678"
echo "  - Database: localhost:5432"
echo "  - Redis: localhost:6379"
echo ""
echo "Check logs with: docker-compose logs -f"

