#!/bin/bash
# EC2 Monitoring Script - Check game server status and metrics

set -e

# Configuration
EC2_HOST="${EC2_HOST:-54.250.35.226}"
EC2_USER="${EC2_USER:-ubuntu}"
KEY_PATH="${KEY_PATH:-~/.ssh/liap-tui-tokyo-key.pem}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if EC2_HOST is configured
if [ "$EC2_HOST" = "your-ec2-ip-here" ]; then
    echo -e "${RED}❌ Error: Please set EC2_HOST environment variable or edit this script${NC}"
    echo "Example: EC2_HOST=54.123.45.67 ./monitor-ec2.sh"
    exit 1
fi

echo -e "${BLUE}📊 Liap Tui EC2 Monitoring Dashboard${NC}"
echo -e "${BLUE}=================================${NC}"
echo -e "Host: ${EC2_HOST}"
echo -e "Time: $(date)"
echo ""

# Function to run remote command
run_remote() {
    ssh -o ConnectTimeout=5 -i ${KEY_PATH} ${EC2_USER}@${EC2_HOST} "$1" 2>/dev/null
}

# Check SSH connectivity
echo -e "${YELLOW}🔌 Checking connectivity...${NC}"
if ! run_remote "echo 'Connected'" > /dev/null; then
    echo -e "${RED}❌ Cannot connect to EC2 instance${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Connected successfully${NC}"
echo ""

# System Resources
echo -e "${BLUE}💻 System Resources${NC}"
echo -e "${BLUE}------------------${NC}"

# CPU and Load
CPU_INFO=$(run_remote "top -bn1 | grep 'Cpu(s)' | sed 's/.*, *\\([0-9.]*\\)%* id.*/\\1/' | awk '{print 100 - \$1}'")
LOAD_AVG=$(run_remote "uptime | awk -F'load average:' '{print \$2}'")
echo -e "CPU Usage: ${CPU_INFO}%"
echo -e "Load Average:${LOAD_AVG}"

# Memory
MEM_INFO=$(run_remote "free -m | awk 'NR==2{printf \"%.1f%% (Used: %sMB / Total: %sMB)\", \$3*100/\$2, \$3, \$2}'")
echo -e "Memory: ${MEM_INFO}"

# Disk
DISK_INFO=$(run_remote "df -h / | awk 'NR==2{printf \"%s (Used: %s / %s)\", \$5, \$3, \$2}'")
echo -e "Disk Usage: ${DISK_INFO}"

# Docker
DOCKER_COUNT=$(run_remote "docker ps -q | wc -l")
echo -e "Running Containers: ${DOCKER_COUNT}"
echo ""

# Application Status
echo -e "${BLUE}🎮 Application Status${NC}"
echo -e "${BLUE}-------------------${NC}"

# Container Status
CONTAINER_STATUS=$(run_remote "docker ps --filter name=liap-tui-game --format 'Status: {{.Status}}'")
if [ -z "$CONTAINER_STATUS" ]; then
    echo -e "${RED}❌ Container not running${NC}"
else
    echo -e "${GREEN}✅ ${CONTAINER_STATUS}${NC}"

    # Container Resources
    CONTAINER_STATS=$(run_remote "docker stats --no-stream --format 'CPU: {{.CPUPerc}} | Memory: {{.MemUsage}}' liap-tui-game")
    echo -e "Resources: ${CONTAINER_STATS}"
fi

# Health Check
echo -e "\n${YELLOW}🏥 Health Check...${NC}"
HEALTH_RESPONSE=$(curl -k -s -w "\n%{http_code}" https://${EC2_HOST}/api/health 2>/dev/null || echo "failed")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)
HEALTH_BODY=$(echo "$HEALTH_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ API Health: OK${NC}"
    if command -v jq &> /dev/null && [ ! -z "$HEALTH_BODY" ]; then
        echo "$HEALTH_BODY" | jq -r '. | "   Status: \(.status)\n   Uptime: \(.uptime)\n   Version: \(.version)"' 2>/dev/null || echo "   $HEALTH_BODY"
    fi
else
    echo -e "${RED}❌ API Health: Failed (HTTP $HTTP_CODE)${NC}"
fi

# Database Status
echo -e "\n${BLUE}💾 Database Status${NC}"
echo -e "${BLUE}-----------------${NC}"

DB_SIZE=$(run_remote "ls -lh /home/ubuntu/liap-tui-data/game_events.db 2>/dev/null | awk '{print \$5}'" || echo "N/A")
DB_MODIFIED=$(run_remote "ls -l /home/ubuntu/liap-tui-data/game_events.db 2>/dev/null | awk '{print \$6, \$7, \$8}'" || echo "N/A")

if [ "$DB_SIZE" != "N/A" ]; then
    echo -e "Database Size: ${DB_SIZE}"
    echo -e "Last Modified: ${DB_MODIFIED}"

    # Recent game activity (if accessible)
    RECENT_ROOMS=$(run_remote "docker exec liap-tui-game sqlite3 /app/data/game_events.db \"SELECT COUNT(DISTINCT room_id) FROM game_summaries WHERE datetime(started_at, 'unixepoch') > datetime('now', '-1 day')\" 2>/dev/null" || echo "N/A")
    if [ "$RECENT_ROOMS" != "N/A" ]; then
        echo -e "Games (last 24h): ${RECENT_ROOMS}"
    fi
else
    echo -e "${YELLOW}⚠️  Database not found or inaccessible${NC}"
fi

# Backup Status
echo -e "\n${BLUE}💾 Backup Status${NC}"
echo -e "${BLUE}---------------${NC}"

LATEST_BACKUP=$(run_remote "ls -t /home/ubuntu/backups/game_backup_*.tar.gz 2>/dev/null | head -1")
if [ ! -z "$LATEST_BACKUP" ]; then
    BACKUP_NAME=$(basename "$LATEST_BACKUP")
    BACKUP_SIZE=$(run_remote "ls -lh $LATEST_BACKUP | awk '{print \$5}'")
    echo -e "Latest: ${BACKUP_NAME} (${BACKUP_SIZE})"

    BACKUP_COUNT=$(run_remote "ls /home/ubuntu/backups/game_backup_*.tar.gz 2>/dev/null | wc -l")
    echo -e "Total Backups: ${BACKUP_COUNT}"
else
    echo -e "${YELLOW}⚠️  No backups found${NC}"
fi

# Recent Logs
echo -e "\n${BLUE}📋 Recent Activity${NC}"
echo -e "${BLUE}-----------------${NC}"

# Container logs (last 10 lines)
echo -e "\nRecent container logs:"
run_remote "docker logs --tail 10 liap-tui-game 2>&1 | grep -E 'ERROR|WARNING|Game.*started|Game.*completed' || echo 'No recent activity'" | sed 's/^/  /'

# Health check logs
HEALTH_LOG_COUNT=$(run_remote "tail -5 /home/ubuntu/logs/health-check.log 2>/dev/null | grep -c '❌' || echo '0'")
if [ "$HEALTH_LOG_COUNT" -gt 0 ]; then
    echo -e "\n${YELLOW}⚠️  Recent health check failures: ${HEALTH_LOG_COUNT}${NC}"
fi

# Network Status
echo -e "\n${BLUE}🌐 Network Status${NC}"
echo -e "${BLUE}----------------${NC}"

CONNECTIONS=$(run_remote "docker exec liap-tui-game netstat -an 2>/dev/null | grep ':5050' | grep ESTABLISHED | wc -l" || echo "0")
echo -e "Active Connections: ${CONNECTIONS}"

# Uptime
CONTAINER_UPTIME=$(run_remote "docker ps --filter name=liap-tui-game --format '{{.Status}}' | grep -oE '[0-9]+ (seconds?|minutes?|hours?|days?)'" || echo "N/A")
SYSTEM_UPTIME=$(run_remote "uptime -p" || echo "N/A")
echo -e "Container Uptime: ${CONTAINER_UPTIME}"
echo -e "System Uptime: ${SYSTEM_UPTIME}"

# Summary
echo -e "\n${BLUE}📊 Summary${NC}"
echo -e "${BLUE}---------${NC}"

# Determine overall status
STATUS="healthy"
STATUS_COLOR=$GREEN
STATUS_ICON="✅"

if [ "$HTTP_CODE" != "200" ] || [ "$DOCKER_COUNT" -eq 0 ]; then
    STATUS="unhealthy"
    STATUS_COLOR=$RED
    STATUS_ICON="❌"
elif [ "$HEALTH_LOG_COUNT" -gt 0 ] || [ "$DB_SIZE" = "N/A" ]; then
    STATUS="warning"
    STATUS_COLOR=$YELLOW
    STATUS_ICON="⚠️"
fi

echo -e "${STATUS_COLOR}${STATUS_ICON} Overall Status: ${STATUS}${NC}"
echo -e "\n${BLUE}=================================${NC}"

# Suggestions
if [ "$STATUS" != "healthy" ]; then
    echo -e "\n${YELLOW}💡 Suggestions:${NC}"

    if [ "$DOCKER_COUNT" -eq 0 ]; then
        echo -e "  - Start container: ssh to EC2 and run 'docker-compose up -d'"
    fi

    if [ "$HTTP_CODE" != "200" ]; then
        echo -e "  - Check container logs: docker logs liap-tui-game"
        echo -e "  - Restart container: docker-compose restart"
    fi

    if [ "$DB_SIZE" = "N/A" ]; then
        echo -e "  - Check database permissions: ls -la /home/ubuntu/liap-tui-data/"
    fi

    if [ "$HEALTH_LOG_COUNT" -gt 0 ]; then
        echo -e "  - Review health check logs: tail -50 /home/ubuntu/logs/health-check.log"
    fi
fi

echo ""