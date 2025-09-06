#\!/bin/bash
# Quick monitoring dashboard for Liap Tui

EC2_HOST="${EC2_HOST:-34.233.7.20}"
KEY_PATH="${KEY_PATH:-./liap-tui-key-1755152170.pem}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

clear
echo -e "${BLUE}🎮 Liap Tui Quick Monitor${NC}"
echo -e "${BLUE}========================${NC}"
echo -e "Server: ${EC2_HOST}"
echo -e "Time: $(date)"
echo ""

# 1. Game Health
echo -e "${YELLOW}Checking game health...${NC}"
HEALTH=$(curl -s http://${EC2_HOST}/api/health  < /dev/null |  python3 -m json.tool 2>/dev/null)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Game is healthy${NC}"
    echo "$HEALTH" | grep -E "uptime_formatted|version" | sed 's/^/  /'
else
    echo -e "${RED}❌ Game health check failed${NC}"
fi

# 2. Server Resources
echo -e "\n${YELLOW}Server resources:${NC}"
ssh -o ConnectTimeout=5 -i ${KEY_PATH} ubuntu@${EC2_HOST} << 'EOF' 2>/dev/null
    # CPU and Memory
    echo -n "  CPU: "
    top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1
    echo -n "  Memory: "
    free -m | awk 'NR==2{printf "%.1f%% (Used: %sMB / Total: %sMB)\n", $3*100/$2, $3, $2}'
    echo -n "  Disk: "
    df -h / | awk 'NR==2{printf "%s (Used: %s / %s)\n", $5, $3, $2}'
    echo -n "  Docker: "
    docker ps --filter name=liap-tui --format "{{.Status}}"
