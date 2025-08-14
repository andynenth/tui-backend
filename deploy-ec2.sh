#!/bin/bash
# Simplified deployment for EC2 + Docker Compose

set -e

# Configuration
EC2_HOST="34.233.7.20"
EC2_USER="ubuntu"
KEY_PATH="./liap-tui-key-1755152170.pem"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🚀 Starting EC2 deployment...${NC}"

# Build production image locally
echo -e "${GREEN}🏗️  Building production image...${NC}"
docker build -f Dockerfile.prod -t liap-tui:latest .

# Save image to tarball
echo -e "${GREEN}📦 Saving Docker image...${NC}"
docker save liap-tui:latest | gzip > liap-tui-latest.tar.gz

# Transfer files to EC2
echo -e "${GREEN}📤 Transferring files to EC2...${NC}"
scp -i ${KEY_PATH} liap-tui-latest.tar.gz ${EC2_USER}@${EC2_HOST}:~/
scp -i ${KEY_PATH} docker-compose.prod.yml ${EC2_USER}@${EC2_HOST}:~/docker-compose.yml

# Deploy on EC2
echo -e "${GREEN}🔄 Deploying on EC2...${NC}"
ssh -i ${KEY_PATH} ${EC2_USER}@${EC2_HOST} << 'ENDSSH'
  # Load Docker image
  docker load < liap-tui-latest.tar.gz
  
  # Create data directory if not exists
  mkdir -p /home/ubuntu/liap-tui-data
  
  # Stop and remove existing container
  docker-compose down || true
  docker stop liap-tui-game || true
  docker rm liap-tui-game || true
  
  # Start new container
  docker-compose up -d
  
  # Cleanup
  rm liap-tui-latest.tar.gz
  
  echo "✅ Deployment complete!"
ENDSSH

# Cleanup local file
rm liap-tui-latest.tar.gz

echo -e "${GREEN}✅ EC2 deployment successful!${NC}"
echo -e "${GREEN}🌐 Application URL: http://${EC2_HOST}${NC}"