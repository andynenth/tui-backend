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
