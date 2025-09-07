#!/bin/bash
# EC2 Restore Script - Restore game data from backup

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

# Check if EC2_HOST is configured
if [ "$EC2_HOST" = "your-ec2-ip-here" ]; then
    echo -e "${RED}❌ Error: Please set EC2_HOST environment variable or edit this script${NC}"
    echo "Example: EC2_HOST=54.123.45.67 ./restore-ec2.sh backup_file.tar.gz"
    exit 1
fi

# Check arguments
if [ $# -eq 0 ]; then
    echo -e "${RED}❌ Error: No backup file specified${NC}"
    echo "Usage: $0 <backup_file.tar.gz>"
    echo ""
    echo "Available local backups:"
    ls -lh backups/game_backup_*.tar.gz 2>/dev/null || echo "No backups found in ./backups/"
    exit 1
fi

BACKUP_FILE=$1

# Verify backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}❌ Error: Backup file not found: $BACKUP_FILE${NC}"
    exit 1
fi

echo -e "${BLUE}🔄 Liap Tui Data Restore${NC}"
echo -e "${BLUE}========================${NC}"
echo -e "Target: ${EC2_HOST}"
echo -e "Backup: ${BACKUP_FILE}"
echo -e "Size: $(ls -lh $BACKUP_FILE | awk '{print $5}')"
echo ""

# Warning
echo -e "${RED}⚠️  WARNING: This will replace ALL game data on the server!${NC}"
echo -e "${RED}   Current data will be backed up first.${NC}"
read -p "Continue? (y/N): " confirm

if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo -e "${YELLOW}Restore cancelled${NC}"
    exit 0
fi

# Function to run remote command
run_remote() {
    ssh -o ConnectTimeout=5 -i ${KEY_PATH} ${EC2_USER}@${EC2_HOST} "$1"
}

# Step 1: Create current backup
echo -e "\n${YELLOW}📦 Creating backup of current data...${NC}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
run_remote "/home/ubuntu/backup-game.sh"

# Download current backup
CURRENT_BACKUP=$(run_remote "ls -t /home/ubuntu/backups/game_backup_*.tar.gz | head -1")
if [ ! -z "$CURRENT_BACKUP" ]; then
    echo -e "${YELLOW}Downloading current backup...${NC}"
    mkdir -p ./backups/before-restore
    scp -i ${KEY_PATH} ${EC2_USER}@${EC2_HOST}:${CURRENT_BACKUP} ./backups/before-restore/
    echo -e "${GREEN}✅ Current data backed up to: ./backups/before-restore/$(basename $CURRENT_BACKUP)${NC}"
fi

# Step 2: Stop container
echo -e "\n${YELLOW}🛑 Stopping game container...${NC}"
run_remote "cd /home/ubuntu && docker-compose down"

# Step 3: Upload backup file
echo -e "\n${YELLOW}📤 Uploading backup file...${NC}"
scp -i ${KEY_PATH} ${BACKUP_FILE} ${EC2_USER}@${EC2_HOST}:/tmp/restore_backup.tar.gz

# Step 4: Clear existing data
echo -e "\n${YELLOW}🧹 Clearing existing data...${NC}"
run_remote "sudo rm -rf /home/ubuntu/liap-tui-data/*"

# Step 5: Restore from backup
echo -e "\n${YELLOW}📥 Restoring from backup...${NC}"
run_remote "sudo tar -xzf /tmp/restore_backup.tar.gz -C /home/ubuntu/liap-tui-data/"

# Step 6: Fix permissions
echo -e "\n${YELLOW}🔧 Fixing permissions...${NC}"
run_remote "sudo chown -R ubuntu:ubuntu /home/ubuntu/liap-tui-data"

# Step 7: Start container
echo -e "\n${YELLOW}🚀 Starting game container...${NC}"
run_remote "cd /home/ubuntu && docker-compose up -d"

# Step 8: Clean up
echo -e "\n${YELLOW}🧹 Cleaning up temporary files...${NC}"
run_remote "rm /tmp/restore_backup.tar.gz"

# Step 9: Verify
echo -e "\n${YELLOW}✅ Verifying restore...${NC}"

# Wait for container to be ready
sleep 10

# Check health
if curl -f http://${EC2_HOST}/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Health check passed${NC}"
else
    echo -e "${RED}❌ Health check failed${NC}"
    echo -e "${YELLOW}Check container logs: ssh to EC2 and run 'docker logs liap-tui-game'${NC}"
fi

# Check database
DB_INFO=$(run_remote "ls -lh /home/ubuntu/liap-tui-data/game_events.db 2>/dev/null" || echo "Database not found")
echo -e "\nDatabase info: ${DB_INFO}"

# Get game count
GAME_COUNT=$(run_remote "docker exec liap-tui-game sqlite3 /app/data/game_events.db 'SELECT COUNT(*) FROM game_summaries' 2>/dev/null" || echo "0")
echo -e "Total games in database: ${GAME_COUNT}"

echo -e "\n${GREEN}✅ Restore completed successfully!${NC}"
echo -e "\n${BLUE}Post-Restore Checklist:${NC}"
echo -e "  1. Test game creation and gameplay"
echo -e "  2. Verify player data is intact"
echo -e "  3. Check play history for specific rooms"
echo -e "  4. Monitor logs for any errors"
echo -e "\n${YELLOW}💡 Tip: Run './monitor-ec2.sh' to check system status${NC}"
