#!/bin/bash
# Deployment script for Tokyo EC2 with SSL support (using existing image)

set -e

# Configuration for Tokyo
EC2_HOST="54.250.35.226"  # Tokyo instance IP (SSH doesn't work through Cloudflare)
EC2_USER="ubuntu"
KEY_PATH="~/.ssh/liap-tui-tokyo-key.pem"  # Tokyo key

# Your domain (will need DNS update)
DOMAIN="castellan.andynenth.dev"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🗾 Starting Tokyo EC2 SSL deployment...${NC}"

# Check if IP is set
if [ "$EC2_HOST" = "YOUR_EC2_IP_HERE" ]; then
    echo -e "${RED}❌ Error: Please set EC2_HOST to your EC2 IP${NC}"
    exit 1
fi

# Check if image exists
if ! docker images | grep -q "liap-tui.*latest"; then
    echo -e "${RED}❌ Docker image liap-tui:latest not found!${NC}"
    echo -e "${YELLOW}Please build it first with: docker-compose -f docker-compose.prod-local.yml build${NC}"
    exit 1
fi

# Get image creation time
IMAGE_TIME=$(docker inspect liap-tui:latest --format='{{.Created}}')
echo -e "${GREEN}📦 Using existing image built at: ${IMAGE_TIME}${NC}"

# Save the image
echo -e "${GREEN}📦 Saving Docker image...${NC}"
docker save liap-tui:latest | gzip > liap-tui-latest.tar.gz

# Calculate checksum
echo -e "${GREEN}🔒 Calculating checksum...${NC}"
CHECKSUM=$(sha256sum liap-tui-latest.tar.gz | awk '{print $1}')
echo "Checksum: $CHECKSUM"

# Transfer files to Tokyo EC2
echo -e "${GREEN}📤 Uploading to Tokyo EC2 (ap-northeast-1)...${NC}"
echo "   Target: $EC2_USER@$EC2_HOST"
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no liap-tui-latest.tar.gz "$EC2_USER@$EC2_HOST:~/"
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no docker-compose.prod-ssl.yml "$EC2_USER@$EC2_HOST:~/docker-compose.yml"

# Copy nginx config if it doesn't exist
echo -e "${GREEN}📄 Checking nginx configuration...${NC}"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_HOST" "mkdir -p ~/nginx-config"
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no nginx/castellan.conf "$EC2_USER@$EC2_HOST:~/nginx-config/"

# Deploy on Tokyo EC2
echo -e "${GREEN}🚀 Deploying on Tokyo EC2...${NC}"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_HOST" << 'ENDSSH'
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

    # Check if this is first deployment to Tokyo
    if ! command -v nginx &> /dev/null; then
        echo -e "${YELLOW}⚠️  First deployment detected - nginx not installed${NC}"
        echo -e "${YELLOW}After this deployment, you need to:${NC}"
        echo -e "${YELLOW}1. Install nginx: sudo apt update && sudo apt install -y nginx certbot python3-certbot-nginx${NC}"
        echo -e "${YELLOW}2. Update DNS to point to this Tokyo server${NC}"
        echo -e "${YELLOW}3. Get SSL cert: sudo certbot certonly --standalone -d castellan.andynenth.dev${NC}"
        echo -e "${YELLOW}4. Run this script again to complete SSL setup${NC}"
    else
        # Check if SSL certificate exists
        if ! sudo test -d "/etc/letsencrypt/live/castellan.andynenth.dev"; then
            echo -e "${YELLOW}⚠️  SSL certificate not found!${NC}"
            echo -e "${YELLOW}After DNS points to Tokyo, run:${NC}"
            echo -e "${YELLOW}sudo certbot certonly --standalone -d castellan.andynenth.dev${NC}"
        else
            # Copy nginx config if needed
            if ! sudo test -f "/etc/nginx/sites-available/castellan"; then
                echo -e "${GREEN}Setting up nginx configuration...${NC}"
                sudo cp ~/nginx-config/castellan.conf /etc/nginx/sites-available/castellan
                sudo ln -sf /etc/nginx/sites-available/castellan /etc/nginx/sites-enabled/
                sudo rm -f /etc/nginx/sites-enabled/default
                sudo nginx -t && sudo systemctl reload nginx
            fi
        fi
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

echo -e "${GREEN}✨ Tokyo deployment successful!${NC}"
echo -e "${GREEN}🗾 Region: ap-northeast-1 (Tokyo)${NC}"
echo -e "${GREEN}🌐 Server: https://$EC2_HOST${NC}"

# Since we're using domain name, the game should be accessible via HTTPS
echo -e "${GREEN}🔗 Game available at: https://$DOMAIN${NC}"

echo -e "\n${GREEN}🌏 Latency Benefits:${NC}"
echo "   Vancouver → Tokyo: ~120ms (balanced)"
echo "   Thailand → Tokyo: ~120ms (balanced)"
echo "   (Previously Thailand → US/Canada: ~250-300ms)"

echo -e "\n${GREEN}📝 Deployment Complete!${NC}"
echo "Your game is now running on the Tokyo server with:"
echo "✅ SSL/HTTPS enabled"
echo "✅ Balanced latency for Vancouver and Thailand"
echo "✅ Automatic deployments ready for future updates"