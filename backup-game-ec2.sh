#\!/bin/bash
# Backup Liap Tui game data from EC2

# Configuration
EC2_HOST="${EC2_HOST:-54.250.35.226}"
EC2_USER="${EC2_USER:-ubuntu}"
KEY_PATH="${KEY_PATH:-~/.ssh/liap-tui-tokyo-key.pem}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="game_backup_${TIMESTAMP}.tar.gz"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🎮 Liap Tui Game Backup${NC}"
echo -e "${BLUE}======================${NC}"
echo -e "Time: $(date)"
echo -e "Server: ${EC2_HOST}"
echo ""

# Create local backup directory
mkdir -p backups

# Step 1: Check game status
echo -e "${YELLOW}Checking game status...${NC}"
STATUS=$(ssh -o ConnectTimeout=5 -i ${KEY_PATH} ${EC2_USER}@${EC2_HOST} "docker ps --filter name=liap-tui-game --format '{{.Status}}'" 2>/dev/null)

if [ -z "$STATUS" ]; then
    echo -e "${RED}❌ Could not connect to server or container not running${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Game container status: ${STATUS}${NC}"

# Step 2: Get database info
echo -e "\n${YELLOW}Getting database information...${NC}"
DB_SIZE=$(ssh -i ${KEY_PATH} ${EC2_USER}@${EC2_HOST} "ls -lh /home/ubuntu/liap-tui-data/game_events.db 2>/dev/null  < /dev/null |  awk '{print \$5}'" || echo "Unknown")
echo -e "Database size: ${DB_SIZE}"

# Step 3: Create backup on EC2
echo -e "\n${YELLOW}Creating backup on server...${NC}"
ssh -i ${KEY_PATH} ${EC2_USER}@${EC2_HOST} << ENDSSH
  # Create backup directory
  mkdir -p /home/ubuntu/backups

  # Create backup
  cd /home/ubuntu/liap-tui-data
  tar czf /home/ubuntu/backups/${BACKUP_NAME} game_events.db

  # Get backup size
  ls -lh /home/ubuntu/backups/${BACKUP_NAME}
ENDSSH

# Step 4: Download backup
echo -e "\n${YELLOW}Downloading backup...${NC}"
scp -i ${KEY_PATH} ${EC2_USER}@${EC2_HOST}:/home/ubuntu/backups/${BACKUP_NAME} ./backups/

# Step 5: Verify backup
if [ -f "./backups/${BACKUP_NAME}" ]; then
    LOCAL_SIZE=$(ls -lh "./backups/${BACKUP_NAME}" | awk '{print $5}')
    echo -e "${GREEN}✅ Backup downloaded successfully\!${NC}"
    echo -e "Local backup: ./backups/${BACKUP_NAME} (${LOCAL_SIZE})"

    # Extract and check
    echo -e "\n${YELLOW}Verifying backup contents...${NC}"
    tar -tzf "./backups/${BACKUP_NAME}" | head -5

    # Create restore script
    cat > restore-backup.sh << 'RESTORE_EOF'
#\!/bin/bash
# Restore game backup to EC2

BACKUP_FILE="$1"
EC2_HOST="${EC2_HOST:-34.233.7.20}"
EC2_USER="${EC2_USER:-ubuntu}"
KEY_PATH="${KEY_PATH:-./liap-tui-key-1755152170.pem}"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: ./restore-backup.sh <backup-file>"
    echo "Example: ./restore-backup.sh backups/game_backup_20250813_235507.tar.gz"
    exit 1
fi

if [ \! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "⚠️  WARNING: This will replace the current game database\!"
echo -n "Are you sure? (yes/no): "
read CONFIRM

if [ "$CONFIRM" \!= "yes" ]; then
    echo "Restore cancelled"
    exit 0
fi

echo "Uploading backup to server..."
scp -i ${KEY_PATH} ${BACKUP_FILE} ${EC2_USER}@${EC2_HOST}:/tmp/restore.tar.gz

echo "Stopping game container..."
ssh -i ${KEY_PATH} ${EC2_USER}@${EC2_HOST} "docker stop liap-tui-game"

echo "Restoring backup..."
ssh -i ${KEY_PATH} ${EC2_USER}@${EC2_HOST} << 'ENDSSH'
  cd /home/ubuntu/liap-tui-data
  # Backup current database
  cp game_events.db game_events.db.before-restore
  # Extract new database
  tar xzf /tmp/restore.tar.gz
  # Clean up
  rm /tmp/restore.tar.gz
ENDSSH

echo "Starting game container..."
ssh -i ${KEY_PATH} ${EC2_USER}@${EC2_HOST} "docker start liap-tui-game"

echo "✅ Restore completed\!"
RESTORE_EOF

    chmod +x restore-backup.sh
    echo -e "\n${GREEN}✅ Created restore script: ./restore-backup.sh${NC}"

else
    echo -e "${RED}❌ Backup download failed${NC}"
    exit 1
fi

# Step 6: Clean up old backups on EC2 (keep last 7)
echo -e "\n${YELLOW}Cleaning up old backups on server...${NC}"
ssh -i ${KEY_PATH} ${EC2_USER}@${EC2_HOST} << 'ENDSSH'
  cd /home/ubuntu/backups
  ls -t game_backup_*.tar.gz 2>/dev/null | tail -n +8 | xargs -r rm -v
ENDSSH

echo -e "\n${BLUE}Backup Summary:${NC}"
echo -e "${BLUE}===============${NC}"
echo -e "✅ Backup created: ${BACKUP_NAME}"
echo -e "✅ Database size: ${DB_SIZE}"
echo -e "✅ Backup location: ./backups/${BACKUP_NAME}"
echo -e "✅ Restore script: ./restore-backup.sh"
echo -e "\nTo restore this backup later:"
echo -e "  ${GREEN}./restore-backup.sh backups/${BACKUP_NAME}${NC}"
