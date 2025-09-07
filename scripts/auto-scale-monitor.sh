#!/bin/bash
# Auto-scaling monitor for Liap Tui - Monitors load and suggests scaling actions

set -e

# Configuration
EC2_HOST="${EC2_HOST:-your-ec2-ip-here}"
EC2_USER="${EC2_USER:-ubuntu}"
KEY_PATH="${KEY_PATH:-~/.ssh/your-key.pem}"

# Thresholds
CPU_THRESHOLD=80
MEMORY_THRESHOLD=85
CONNECTIONS_THRESHOLD=100
RESPONSE_TIME_THRESHOLD=1000  # milliseconds

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check configuration
if [ "$EC2_HOST" = "your-ec2-ip-here" ]; then
    echo -e "${RED}❌ Error: Please set EC2_HOST environment variable${NC}"
    exit 1
fi

# Function to run remote command
run_remote() {
    ssh -o ConnectTimeout=5 -i ${KEY_PATH} ${EC2_USER}@${EC2_HOST} "$1" 2>/dev/null
}

# Function to get metrics
get_cpu_usage() {
    run_remote "top -bn1 | grep 'Cpu(s)' | sed 's/.*, *\\([0-9.]*\\)%* id.*/\\1/' | awk '{print int(100 - \$1)}'"
}

get_memory_usage() {
    run_remote "free | awk 'NR==2{printf \"%d\", \$3*100/\$2}'"
}

get_active_connections() {
    run_remote "docker exec liap-tui-game netstat -an 2>/dev/null | grep ':5050' | grep ESTABLISHED | wc -l" || echo "0"
}

get_response_time() {
    curl -o /dev/null -s -w "%{time_total}\n" http://${EC2_HOST}/api/health | awk '{print int($1 * 1000)}'
}

get_container_count() {
    run_remote "docker ps -q | wc -l"
}

# Initialize tracking
SCALE_SCORE=0
RECOMMENDATIONS=()
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

echo -e "${BLUE}🚀 Auto-Scaling Analysis for Liap Tui${NC}"
echo -e "${BLUE}=====================================${NC}"
echo -e "Time: ${TIMESTAMP}"
echo -e "Host: ${EC2_HOST}"
echo ""

# Collect metrics
echo -e "${YELLOW}📊 Collecting metrics...${NC}"

CPU_USAGE=$(get_cpu_usage)
MEMORY_USAGE=$(get_memory_usage)
CONNECTIONS=$(get_active_connections)
RESPONSE_TIME=$(get_response_time)
CONTAINERS=$(get_container_count)

# Display current metrics
echo -e "\n${BLUE}Current Metrics:${NC}"
echo -e "├─ CPU Usage: ${CPU_USAGE}% (threshold: ${CPU_THRESHOLD}%)"
echo -e "├─ Memory Usage: ${MEMORY_USAGE}% (threshold: ${MEMORY_THRESHOLD}%)"
echo -e "├─ Active Connections: ${CONNECTIONS} (threshold: ${CONNECTIONS_THRESHOLD})"
echo -e "├─ Response Time: ${RESPONSE_TIME}ms (threshold: ${RESPONSE_TIME_THRESHOLD}ms)"
echo -e "└─ Running Containers: ${CONTAINERS}"

# Analyze metrics and calculate scale score
echo -e "\n${BLUE}📈 Scaling Analysis:${NC}"

# CPU Analysis
if [ $CPU_USAGE -gt $CPU_THRESHOLD ]; then
    SCALE_SCORE=$((SCALE_SCORE + 30))
    echo -e "${RED}⚠️  High CPU usage detected${NC}"
    RECOMMENDATIONS+=("Consider upgrading to t2.small or t3.medium for better CPU performance")
elif [ $CPU_USAGE -gt 60 ]; then
    SCALE_SCORE=$((SCALE_SCORE + 10))
    echo -e "${YELLOW}📊 Moderate CPU usage${NC}"
else
    echo -e "${GREEN}✅ CPU usage is healthy${NC}"
fi

# Memory Analysis
if [ $MEMORY_USAGE -gt $MEMORY_THRESHOLD ]; then
    SCALE_SCORE=$((SCALE_SCORE + 30))
    echo -e "${RED}⚠️  High memory usage detected${NC}"
    RECOMMENDATIONS+=("Consider upgrading instance type for more memory")
    RECOMMENDATIONS+=("Enable swap space as temporary measure: sudo fallocate -l 2G /swapfile")
elif [ $MEMORY_USAGE -gt 70 ]; then
    SCALE_SCORE=$((SCALE_SCORE + 10))
    echo -e "${YELLOW}📊 Moderate memory usage${NC}"
else
    echo -e "${GREEN}✅ Memory usage is healthy${NC}"
fi

# Connection Analysis
if [ $CONNECTIONS -gt $CONNECTIONS_THRESHOLD ]; then
    SCALE_SCORE=$((SCALE_SCORE + 25))
    echo -e "${RED}⚠️  High connection count detected${NC}"
    RECOMMENDATIONS+=("Consider implementing a load balancer")
    RECOMMENDATIONS+=("Enable connection pooling in application")
elif [ $CONNECTIONS -gt 50 ]; then
    SCALE_SCORE=$((SCALE_SCORE + 10))
    echo -e "${YELLOW}📊 Moderate connection count${NC}"
else
    echo -e "${GREEN}✅ Connection count is healthy${NC}"
fi

# Response Time Analysis
if [ $RESPONSE_TIME -gt $RESPONSE_TIME_THRESHOLD ]; then
    SCALE_SCORE=$((SCALE_SCORE + 15))
    echo -e "${RED}⚠️  Slow response times detected${NC}"
    RECOMMENDATIONS+=("Check application logs for bottlenecks")
    RECOMMENDATIONS+=("Consider enabling caching")
elif [ $RESPONSE_TIME -gt 500 ]; then
    SCALE_SCORE=$((SCALE_SCORE + 5))
    echo -e "${YELLOW}📊 Response times could be better${NC}"
else
    echo -e "${GREEN}✅ Response times are good${NC}"
fi

# Calculate scaling recommendation
echo -e "\n${BLUE}🎯 Scaling Score: ${SCALE_SCORE}/100${NC}"

if [ $SCALE_SCORE -ge 70 ]; then
    SCALE_RECOMMENDATION="URGENT: Scale up immediately"
    SCALE_COLOR=$RED
elif [ $SCALE_SCORE -ge 50 ]; then
    SCALE_RECOMMENDATION="WARNING: Consider scaling soon"
    SCALE_COLOR=$YELLOW
elif [ $SCALE_SCORE -ge 30 ]; then
    SCALE_RECOMMENDATION="MONITOR: Keep watching metrics"
    SCALE_COLOR=$YELLOW
else
    SCALE_RECOMMENDATION="HEALTHY: No scaling needed"
    SCALE_COLOR=$GREEN
fi

echo -e "${SCALE_COLOR}📊 Recommendation: ${SCALE_RECOMMENDATION}${NC}"

# Detailed recommendations
if [ ${#RECOMMENDATIONS[@]} -gt 0 ]; then
    echo -e "\n${BLUE}💡 Specific Recommendations:${NC}"
    for rec in "${RECOMMENDATIONS[@]}"; do
        echo -e "  • $rec"
    done
fi

# Scaling options
echo -e "\n${BLUE}🔧 Scaling Options:${NC}"

if [ $SCALE_SCORE -ge 50 ]; then
    echo -e "\n${YELLOW}Vertical Scaling (Upgrade Instance):${NC}"
    echo -e "  Current: t2.micro (1 vCPU, 1 GB RAM)"
    echo -e "  Options:"
    echo -e "    • t2.small  (1 vCPU, 2 GB RAM) - ~\$16/month"
    echo -e "    • t3.medium (2 vCPU, 4 GB RAM) - ~\$30/month"
    echo -e "    • t3.large  (2 vCPU, 8 GB RAM) - ~\$60/month"

    echo -e "\n${YELLOW}Horizontal Scaling (Multiple Instances):${NC}"
    echo -e "  • Add Application Load Balancer (ALB)"
    echo -e "  • Deploy multiple EC2 instances"
    echo -e "  • Use RDS for shared database"
    echo -e "  • Estimated cost: ~\$50+/month"
fi

# Performance optimization suggestions
echo -e "\n${BLUE}⚡ Performance Optimizations:${NC}"
echo -e "  1. Enable CloudFront CDN for static assets"
echo -e "  2. Implement Redis for session caching"
echo -e "  3. Optimize database queries and add indexes"
echo -e "  4. Enable gzip compression in application"
echo -e "  5. Use connection pooling for database"

# Cost optimization
if [ $SCALE_SCORE -lt 30 ]; then
    echo -e "\n${GREEN}💰 Cost Optimization:${NC}"
    echo -e "  Your instance is underutilized. Consider:"
    echo -e "  • Using t3.nano for even lower costs"
    echo -e "  • Implementing auto-stop during low usage hours"
    echo -e "  • Using spot instances for non-production"
fi

# Generate report file
REPORT_FILE="scaling_report_$(date +%Y%m%d_%H%M%S).txt"
{
    echo "Liap Tui Auto-Scaling Report"
    echo "Generated: ${TIMESTAMP}"
    echo "Host: ${EC2_HOST}"
    echo ""
    echo "Metrics:"
    echo "  CPU Usage: ${CPU_USAGE}%"
    echo "  Memory Usage: ${MEMORY_USAGE}%"
    echo "  Active Connections: ${CONNECTIONS}"
    echo "  Response Time: ${RESPONSE_TIME}ms"
    echo ""
    echo "Scaling Score: ${SCALE_SCORE}/100"
    echo "Recommendation: ${SCALE_RECOMMENDATION}"
    echo ""
    echo "Detailed Recommendations:"
    for rec in "${RECOMMENDATIONS[@]}"; do
        echo "  - $rec"
    done
} > "$REPORT_FILE"

echo -e "\n${GREEN}📄 Report saved to: ${REPORT_FILE}${NC}"

# Historical tracking
HISTORY_FILE="scaling_history.csv"
if [ ! -f "$HISTORY_FILE" ]; then
    echo "timestamp,cpu,memory,connections,response_time,scale_score,recommendation" > "$HISTORY_FILE"
fi
echo "${TIMESTAMP},${CPU_USAGE},${MEMORY_USAGE},${CONNECTIONS},${RESPONSE_TIME},${SCALE_SCORE},\"${SCALE_RECOMMENDATION}\"" >> "$HISTORY_FILE"

echo -e "\n${BLUE}📊 Next Steps:${NC}"
echo -e "  1. Review the recommendations above"
echo -e "  2. Check historical trends in ${HISTORY_FILE}"
echo -e "  3. Run './maintain-ec2.sh' for immediate actions"
echo -e "  4. Consider scheduling this script via cron for monitoring"
echo ""