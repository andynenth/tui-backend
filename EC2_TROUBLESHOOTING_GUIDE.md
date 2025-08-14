# EC2 Troubleshooting Guide

Quick solutions to common problems with your Liap Tui EC2 deployment.

## 🚨 Emergency Contacts
- **EC2 IP**: 34.233.7.20
- **Instance ID**: i-031f0be2cfed1ff2f
- **AWS Console**: https://console.aws.amazon.com/ec2/

## ❌ Problem: Can't Access Game in Browser

### Check 1: Is the container running?
```bash
ssh -i liap-tui-key-1755152170.pem ubuntu@34.233.7.20 "docker ps"
```

**If not running**, start it:
```bash
ssh -i liap-tui-key-1755152170.pem ubuntu@34.233.7.20 "docker start liap-tui-game"
```

### Check 2: View error logs
```bash
ssh -i liap-tui-key-1755152170.pem ubuntu@34.233.7.20 "docker logs liap-tui-game --tail 100"
```

### Check 3: Test health endpoint
```bash
curl http://34.233.7.20/api/health
```

## ❌ Problem: SSH Connection Failed

### Error: "Permission denied (publickey)"
```bash
# Fix key permissions
chmod 400 liap-tui-key-1755152170.pem

# Make sure you're using the right key
ssh -i ./liap-tui-key-1755152170.pem ubuntu@34.233.7.20
```

### Error: "Connection timeout"
- Check if EC2 instance is running in AWS Console
- Check Security Group allows SSH from your IP
- Try: `aws ec2 describe-instances --instance-ids i-031f0be2cfed1ff2f`

## ❌ Problem: Deploy Script Fails

### Error during docker build
```bash
# Clean Docker cache and try again
docker system prune -a
docker build -f Dockerfile.prod -t liap-tui:latest .
```

### Error during upload
```bash
# Check file size
ls -lh liap-tui-latest.tar.gz

# If too large, check internet connection
# Try manual upload with resume capability:
rsync -avz -e "ssh -i liap-tui-key-1755152170.pem" \
  liap-tui-latest.tar.gz ubuntu@34.233.7.20:~/
```

## ❌ Problem: Container Keeps Restarting

### Check what's wrong:
```bash
# View detailed logs
ssh -i liap-tui-key-1755152170.pem ubuntu@34.233.7.20 "docker logs liap-tui-game --tail 200"

# Check container status
ssh -i liap-tui-key-1755152170.pem ubuntu@34.233.7.20 "docker inspect liap-tui-game | grep -A 10 State"
```

### Common fixes:
```bash
# Remove and recreate container
ssh -i liap-tui-key-1755152170.pem ubuntu@34.233.7.20 << 'REMOTE'
docker stop liap-tui-game
docker rm liap-tui-game
docker run -d \
  --name liap-tui-game \
  -p 80:5050 \
  -v /home/ubuntu/liap-tui-data:/app/data \
  -e DATABASE_PATH=/app/data/game_events.db \
  -e ALLOWED_ORIGINS="http://localhost,http://34.233.7.20" \
  --restart unless-stopped \
  liap-tui:latest
REMOTE
```

## ❌ Problem: Out of Disk Space

### Check disk usage:
```bash
ssh -i liap-tui-key-1755152170.pem ubuntu@34.233.7.20 "df -h"
```

### Clean up:
```bash
ssh -i liap-tui-key-1755152170.pem ubuntu@34.233.7.20 << 'REMOTE'
# Remove old Docker images
docker image prune -a -f

# Remove old backups (keep last 5)
cd /home/ubuntu/backups
ls -t game_backup_*.tar.gz 2>/dev/null | tail -n +6 | xargs rm -f

# Clear logs
docker logs liap-tui-game > /home/ubuntu/logs/game.log
echo "" > $(docker inspect --format='{{.LogPath}}' liap-tui-game)
REMOTE
```

## ❌ Problem: High AWS Bill

### Check what's costing money:
```bash
./monitor-aws-costs.sh
```

### Common causes:
1. **Unattached Elastic IP** - Always keep it attached
2. **Old snapshots** - Delete unused EBS snapshots
3. **Multiple instances** - Check for forgotten instances
4. **Exceeded Free Tier** - Monitor usage

### Fix high costs:
```bash
# List all resources
aws ec2 describe-instances --query 'Reservations[*].Instances[*].[InstanceId,State.Name,InstanceType]' --output table
aws ec2 describe-addresses --query 'Addresses[?AssociationId==null]'
aws ec2 describe-snapshots --owner-ids self
```

## ❌ Problem: Database Issues

### Backup current database:
```bash
./backup-game-ec2.sh
```

### Check database:
```bash
ssh -i liap-tui-key-1755152170.pem ubuntu@34.233.7.20 << 'REMOTE'
# Check if database exists
ls -la /home/ubuntu/liap-tui-data/

# Check database size
du -h /home/ubuntu/liap-tui-data/game_events.db

# Test database access
docker exec liap-tui-game sqlite3 /app/data/game_events.db ".tables"
REMOTE
```

## ❌ Problem: Can't Find Files

### Important file locations:

**Local (your computer):**
```
/Users/nrw/python/tui-project/liap-tui/
├── liap-tui-key-1755152170.pem     # SSH key
├── deploy-ec2.sh                    # Deploy script
├── backup-game-ec2.sh               # Backup script
├── monitor-ec2.sh                   # Monitor script
└── docker-compose.prod.yml          # Docker config
```

**Remote (EC2 server):**
```
/home/ubuntu/
├── docker-compose.yml               # Docker config
├── liap-tui-data/                  # Database directory
│   └── game_events.db              # Game database
├── backups/                        # Backup directory
└── logs/                           # Log directory
```

## 🔧 Quick Fix Commands

```bash
# Restart everything
ssh -i liap-tui-key-1755152170.pem ubuntu@34.233.7.20 "docker restart liap-tui-game"

# Force rebuild and deploy
docker build -f Dockerfile.prod -t liap-tui:latest . --no-cache
./deploy-ec2.sh

# Emergency backup
./backup-game-ec2.sh

# Check everything
./quick-monitor.sh
```

## 🆘 Still Stuck?

1. **Save the error message** - Copy the full error
2. **Check AWS Console** - Make sure instance is running
3. **Try manual steps** - Sometimes automation fails
4. **Restart from scratch** - Use EC2_SETUP_FROM_SCRATCH_GUIDE.md

Remember: Your game data is safe in `/home/ubuntu/liap-tui-data/` and backed up daily!