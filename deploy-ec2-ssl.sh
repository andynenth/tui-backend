#!/bin/bash
# Deployment script for EC2 with SSL support

set -e

# Configuration
EC2_HOST="34.233.7.20"
EC2_USER="ubuntu"
KEY_PATH="./liap-tui-key-1755152170.pem"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🚀 Starting EC2 SSL deployment...${NC}"

# Build production image locally
echo -e "${GREEN}🏗️  Building production image...${NC}"
docker build -f Dockerfile.prod -t liap-tui:latest .

# Save the image
echo -e "${GREEN}📦 Saving Docker image...${NC}"
docker save liap-tui:latest | gzip > liap-tui-latest.tar.gz

# Calculate checksum
echo -e "${GREEN}🔒 Calculating checksum...${NC}"
CHECKSUM=$(sha256sum liap-tui-latest.tar.gz | awk '{print $1}')
echo "Checksum: $CHECKSUM"

# Transfer files to EC2
echo -e "${GREEN}📤 Uploading to EC2...${NC}"
scp -i "$KEY_PATH" liap-tui-latest.tar.gz "$EC2_USER@$EC2_HOST:~/"
scp -i "$KEY_PATH" docker-compose.prod-ssl.yml "$EC2_USER@$EC2_HOST:~/docker-compose.yml"

# Copy nginx config if it doesn't exist
echo -e "${GREEN}📄 Checking nginx configuration...${NC}"
ssh -i "$KEY_PATH" "$EC2_USER@$EC2_HOST" "mkdir -p ~/nginx-config"
scp -i "$KEY_PATH" nginx/castellan.conf "$EC2_USER@$EC2_HOST:~/nginx-config/"

# Deploy on EC2
echo -e "${GREEN}🚀 Deploying on EC2...${NC}"
ssh -i "$KEY_PATH" "$EC2_USER@$EC2_HOST" << 'ENDSSH'
    # Colors for remote
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    RED='\033[0;31m'
    NC='\033[0m'

    # Verify checksum
    echo -e "${YELLOW}Verifying checksum...${NC}"
    REMOTE_CHECKSUM=$(sha256sum liap-tui-latest.tar.gz | awk '{print $1}')
    echo "Remote checksum: $REMOTE_CHECKSUM"

    # Load the Docker image
    echo -e "${GREEN}Loading Docker image...${NC}"
    docker load < liap-tui-latest.tar.gz

    # Stop existing container
    echo -e "${YELLOW}Stopping existing container...${NC}"
    docker-compose down || true

    # Check if nginx is installed
    if ! command -v nginx &> /dev/null; then
        echo -e "${RED}Nginx not installed! Please run the SSL setup first.${NC}"
        echo -e "${YELLOW}Run: sudo apt install nginx certbot python3-certbot-nginx${NC}"
        exit 1
    fi

    # Check if SSL certificate exists
    if [ ! -d "/etc/letsencrypt/live/castellan.andynenth.dev" ]; then
        echo -e "${RED}SSL certificate not found!${NC}"
        echo -e "${YELLOW}Please run: sudo certbot certonly --standalone -d castellan.andynenth.dev${NC}"
        exit 1
    fi

    # Copy nginx config if needed
    if [ ! -f "/etc/nginx/sites-available/castellan" ]; then
        echo -e "${GREEN}Setting up nginx configuration...${NC}"
        sudo cp ~/nginx-config/castellan.conf /etc/nginx/sites-available/castellan
        sudo ln -sf /etc/nginx/sites-available/castellan /etc/nginx/sites-enabled/
        sudo rm -f /etc/nginx/sites-enabled/default
        sudo nginx -t && sudo systemctl reload nginx
    fi

    # Start new container on port 8080
    echo -e "${GREEN}Starting new container...${NC}"
    docker-compose up -d

    # Wait for health check
    echo -e "${YELLOW}Waiting for health check...${NC}"
    sleep 10

    # Check if container is healthy
    if docker ps --filter "name=liap-tui-game" --filter "health=healthy" | grep -q liap-tui-game; then
        echo -e "${GREEN}✅ Container is healthy!${NC}"
    else
        echo -e "${RED}❌ Container health check failed!${NC}"
        docker logs liap-tui-game --tail 50
        exit 1
    fi

    # Clean up
    echo -e "${GREEN}🧹 Cleaning up...${NC}"
    rm liap-tui-latest.tar.gz

    echo -e "${GREEN}✅ Deployment complete!${NC}"
ENDSSH

# Clean up local file
rm liap-tui-latest.tar.gz

echo -e "${GREEN}✨ Deployment successful!${NC}"
echo -e "${GREEN}🔗 Game available at: https://castellan.andynenth.dev${NC}"
echo -e "${YELLOW}📝 Note: If this is the first deployment, you need to:${NC}"
echo -e "${YELLOW}   1. Set up nginx and SSL certificate on the server${NC}"
echo -e "${YELLOW}   2. Open port 443 in EC2 security group${NC}"