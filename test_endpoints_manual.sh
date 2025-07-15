#!/bin/bash
# Manual test script for REST endpoints
# This script tests each endpoint with curl and shows the results

BASE_URL="http://localhost:5050/api"

echo "======================================"
echo "Testing Liap Tui REST API Endpoints"
echo "======================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to test endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local description=$3
    local data=$4
    
    echo -e "${BLUE}Testing: $description${NC}"
    echo "Endpoint: $method $endpoint"
    
    if [ "$method" == "GET" ]; then
        response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "$BASE_URL$endpoint")
    else
        if [ -n "$data" ]; then
            response=$(curl -s -X $method -w "\nHTTP_STATUS:%{http_code}" "$BASE_URL$endpoint" -H "Content-Type: application/json" -d "$data")
        else
            response=$(curl -s -X $method -w "\nHTTP_STATUS:%{http_code}" "$BASE_URL$endpoint")
        fi
    fi
    
    http_status=$(echo "$response" | tail -n 1 | cut -d: -f2)
    body=$(echo "$response" | sed '$d')
    
    echo "Status: $http_status"
    
    if [ "$http_status" == "200" ]; then
        echo -e "${GREEN}✓ Success${NC}"
        # Pretty print JSON if possible
        if command -v jq &> /dev/null && [ -n "$body" ]; then
            echo "$body" | jq '.' 2>/dev/null || echo "$body"
        else
            echo "$body"
        fi
    else
        echo -e "${RED}✗ Failed${NC}"
        echo "$body"
    fi
    
    echo "--------------------------------------"
    echo ""
}

# Check if server is running
echo "Checking server connection..."
if curl -s -f "$BASE_URL/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Server is running${NC}"
else
    echo -e "${RED}✗ Cannot connect to server at $BASE_URL${NC}"
    echo "Please ensure the server is running with: ./start.sh"
    exit 1
fi

echo ""
echo "======================================"
echo "Health Monitoring Endpoints"
echo "======================================"
echo ""

test_endpoint "GET" "/health" "Basic Health Check"
test_endpoint "GET" "/health/detailed" "Detailed Health Check"
test_endpoint "GET" "/health/metrics" "Prometheus Metrics (first 10 lines)" | head -n 20

echo ""
echo "======================================"
echo "Debug and Admin Endpoints"
echo "======================================"
echo ""

test_endpoint "GET" "/debug/room-stats" "Room Statistics (All Rooms)"
test_endpoint "GET" "/debug/room-stats?room_id=TEST123" "Room Statistics (Specific Room)"

echo ""
echo "======================================"
echo "System Statistics"
echo "======================================"
echo ""

test_endpoint "GET" "/system/stats" "Comprehensive System Stats"

echo ""
echo "======================================"
echo "Event Store Management"
echo "======================================"
echo ""

test_endpoint "GET" "/event-store/stats" "Event Store Statistics"
test_endpoint "GET" "/rooms/TEST123/events?limit=5" "Room Events (limit 5)"

echo ""
echo "======================================"
echo "Recovery System"
echo "======================================"
echo ""

test_endpoint "GET" "/recovery/status" "Recovery System Status"

echo ""
echo "======================================"
echo "Test Complete!"
echo "======================================" 