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

  # Create logs directory with proper permissions
  mkdir -p /home/ubuntu/logs
  chmod 755 /home/ubuntu/logs

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

# Verify deployed version
echo -e "\n${YELLOW}🔍 Verifying deployment version...${NC}"
sleep 5  # Give the server a moment to fully start

# Get deployed version from API
DEPLOYED_VERSION=$(curl -s http://${EC2_HOST}/api/health | python3 -c "import sys, json; print(json.load(sys.stdin).get('version', 'unknown'))" 2>/dev/null || echo "failed")

# Get local version
LOCAL_VERSION=$(cd frontend && node -p "require('./package.json').version" 2>/dev/null || echo "unknown")

if [ "$DEPLOYED_VERSION" = "$LOCAL_VERSION" ]; then
    echo -e "${GREEN}✅ Version verified: $DEPLOYED_VERSION${NC}"
else
    echo -e "${YELLOW}⚠️  Version mismatch!${NC}"
    echo "   Deployed: $DEPLOYED_VERSION"
    echo "   Expected: $LOCAL_VERSION"
    echo "   Check logs: ssh -i ${KEY_PATH} ${EC2_USER}@${EC2_HOST} 'docker logs liap-tui-game | grep -i version'"
fi

echo -e "\n📊 Monitoring commands:"
echo "  ssh -i ${KEY_PATH} ${EC2_USER}@${EC2_HOST} 'docker logs liap-tui-game'"
echo "  ssh -i ${KEY_PATH} ${EC2_USER}@${EC2_HOST} 'docker-compose logs -f'"
