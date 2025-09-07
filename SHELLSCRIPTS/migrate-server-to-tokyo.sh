#!/bin/bash
# Migrate server data from US to Tokyo

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🚀 Server Migration: US-East → Tokyo${NC}"

# Configuration
SOURCE_IP="34.233.7.20"
TARGET_IP="54.250.35.226"
SOURCE_KEY="~/.ssh/liap-tui-key-1755152170.pem"
TARGET_KEY="~/.ssh/liap-tui-tokyo-key.pem"

# Option 1: Quick Docker-based migration (Recommended)
echo -e "${GREEN}Option 1: Docker Migration (Faster)${NC}"
echo "This will export your Docker setup and data"
echo

read -p "Continue with Docker migration? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Create backup on source server
    echo -e "${YELLOW}📦 Creating backup on source server...${NC}"
    ssh -i "$SOURCE_KEY" ubuntu@$SOURCE_IP << 'ENDSSH'
        # Stop container to ensure data consistency
        docker-compose down

        # Create backup directory
        mkdir -p ~/backup

        # Export Docker images
        echo "Exporting Docker images..."
        docker save liap-tui:latest nginx:latest | gzip > ~/backup/docker-images.tar.gz

        # Backup data and configs
        echo "Backing up data..."
        sudo tar -czf ~/backup/app-data.tar.gz \
            ~/liap-tui-data \
            ~/logs \
            ~/nginx-config \
            ~/docker-compose.yml \
            /etc/nginx/sites-available/castellan \
            /etc/letsencrypt 2>/dev/null || true

        # Get docker-compose file
        cp ~/docker-compose.yml ~/backup/

        # Restart container
        docker-compose up -d

        echo "Backup complete!"
        ls -lh ~/backup/
ENDSSH

    # Download backups
    echo -e "${YELLOW}📥 Downloading backups...${NC}"
    mkdir -p ./tokyo-migration-backup
    scp -i "$SOURCE_KEY" ubuntu@$SOURCE_IP:~/backup/* ./tokyo-migration-backup/

    # Upload to Tokyo server
    echo -e "${YELLOW}📤 Uploading to Tokyo server...${NC}"
    scp -i "$TARGET_KEY" -o StrictHostKeyChecking=no ./tokyo-migration-backup/* ubuntu@$TARGET_IP:~/

    # Restore on Tokyo server
    echo -e "${YELLOW}🔄 Restoring on Tokyo server...${NC}"
    ssh -i "$TARGET_KEY" -o StrictHostKeyChecking=no ubuntu@$TARGET_IP << 'ENDSSH'
        # Install Docker if not present
        if ! command -v docker &> /dev/null; then
            echo "Installing Docker..."
            sudo apt-get update
            sudo apt-get install -y docker.io docker-compose
            sudo usermod -aG docker ubuntu
            newgrp docker
        fi

        # Load Docker images
        echo "Loading Docker images..."
        docker load < ~/docker-images.tar.gz

        # Extract app data
        echo "Extracting app data..."
        sudo tar -xzf ~/app-data.tar.gz -C /

        # Fix permissions
        sudo chown -R ubuntu:ubuntu ~/liap-tui-data ~/logs ~/nginx-config

        # Install nginx if needed
        if ! command -v nginx &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y nginx
        fi

        # Start containers
        echo "Starting containers..."
        docker-compose up -d

        # Check status
        docker ps
        echo "Migration complete!"
ENDSSH

    echo -e "${GREEN}✅ Migration complete!${NC}"
    echo -e "${GREEN}🌐 Test your game at: http://$TARGET_IP${NC}"
    echo
    echo -e "${YELLOW}⚠️  Important Notes:${NC}"
    echo "1. The Tokyo server has all your data and Docker setup"
    echo "2. SSL certificates were NOT copied (domain-specific)"
    echo "3. After DNS update, you'll need to get new SSL certs"
    echo
    echo -e "${YELLOW}📋 Next steps:${NC}"
    echo "1. Test the game at http://$TARGET_IP"
    echo "2. Update DNS to point castellan.andynenth.dev to $TARGET_IP"
    echo "3. After DNS propagation, get SSL cert:"
    echo "   ssh -i $TARGET_KEY ubuntu@$TARGET_IP"
    echo "   sudo certbot certonly --standalone -d castellan.andynenth.dev"
fi

# Cleanup
echo -e "${YELLOW}🧹 Cleaning up local files...${NC}"
rm -rf ./tokyo-migration-backup

echo -e "${GREEN}🎉 Done!${NC}"