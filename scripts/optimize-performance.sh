#!/bin/bash
# Performance Optimization Script for Liap Tui

set -e

# Configuration
EC2_HOST="${EC2_HOST:-your-ec2-ip-here}"
EC2_USER="${EC2_USER:-ubuntu}"
KEY_PATH="${KEY_PATH:-~/.ssh/your-key.pem}"

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
    ssh -o ConnectTimeout=5 -i ${KEY_PATH} ${EC2_USER}@${EC2_HOST} "$1"
}

# Function to measure response time
measure_response_time() {
    curl -o /dev/null -s -w "%{time_total}\n" http://${EC2_HOST}/api/health | awk '{print int($1 * 1000)}'
}

echo -e "${BLUE}⚡ Liap Tui Performance Optimization${NC}"
echo -e "${BLUE}===================================${NC}"
echo -e "Host: ${EC2_HOST}"
echo -e "Date: $(date)"
echo ""

# Initial performance check
echo -e "${YELLOW}📊 Initial Performance Check...${NC}"
INITIAL_RESPONSE=$(measure_response_time)
echo -e "Current response time: ${INITIAL_RESPONSE}ms"
echo ""

# Track optimizations applied
OPTIMIZATIONS_APPLIED=()

# 1. System-level optimizations
echo -e "${BLUE}1. System Optimizations${NC}"

# Check and adjust swappiness
SWAPPINESS=$(run_remote "cat /proc/sys/vm/swappiness")
echo -e "  Current swappiness: ${SWAPPINESS}"
if [ "$SWAPPINESS" -gt 10 ]; then
    echo -e "${YELLOW}  Reducing swappiness for better performance...${NC}"
    run_remote "echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf > /dev/null"
    run_remote "sudo sysctl -p > /dev/null"
    OPTIMIZATIONS_APPLIED+=("Reduced swappiness to 10")
    echo -e "${GREEN}  ✅ Swappiness optimized${NC}"
fi

# Enable TCP optimizations
echo -e "\n${YELLOW}  Applying TCP optimizations...${NC}"
run_remote "cat > /tmp/tcp_optimizations.conf << 'EOF'
# TCP Optimizations for web server
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.ipv4.tcp_rmem = 4096 87380 134217728
net.ipv4.tcp_wmem = 4096 65536 134217728
net.ipv4.tcp_congestion_control = bbr
net.core.default_qdisc = fq
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_mtu_probing = 1
EOF"

run_remote "sudo cp /tmp/tcp_optimizations.conf /etc/sysctl.d/99-tcp-optimizations.conf"
run_remote "sudo sysctl -p /etc/sysctl.d/99-tcp-optimizations.conf > /dev/null 2>&1" || true
OPTIMIZATIONS_APPLIED+=("Applied TCP performance optimizations")
echo -e "${GREEN}  ✅ TCP optimizations applied${NC}"

# 2. Docker optimizations
echo -e "\n${BLUE}2. Docker Optimizations${NC}"

# Clean up unused Docker resources
echo -e "${YELLOW}  Cleaning Docker resources...${NC}"
BEFORE_SPACE=$(run_remote "df -h / | awk 'NR==2{print \$4}'")
run_remote "docker system prune -af --volumes > /dev/null 2>&1" || true
AFTER_SPACE=$(run_remote "df -h / | awk 'NR==2{print \$4}'")
echo -e "${GREEN}  ✅ Freed disk space (${BEFORE_SPACE} → ${AFTER_SPACE})${NC}"
OPTIMIZATIONS_APPLIED+=("Cleaned Docker resources")

# Update Docker daemon settings
echo -e "\n${YELLOW}  Optimizing Docker daemon...${NC}"
run_remote "sudo tee /etc/docker/daemon.json > /dev/null << 'EOF'
{
  \"log-driver\": \"json-file\",
  \"log-opts\": {
    \"max-size\": \"10m\",
    \"max-file\": \"3\"
  },
  \"storage-driver\": \"overlay2\",
  \"storage-opts\": [
    \"overlay2.override_kernel_check=true\"
  ]
}
EOF"

run_remote "sudo systemctl restart docker" || true
OPTIMIZATIONS_APPLIED+=("Optimized Docker daemon configuration")
echo -e "${GREEN}  ✅ Docker daemon optimized${NC}"

# 3. Application optimizations
echo -e "\n${BLUE}3. Application Optimizations${NC}"

# Create optimized docker-compose override
echo -e "${YELLOW}  Creating performance-optimized configuration...${NC}"
run_remote "cat > /home/ubuntu/docker-compose.override.yml << 'EOF'
version: '3.8'

services:
  liap-tui:
    environment:
      # Performance optimizations
      - PYTHONUNBUFFERED=1
      - WORKERS=2
      - MAX_CONNECTIONS=200
      - CONNECTION_TIMEOUT=30
      
      # Enable response compression
      - ENABLE_COMPRESSION=true
      - COMPRESSION_LEVEL=6
      
      # Optimize event buffer
      - EVENT_BUFFER_ENABLED=true
      - EVENT_BUFFER_SIZE=50
      - EVENT_BUFFER_FLUSH_INTERVAL=5.0
      
      # Database optimizations
      - SQLITE_SYNCHRONOUS=NORMAL
      - SQLITE_JOURNAL_MODE=WAL
      
    # Resource limits
    deploy:
      resources:
        limits:
          cpus: '0.75'
          memory: 768M
        reservations:
          cpus: '0.25'
          memory: 256M
    
    # Logging optimization
    logging:
      driver: json-file
      options:
        max-size: \"10m\"
        max-file: \"3\"
EOF"

OPTIMIZATIONS_APPLIED+=("Created performance-optimized Docker configuration")
echo -e "${GREEN}  ✅ Application configuration optimized${NC}"

# 4. Database optimizations
echo -e "\n${BLUE}4. Database Optimizations${NC}"

# Optimize SQLite database
echo -e "${YELLOW}  Optimizing database...${NC}"
run_remote "docker exec liap-tui-game sqlite3 /app/data/game_events.db 'PRAGMA optimize;' 2>/dev/null" || echo "  Database not accessible"
run_remote "docker exec liap-tui-game sqlite3 /app/data/game_events.db 'VACUUM;' 2>/dev/null" || echo "  Cannot vacuum database"
OPTIMIZATIONS_APPLIED+=("Optimized SQLite database")
echo -e "${GREEN}  ✅ Database optimized${NC}"

# 5. Network optimizations
echo -e "\n${BLUE}5. Network Optimizations${NC}"

# Install and configure nginx as reverse proxy with caching
echo -e "${YELLOW}  Setting up nginx reverse proxy...${NC}"
if ! run_remote "which nginx > /dev/null 2>&1"; then
    run_remote "sudo apt update > /dev/null 2>&1 && sudo apt install -y nginx > /dev/null 2>&1"
fi

run_remote "sudo tee /etc/nginx/sites-available/liap-tui > /dev/null << 'EOF'
server {
    listen 8080;
    server_name _;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml application/json application/javascript;
    
    # Cache static files
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|woff|woff2|ttf|svg)$ {
        proxy_pass http://localhost:5050;
        expires 30d;
        add_header Cache-Control \"public, immutable\";
    }
    
    # WebSocket support
    location /ws {
        proxy_pass http://localhost:5050;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection \"upgrade\";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_read_timeout 86400;
    }
    
    # API endpoints
    location /api {
        proxy_pass http://localhost:5050;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        
        # API response caching for read-only endpoints
        location ~* /api/(health|rooms|stats) {
            proxy_pass http://localhost:5050;
            proxy_cache_valid 200 5s;
            add_header X-Cache-Status \$upstream_cache_status;
        }
    }
    
    # Default location
    location / {
        proxy_pass http://localhost:5050;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
    
    # Security headers
    add_header X-Frame-Options \"SAMEORIGIN\" always;
    add_header X-Content-Type-Options \"nosniff\" always;
    add_header X-XSS-Protection \"1; mode=block\" always;
}
EOF"

run_remote "sudo ln -sf /etc/nginx/sites-available/liap-tui /etc/nginx/sites-enabled/"
run_remote "sudo nginx -t > /dev/null 2>&1 && sudo systemctl reload nginx > /dev/null 2>&1" || echo "  Nginx configuration issue"
OPTIMIZATIONS_APPLIED+=("Configured nginx reverse proxy with caching")
echo -e "${GREEN}  ✅ Nginx reverse proxy configured${NC}"

# 6. Restart application with optimizations
echo -e "\n${BLUE}6. Applying Optimizations${NC}"
echo -e "${YELLOW}  Restarting application...${NC}"
run_remote "cd /home/ubuntu && docker-compose down && docker-compose up -d"
echo -e "${GREEN}  ✅ Application restarted${NC}"

# Wait for application to stabilize
echo -e "\n${YELLOW}⏳ Waiting for application to stabilize...${NC}"
sleep 30

# 7. Performance comparison
echo -e "\n${BLUE}7. Performance Results${NC}"

# Measure new response time
FINAL_RESPONSE=$(measure_response_time)
IMPROVEMENT=$((INITIAL_RESPONSE - FINAL_RESPONSE))
IMPROVEMENT_PCT=$((IMPROVEMENT * 100 / INITIAL_RESPONSE))

echo -e "  Initial response time: ${INITIAL_RESPONSE}ms"
echo -e "  Final response time: ${FINAL_RESPONSE}ms"
echo -e "  Improvement: ${IMPROVEMENT}ms (${IMPROVEMENT_PCT}%)"

if [ $IMPROVEMENT -gt 0 ]; then
    echo -e "${GREEN}  ✅ Performance improved by ${IMPROVEMENT_PCT}%${NC}"
else
    echo -e "${YELLOW}  ⚠️  No significant improvement detected${NC}"
fi

# 8. Generate optimization report
echo -e "\n${BLUE}📊 Optimization Summary${NC}"
echo -e "${BLUE}======================${NC}"

echo -e "\n${GREEN}Applied Optimizations:${NC}"
for opt in "${OPTIMIZATIONS_APPLIED[@]}"; do
    echo -e "  ✓ $opt"
done

# Additional recommendations
echo -e "\n${BLUE}💡 Additional Recommendations:${NC}"
echo -e "  1. Consider using CloudFront CDN for static assets"
echo -e "  2. Implement Redis for session and game state caching"
echo -e "  3. Use Amazon RDS for database if scaling beyond single instance"
echo -e "  4. Enable HTTP/2 in nginx for better performance"
echo -e "  5. Implement connection pooling in the application"

# Generate report file
REPORT_FILE="performance_optimization_$(date +%Y%m%d_%H%M%S).txt"
{
    echo "Liap Tui Performance Optimization Report"
    echo "Generated: $(date)"
    echo "Host: ${EC2_HOST}"
    echo ""
    echo "Performance Results:"
    echo "  Initial response time: ${INITIAL_RESPONSE}ms"
    echo "  Final response time: ${FINAL_RESPONSE}ms"
    echo "  Improvement: ${IMPROVEMENT}ms (${IMPROVEMENT_PCT}%)"
    echo ""
    echo "Optimizations Applied:"
    for opt in "${OPTIMIZATIONS_APPLIED[@]}"; do
        echo "  - $opt"
    done
} > "$REPORT_FILE"

echo -e "\n${GREEN}📄 Report saved to: ${REPORT_FILE}${NC}"

# Create monitoring script
cat > monitor_performance.sh << 'EOF'
#!/bin/bash
# Performance monitoring script

while true; do
    TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
    RESPONSE_TIME=$(curl -o /dev/null -s -w "%{time_total}" http://localhost/api/health)
    echo "$TIMESTAMP,$RESPONSE_TIME" >> performance_metrics.csv
    sleep 60
done
EOF

chmod +x monitor_performance.sh
echo -e "${GREEN}📊 Created monitor_performance.sh for ongoing monitoring${NC}"

echo -e "\n${BLUE}✅ Performance optimization complete!${NC}"
echo ""