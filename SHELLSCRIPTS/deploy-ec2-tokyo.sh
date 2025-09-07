#!/bin/bash
# Tokyo EC2 deployment script for ap-northeast-1

set -e

# Configuration for Tokyo region
EC2_HOST="YOUR_TOKYO_EC2_IP"  # Replace after creating instance
EC2_USER="ubuntu"
KEY_PATH="./liap-tui-key-tokyo.pem"  # You'll download this when creating the instance

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🗾 Starting Tokyo EC2 deployment...${NC}"

# Check if IP is set
if [ "$EC2_HOST" = "YOUR_TOKYO_EC2_IP" ]; then
    echo -e "${RED}❌ Error: Please set EC2_HOST to your Tokyo instance IP${NC}"
    exit 1
fi

# Check if key file exists
if [ ! -f "$KEY_PATH" ]; then
    echo -e "${RED}❌ Error: Key file not found at $KEY_PATH${NC}"
    echo "Please ensure you have the Tokyo instance key file"
    exit 1
fi

# Build production image locally
echo -e "${GREEN}🏗️  Building production image...${NC}"
docker build -f Dockerfile.prod -t liap-tui:latest .

# Save image to tarball
echo -e "${GREEN}📦 Saving Docker image...${NC}"
docker save liap-tui:latest | gzip > liap-tui-latest.tar.gz

# Transfer files to Tokyo EC2
echo -e "${GREEN}📤 Transferring files to Tokyo EC2...${NC}"
echo "   Region: ap-northeast-1 (Tokyo)"
echo "   Host: ${EC2_HOST}"

scp -i ${KEY_PATH} -o StrictHostKeyChecking=no liap-tui-latest.tar.gz ${EC2_USER}@${EC2_HOST}:~/
scp -i ${KEY_PATH} -o StrictHostKeyChecking=no docker-compose.prod.yml ${EC2_USER}@${EC2_HOST}:~/docker-compose.yml

# Deploy on Tokyo EC2
echo -e "${GREEN}🔄 Deploying on Tokyo EC2...${NC}"
ssh -i ${KEY_PATH} -o StrictHostKeyChecking=no ${EC2_USER}@${EC2_HOST} << 'ENDSSH'
  # Load Docker image
  echo "Loading Docker image..."
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
  echo "Starting new container..."
  docker-compose up -d

  # Cleanup
  rm liap-tui-latest.tar.gz

  echo "✅ Deployment complete!"
ENDSSH

# Cleanup local file
rm liap-tui-latest.tar.gz

echo -e "${GREEN}✅ Tokyo EC2 deployment successful!${NC}"
echo -e "${GREEN}🌐 Application URL: http://${EC2_HOST}${NC}"
echo -e "${GREEN}🗾 Region: ap-northeast-1 (Tokyo)${NC}"

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

# Show latency benefits
echo -e "\n${GREEN}🌏 Latency Benefits of Tokyo Region:${NC}"
echo "   Vancouver → Tokyo: ~120ms (balanced)"
echo "   Thailand → Tokyo: ~120ms (balanced)"
echo "   Previous Canada → Thailand: ~250-300ms"

echo -e "\n📊 Monitoring commands:"
echo "  ssh -i ${KEY_PATH} ${EC2_USER}@${EC2_HOST} 'docker logs liap-tui-game'"
echo "  ssh -i ${KEY_PATH} ${EC2_USER}@${EC2_HOST} 'docker-compose logs -f'"
echo "  ssh -i ${KEY_PATH} ${EC2_USER}@${EC2_HOST} 'df -h'  # Check disk space"
