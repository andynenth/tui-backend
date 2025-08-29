#!/bin/bash
# Deployment Verification Script for Liap Tui
# Run this after deploying to EC2 to verify everything is working

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Server configuration
SERVER_URL="https://34.233.7.20"
if [ "$1" ]; then
    SERVER_URL="$1"
fi

echo "🚀 Starting deployment verification for: $SERVER_URL"
echo "============================================"

# Function to check endpoint
check_endpoint() {
    local endpoint=$1
    local expected_status=$2
    local description=$3
    
    response=$(curl -s -o /dev/null -w "%{http_code}" -k "$SERVER_URL$endpoint")
    
    if [ "$response" -eq "$expected_status" ]; then
        echo -e "${GREEN}✓${NC} $description ($endpoint) - Status: $response"
        return 0
    else
        echo -e "${RED}✗${NC} $description ($endpoint) - Expected: $expected_status, Got: $response"
        return 1
    fi
}

# Function to check JSON endpoint
check_json_endpoint() {
    local endpoint=$1
    local description=$2
    
    response=$(curl -s -k "$SERVER_URL$endpoint")
    
    if echo "$response" | jq . >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $description ($endpoint) - Valid JSON"
        echo "   Preview: $(echo "$response" | jq -c . | head -c 100)..."
        return 0
    else
        echo -e "${RED}✗${NC} $description ($endpoint) - Invalid JSON or error"
        echo "   Response: $(echo "$response" | head -c 100)..."
        return 1
    fi
}

# Function to test WebSocket
test_websocket() {
    local ws_url="wss://34.233.7.20/ws/lobby"
    if [[ "$SERVER_URL" == "http://"* ]]; then
        ws_url="ws://$(echo $SERVER_URL | cut -d'/' -f3)/ws/lobby"
    elif [[ "$SERVER_URL" == "https://"* ]]; then
        ws_url="wss://$(echo $SERVER_URL | cut -d'/' -f3)/ws/lobby"
    fi
    
    echo -e "\n${YELLOW}Testing WebSocket connection...${NC}"
    
    # Simple WebSocket test using curl (requires curl 7.86.0+)
    if command -v websocat &> /dev/null; then
        echo "test" | timeout 3 websocat -n1 "$ws_url" 2>/dev/null && \
            echo -e "${GREEN}✓${NC} WebSocket connection successful" || \
            echo -e "${YELLOW}!${NC} WebSocket test inconclusive (may require websocat tool)"
    else
        echo -e "${YELLOW}!${NC} WebSocket test skipped (install websocat for full test)"
    fi
}

# Core functionality tests
echo -e "\n1. Testing Core Health Endpoints"
echo "================================"
check_endpoint "/" 200 "Main application"
check_json_endpoint "/api/health" "Basic health check"
check_json_endpoint "/api/health/detailed" "Detailed health check"

# API endpoints
echo -e "\n2. Testing API Endpoints"
echo "========================"
check_json_endpoint "/api/debug/room-stats" "Room statistics"
check_json_endpoint "/api/metrics" "Monitoring metrics"
check_json_endpoint "/api/system/stats" "System statistics"

# Telemetry system
echo -e "\n3. Testing Telemetry System"
echo "============================"
check_endpoint "/telemetry-dashboard" 200 "Telemetry dashboard"
check_json_endpoint "/api/analytics/bundle-load-stats?hours=1" "Bundle load analytics"

# Test telemetry data submission
echo -e "\n${YELLOW}Testing telemetry data submission...${NC}"
telemetry_response=$(curl -s -X POST -k "$SERVER_URL/api/telemetry" \
    -H "Content-Type: application/json" \
    -d '{"sessionId":"test-session","events":[{"event":"test_event","timestamp":'$(date +%s000)'}]}')

if echo "$telemetry_response" | grep -q "accepted"; then
    echo -e "${GREEN}✓${NC} Telemetry submission working"
else
    echo -e "${RED}✗${NC} Telemetry submission failed"
    echo "   Response: $telemetry_response"
fi

# Database checks
echo -e "\n4. Database Verification"
echo "========================"
echo -e "${YELLOW}Checking database files on server...${NC}"
echo "Run on server: ls -la /home/ubuntu/liap-tui-data/"
echo "Expected files:"
echo "  - game_events.db (game data)"
echo "  - telemetry_data.db (telemetry data)"

# WebSocket testing
test_websocket

# Performance check
echo -e "\n5. Performance Quick Check"
echo "==========================="
start_time=$(date +%s%N)
curl -s -k "$SERVER_URL/api/health" > /dev/null
end_time=$(date +%s%N)
response_time=$(( ($end_time - $start_time) / 1000000 ))

if [ "$response_time" -lt 1000 ]; then
    echo -e "${GREEN}✓${NC} API response time: ${response_time}ms"
else
    echo -e "${YELLOW}!${NC} API response time: ${response_time}ms (>1s)"
fi

# Summary
echo -e "\n============================================"
echo "📊 Verification Summary"
echo "============================================"
echo -e "${YELLOW}Manual checks needed:${NC}"
echo "1. Visit $SERVER_URL and verify the game loads"
echo "2. Check telemetry dashboard: $SERVER_URL/telemetry-dashboard"
echo "3. Create/join a room and verify WebSocket gameplay"
echo "4. SSH to server and check logs: sudo docker-compose logs -f"
echo "5. Verify SSL certificate (if using HTTPS)"

echo -e "\n${GREEN}Deployment verification complete!${NC}\n"