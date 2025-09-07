#!/bin/bash
# EC2 Setup Script - Run this on a fresh Ubuntu 22.04 EC2 instance
# This script prepares the EC2 instance for hosting the Liap Tui game

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🚀 Starting EC2 setup for Liap Tui...${NC}"

# Update system packages
echo -e "${GREEN}📦 Updating system packages...${NC}"
sudo apt update
sudo apt upgrade -y

# Install Docker
echo -e "${GREEN}🐳 Installing Docker...${NC}"
sudo apt install -y docker.io docker-compose

# Add ubuntu user to docker group
echo -e "${GREEN}👤 Adding ubuntu user to docker group...${NC}"
sudo usermod -aG docker ubuntu

# Create necessary directories
echo -e "${GREEN}📁 Creating directories...${NC}"
mkdir -p /home/ubuntu/liap-tui-data
mkdir -p /home/ubuntu/backups
mkdir -p /home/ubuntu/logs

# Create backup script
echo -e "${GREEN}📝 Creating backup script...${NC}"
cat > /home/ubuntu/backup-game.sh << 'EOF'
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/ubuntu/backups"

# Create backup
docker run --rm \
  -v liap-tui-game_game_data:/data \
  -v ${BACKUP_DIR}:/backup \
  alpine tar czf /backup/game_backup_${TIMESTAMP}.tar.gz -C /data .

# Keep only last 7 daily backups
cd ${BACKUP_DIR}
ls -t game_backup_*.tar.gz 2>/dev/null | tail -n +8 | xargs -r rm

echo "✅ Backup completed: ${BACKUP_DIR}/game_backup_${TIMESTAMP}.tar.gz"
EOF

chmod +x /home/ubuntu/backup-game.sh

# Create health check script
echo -e "${GREEN}🏥 Creating health check script...${NC}"
cat > /home/ubuntu/health-check.sh << 'EOF'
#!/bin/bash
# Health check script - can be used by cron to monitor the application

if ! curl -f http://localhost/api/health > /dev/null 2>&1; then
    echo "❌ Health check failed at $(date)" >> /home/ubuntu/logs/health-check.log
    # Restart the container
    cd /home/ubuntu && docker-compose restart
    echo "🔄 Container restarted at $(date)" >> /home/ubuntu/logs/health-check.log
else
    echo "✅ Health check passed at $(date)" >> /home/ubuntu/logs/health-check.log
fi
EOF

chmod +x /home/ubuntu/health-check.sh

# Setup crontab for automated tasks
echo -e "${GREEN}⏰ Setting up cron jobs...${NC}"
(crontab -l 2>/dev/null || true; echo "# Daily backup at 2 AM") | crontab -
(crontab -l; echo "0 2 * * * /home/ubuntu/backup-game.sh >> /home/ubuntu/logs/backup.log 2>&1") | crontab -
(crontab -l; echo "# Health check every 5 minutes") | crontab -
(crontab -l; echo "*/5 * * * * /home/ubuntu/health-check.sh") | crontab -

# Configure firewall (ufw)
echo -e "${GREEN}🔥 Configuring firewall...${NC}"
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS (for future)
sudo ufw --force enable

# Install monitoring tools (optional but recommended)
echo -e "${GREEN}📊 Installing monitoring tools...${NC}"
sudo apt install -y htop iotop ncdu

# Create a simple systemd service for docker-compose (optional)
echo -e "${GREEN}🔧 Creating systemd service...${NC}"
sudo tee /etc/systemd/system/liap-tui.service > /dev/null << 'EOF'
[Unit]
Description=Liap Tui Game Server
Requires=docker.service
After=docker.service

[Service]
Type=simple
RemainAfterExit=true
WorkingDirectory=/home/ubuntu
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
Restart=always
User=ubuntu

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable liap-tui.service

# Print summary
echo -e "${GREEN}✅ EC2 setup completed!${NC}"
echo -e "${YELLOW}📋 Summary:${NC}"
echo "  - Docker and Docker Compose installed"
echo "  - Data directory: /home/ubuntu/liap-tui-data"
echo "  - Backup directory: /home/ubuntu/backups"
echo "  - Daily backups scheduled at 2 AM"
echo "  - Health checks every 5 minutes"
echo "  - Firewall configured (ports 22, 80, 443)"
echo ""
echo -e "${YELLOW}⚠️  Important next steps:${NC}"
echo "  1. Log out and log back in for docker group changes"
echo "  2. Upload docker-compose.yml to /home/ubuntu/"
echo "  3. Run: docker-compose up -d"
echo ""
echo -e "${GREEN}🎮 Happy gaming!${NC}"
