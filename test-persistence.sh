#!/bin/bash
# Test script to verify database persistence with Docker volumes

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🧪 Testing Database Persistence...${NC}"

# Clean up any existing test containers
echo -e "${YELLOW}🧹 Cleaning up existing test containers...${NC}"
docker-compose -f docker-compose.test.yml down -v 2>/dev/null || true
rm -rf test-data 2>/dev/null || true

# Start the container
echo -e "${GREEN}🚀 Starting test container...${NC}"
docker-compose -f docker-compose.test.yml up -d

# Wait for container to be healthy
echo -e "${YELLOW}⏳ Waiting for container to be healthy...${NC}"
for i in {1..30}; do
    if curl -f http://localhost:5051/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Container is healthy!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ Container failed to become healthy${NC}"
        docker-compose -f docker-compose.test.yml logs
        exit 1
    fi
    sleep 2
done

# Check if database file was created
echo -e "${YELLOW}🔍 Checking database file...${NC}"
if [ -f "test-data/game_events.db" ]; then
    echo -e "${GREEN}✅ Database file created successfully${NC}"
    ls -la test-data/
else
    echo -e "${RED}❌ Database file not found${NC}"
    exit 1
fi

# Create a test room using curl
echo -e "${YELLOW}🎮 Creating test room...${NC}"
ROOM_ID="TEST$(date +%s)"
# Note: Game operations use WebSocket, so we can't create a room via REST
# But we can verify the database is accessible

# Stop the container
echo -e "${YELLOW}🛑 Stopping container...${NC}"
docker-compose -f docker-compose.test.yml down

# Check if database file still exists
echo -e "${YELLOW}🔍 Checking database persistence...${NC}"
if [ -f "test-data/game_events.db" ]; then
    echo -e "${GREEN}✅ Database file persisted after container stop${NC}"
    FILESIZE=$(stat -f%z "test-data/game_events.db" 2>/dev/null || stat -c%s "test-data/game_events.db" 2>/dev/null || echo "0")
    echo -e "${GREEN}📊 Database size: ${FILESIZE} bytes${NC}"
else
    echo -e "${RED}❌ Database file lost after container stop${NC}"
    exit 1
fi

# Restart container
echo -e "${YELLOW}🔄 Restarting container...${NC}"
docker-compose -f docker-compose.test.yml up -d

# Wait for container to be healthy again
echo -e "${YELLOW}⏳ Waiting for container to be healthy...${NC}"
for i in {1..30}; do
    if curl -f http://localhost:5051/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Container is healthy again!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ Container failed to become healthy${NC}"
        exit 1
    fi
    sleep 2
done

# Final check
echo -e "${YELLOW}🔍 Final database check...${NC}"
if [ -f "test-data/game_events.db" ]; then
    echo -e "${GREEN}✅ Database file still exists after restart${NC}"
    NEWSIZE=$(stat -f%z "test-data/game_events.db" 2>/dev/null || stat -c%s "test-data/game_events.db" 2>/dev/null || echo "0")
    echo -e "${GREEN}📊 Database size: ${NEWSIZE} bytes${NC}"
else
    echo -e "${RED}❌ Database file lost${NC}"
    exit 1
fi

# Cleanup
echo -e "${YELLOW}🧹 Cleaning up...${NC}"
docker-compose -f docker-compose.test.yml down

echo -e "${GREEN}✅ Database persistence test PASSED!${NC}"
echo -e "${GREEN}📁 Test data preserved in: ./test-data/${NC}"
echo ""
echo -e "${YELLOW}💡 Next steps:${NC}"
echo "  1. Review the test data directory"
echo "  2. Run './deploy-ec2.sh' when ready to deploy"
echo "  3. Follow the migration checklist in MIGRATION_CHECKLIST.md"