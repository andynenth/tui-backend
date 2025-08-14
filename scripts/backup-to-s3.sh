#!/bin/bash
# Automated backup to AWS S3 for Liap Tui

set -e

# Configuration
EC2_HOST="${EC2_HOST:-your-ec2-ip-here}"
EC2_USER="${EC2_USER:-ubuntu}"
KEY_PATH="${KEY_PATH:-~/.ssh/your-key.pem}"
S3_BUCKET="${S3_BUCKET:-your-s3-bucket-name}"
S3_PREFIX="${S3_PREFIX:-liap-tui-backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check configuration
if [ "$EC2_HOST" = "your-ec2-ip-here" ] || [ "$S3_BUCKET" = "your-s3-bucket-name" ]; then
    echo -e "${RED}❌ Error: Please configure environment variables${NC}"
    echo "Required:"
    echo "  EC2_HOST=your-ec2-ip"
    echo "  S3_BUCKET=your-s3-bucket-name"
    echo ""
    echo "Optional:"
    echo "  S3_PREFIX=liap-tui-backups (default)"
    echo "  RETENTION_DAYS=30 (default)"
    exit 1
fi

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ Error: AWS CLI not installed${NC}"
    echo "Install with: pip install awscli"
    exit 1
fi

# Function to run remote command
run_remote() {
    ssh -o ConnectTimeout=5 -i ${KEY_PATH} ${EC2_USER}@${EC2_HOST} "$1"
}

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="game_backup_${TIMESTAMP}.tar.gz"

echo -e "${BLUE}☁️  Liap Tui S3 Backup${NC}"
echo -e "${BLUE}====================${NC}"
echo -e "Time: $(date)"
echo -e "EC2 Host: ${EC2_HOST}"
echo -e "S3 Bucket: s3://${S3_BUCKET}/${S3_PREFIX}/"
echo ""

# Step 1: Create backup on EC2
echo -e "${YELLOW}📦 Creating backup on EC2...${NC}"
run_remote "/home/ubuntu/backup-game.sh" > /dev/null 2>&1

# Get the latest backup file
LATEST_BACKUP=$(run_remote "ls -t /home/ubuntu/backups/game_backup_*.tar.gz | head -1")
if [ -z "$LATEST_BACKUP" ]; then
    echo -e "${RED}❌ No backup found on EC2${NC}"
    exit 1
fi

BACKUP_SIZE=$(run_remote "ls -lh $LATEST_BACKUP | awk '{print \$5}'")
echo -e "${GREEN}✅ Backup created: $(basename $LATEST_BACKUP) (${BACKUP_SIZE})${NC}"

# Step 2: Calculate backup checksum
echo -e "\n${YELLOW}🔐 Calculating checksum...${NC}"
CHECKSUM=$(run_remote "sha256sum $LATEST_BACKUP | awk '{print \$1}'")
echo -e "${GREEN}✅ Checksum: ${CHECKSUM:0:16}...${NC}"

# Step 3: Download backup
echo -e "\n${YELLOW}📥 Downloading backup...${NC}"
mkdir -p /tmp/liap-tui-backups
scp -i ${KEY_PATH} ${EC2_USER}@${EC2_HOST}:${LATEST_BACKUP} /tmp/liap-tui-backups/${BACKUP_NAME}

# Verify download
LOCAL_CHECKSUM=$(sha256sum /tmp/liap-tui-backups/${BACKUP_NAME} | awk '{print $1}')
if [ "$CHECKSUM" != "$LOCAL_CHECKSUM" ]; then
    echo -e "${RED}❌ Checksum mismatch! Backup may be corrupted${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Download verified${NC}"

# Step 4: Get database statistics
echo -e "\n${YELLOW}📊 Gathering backup metadata...${NC}"
DB_INFO=$(run_remote "docker exec liap-tui-game sqlite3 /app/data/game_events.db 'SELECT COUNT(*) as games FROM game_summaries;' 2>/dev/null" || echo "0")
METADATA=$(cat <<EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "source_host": "${EC2_HOST}",
  "backup_size": "${BACKUP_SIZE}",
  "checksum": "${CHECKSUM}",
  "total_games": "${DB_INFO}",
  "retention_days": ${RETENTION_DAYS}
}
EOF
)

# Save metadata
echo "$METADATA" > /tmp/liap-tui-backups/${BACKUP_NAME}.metadata.json

# Step 5: Upload to S3
echo -e "\n${YELLOW}☁️  Uploading to S3...${NC}"

# Upload backup file
aws s3 cp /tmp/liap-tui-backups/${BACKUP_NAME} \
    s3://${S3_BUCKET}/${S3_PREFIX}/${BACKUP_NAME} \
    --storage-class STANDARD_IA \
    --metadata "checksum=${CHECKSUM},games=${DB_INFO}"

# Upload metadata
aws s3 cp /tmp/liap-tui-backups/${BACKUP_NAME}.metadata.json \
    s3://${S3_BUCKET}/${S3_PREFIX}/${BACKUP_NAME}.metadata.json

echo -e "${GREEN}✅ Upload complete${NC}"

# Step 6: Set lifecycle policy for automatic deletion
echo -e "\n${YELLOW}⏰ Setting retention policy...${NC}"

# Tag the backup with expiration date
EXPIRATION_DATE=$(date -d "+${RETENTION_DAYS} days" +%Y-%m-%d)
aws s3api put-object-tagging \
    --bucket ${S3_BUCKET} \
    --key ${S3_PREFIX}/${BACKUP_NAME} \
    --tagging "TagSet=[{Key=ExpirationDate,Value=${EXPIRATION_DATE}},{Key=Type,Value=GameBackup}]"

echo -e "${GREEN}✅ Backup will expire on ${EXPIRATION_DATE}${NC}"

# Step 7: Clean up old backups
echo -e "\n${YELLOW}🧹 Cleaning up old backups...${NC}"

# List backups older than retention period
OLD_BACKUPS=$(aws s3 ls s3://${S3_BUCKET}/${S3_PREFIX}/ | grep "game_backup_" | awk '{print $4}' | while read backup; do
    BACKUP_DATE=$(echo $backup | grep -oE '[0-9]{8}' | head -1)
    if [ ! -z "$BACKUP_DATE" ]; then
        BACKUP_EPOCH=$(date -d "${BACKUP_DATE:0:4}-${BACKUP_DATE:4:2}-${BACKUP_DATE:6:2}" +%s 2>/dev/null || echo 0)
        CURRENT_EPOCH=$(date +%s)
        AGE_DAYS=$(( (CURRENT_EPOCH - BACKUP_EPOCH) / 86400 ))
        
        if [ $AGE_DAYS -gt $RETENTION_DAYS ]; then
            echo $backup
        fi
    fi
done)

if [ ! -z "$OLD_BACKUPS" ]; then
    echo "$OLD_BACKUPS" | while read old_backup; do
        echo -e "  Deleting: $old_backup"
        aws s3 rm s3://${S3_BUCKET}/${S3_PREFIX}/$old_backup
        aws s3 rm s3://${S3_BUCKET}/${S3_PREFIX}/${old_backup}.metadata.json 2>/dev/null || true
    done
    echo -e "${GREEN}✅ Old backups cleaned up${NC}"
else
    echo -e "${GREEN}✅ No old backups to clean${NC}"
fi

# Step 8: List recent backups
echo -e "\n${BLUE}📋 Recent S3 Backups:${NC}"
aws s3 ls s3://${S3_BUCKET}/${S3_PREFIX}/ --human-readable | grep "game_backup_" | tail -5

# Step 9: Generate backup report
REPORT_FILE="s3_backup_report_${TIMESTAMP}.txt"
{
    echo "Liap Tui S3 Backup Report"
    echo "========================"
    echo "Timestamp: $(date)"
    echo "Backup Name: ${BACKUP_NAME}"
    echo "S3 Location: s3://${S3_BUCKET}/${S3_PREFIX}/${BACKUP_NAME}"
    echo "Size: ${BACKUP_SIZE}"
    echo "Checksum: ${CHECKSUM}"
    echo "Games Backed Up: ${DB_INFO}"
    echo "Retention: ${RETENTION_DAYS} days"
    echo "Expires: ${EXPIRATION_DATE}"
} > "$REPORT_FILE"

# Step 10: Cleanup local files
rm -f /tmp/liap-tui-backups/${BACKUP_NAME}
rm -f /tmp/liap-tui-backups/${BACKUP_NAME}.metadata.json

echo -e "\n${GREEN}✅ S3 backup completed successfully!${NC}"
echo -e "${GREEN}📄 Report saved to: ${REPORT_FILE}${NC}"

# Optional: Send notification
if [ ! -z "$SNS_TOPIC_ARN" ]; then
    aws sns publish \
        --topic-arn "$SNS_TOPIC_ARN" \
        --subject "Liap Tui Backup Successful" \
        --message "Backup ${BACKUP_NAME} uploaded to S3. Size: ${BACKUP_SIZE}, Games: ${DB_INFO}"
fi

# Create restore instructions
cat > restore_from_s3.sh << EOF
#!/bin/bash
# Restore from S3 backup

# Download backup
aws s3 cp s3://${S3_BUCKET}/${S3_PREFIX}/${BACKUP_NAME} ./

# Restore to EC2
./restore-ec2.sh ${BACKUP_NAME}
EOF

chmod +x restore_from_s3.sh
echo -e "\n${BLUE}💡 To restore this backup:${NC}"
echo -e "   ./restore_from_s3.sh"
echo ""