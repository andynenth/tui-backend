#!/bin/bash
# update-version-local.sh - Update version and test locally

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get version type from argument (default: patch)
VERSION_TYPE=${1:-patch}

echo -e "${GREEN}📦 Updating version (${VERSION_TYPE})...${NC}"
cd frontend
npm version $VERSION_TYPE
VERSION=$(node -p "require('./package.json').version")
cd ..

echo -e "${GREEN}✅ Updated to version ${VERSION}${NC}"

echo -e "${YELLOW}🏗️  Building Docker image with version ${VERSION}...${NC}"
docker-compose -f docker-compose.prod-local.yml build --build-arg FRONTEND_VERSION=$VERSION

echo -e "${GREEN}🚀 Starting container...${NC}"
docker-compose -f docker-compose.prod-local.yml up -d

echo -e "${GREEN}⏳ Waiting for container to be healthy...${NC}"
sleep 10

echo -e "${GREEN}🔍 Checking versions...${NC}"
API_VERSION=$(curl -s http://localhost/api/health | python3 -c "import sys, json; print(json.load(sys.stdin)['version'])" 2>/dev/null || echo "Failed to get API version")
echo -e "  API Version: ${API_VERSION}"
echo -e "  Frontend Version: Check http://localhost (should show v${VERSION})"

echo -e "${GREEN}✨ Done! Both should show version ${VERSION}${NC}"