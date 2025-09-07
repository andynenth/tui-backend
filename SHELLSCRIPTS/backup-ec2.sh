#!/bin/bash
# Backup game database from EC2

EC2_HOST="${EC2_HOST:-34.233.7.20}"
EC2_USER="${EC2_USER:-ubuntu}"
KEY_PATH="${KEY_PATH:-./liap-tui-key-1755152170.pem}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create local backup directory
mkdir -p backups

# Create backup on EC2
ssh -i ${KEY_PATH} ${EC2_USER}@${EC2_HOST} << ENDSSH
  cd ~
  docker run --rm \
    -v liap-tui-game_game_data:/data \
    -v \$(pwd):/backup \
    alpine tar czf /backup/game_backup_${TIMESTAMP}.tar.gz -C /data .
ENDSSH

# Download backup
scp -i ${KEY_PATH} ${EC2_USER}@${EC2_HOST}:~/game_backup_${TIMESTAMP}.tar.gz ./backups/

# Cleanup remote backup
ssh -i ${KEY_PATH} ${EC2_USER}@${EC2_HOST} "rm ~/game_backup_${TIMESTAMP}.tar.gz"

echo "✅ Backup saved to: backups/game_backup_${TIMESTAMP}.tar.gz"
