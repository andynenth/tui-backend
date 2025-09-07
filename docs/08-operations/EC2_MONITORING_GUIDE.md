# EC2 Monitoring & Maintenance Guide

**📍 Note**: For comprehensive monitoring documentation, see [Comprehensive Monitoring & Observability Guide](./MONITORING_COMPREHENSIVE.md), particularly the "EC2 Deployment Monitoring" section.

This guide explains how to monitor and maintain your Liap Tui EC2 server using the provided shell scripts.

## Quick Start

Your EC2 server details:
- **IP Address**: 54.250.35.226 (Tokyo region)
- **SSH Key**: `~/.ssh/liap-tui-tokyo-key.pem`
- **User**: ubuntu

## Available Scripts

### 1. `monitor-ec2.sh` - Health Monitoring

**Purpose**: Quick health check of your EC2 server

**Usage**:
```bash
./monitor-ec2.sh
```

**What it checks**:
- ✅ SSH connectivity
- ✅ CPU, memory, and disk usage
- ✅ Docker container status
- ✅ API health endpoint
- ✅ Database size and activity
- ✅ Backup status

**Key metrics to watch**:
- **Disk Usage**: Alert if >80% (Currently: 13%)
- **Container Status**: Should be "Up" and "healthy"
- **API Health**: Should return HTTP 200 OK

### 2. `maintain-ec2.sh` - Interactive Maintenance

**Purpose**: Perform maintenance tasks through an interactive menu

**Usage**:
```bash
./maintain-ec2.sh
```

**Menu Options**:
1. **View container status** - Check if game is running
2. **Restart game container** - If game is unresponsive
3. **View recent logs** - Debug issues
4. **Create manual backup** - Before updates or weekly
5. **Download latest backup** - Save to local machine
6. **Clean up old backups** - Free disk space
7. **Update container** - Deploy new version
8. **View database statistics** - Game activity
9. **Check disk usage** - Monitor storage
10. **Restart Docker service** - Last resort fix
11. **View active game rooms** - Current players
12. **Clean up old games** - Archive old data
13. **Export game statistics** - Usage reports
14. **View system resources** - CPU/Memory details
15. **Emergency container rebuild** - Critical repairs

**Common workflows**:

#### Weekly Maintenance:
```bash
./maintain-ec2.sh
# Choose 9 - Check disk usage
# Choose 4 - Create backup
# Choose 5 - Download backup
```

#### Troubleshooting:
```bash
./maintain-ec2.sh
# Choose 3 - View logs
# Choose 1 - Check container status
# Choose 2 - Restart if needed
```

### 3. `backup-game-ec2.sh` - Automated Backup

**Purpose**: Create and download game database backup

**Usage**:
```bash
./backup-game-ec2.sh
```

**What it does**:
1. Connects to EC2 via SSH
2. Creates compressed backup of `game_events.db`
3. Downloads backup to `./backups/` directory
4. Creates restore script
5. Cleans up old backups (keeps last 7)

**Backup naming**: `game_backup_YYYYMMDD_HHMMSS.tar.gz`

**To restore a backup**:
```bash
./restore-backup.sh backups/game_backup_20250906_141231.tar.gz
```

## Monitoring Workflow

### Daily Quick Check
```bash
# Run monitoring script
./monitor-ec2.sh

# Look for:
# - Disk usage <80%
# - Container status "healthy"
# - API health "OK"
```

### Weekly Maintenance
```bash
# 1. Check server health
./monitor-ec2.sh

# 2. Create and download backup
./backup-game-ec2.sh

# 3. Check disk usage and clean if needed
./maintain-ec2.sh
# Choose option 9 (disk usage)
# Choose option 6 (clean old backups) if needed
```

### Monthly Tasks
```bash
# 1. Download all recent backups
./maintain-ec2.sh
# Choose option 5

# 2. Export game statistics
./maintain-ec2.sh
# Choose option 13

# 3. Review and archive old backups locally
ls -la backups/
```

## Important Metrics

### Critical Thresholds
- **Disk Space**: Take action if >80% used
- **Memory**: Normal if <50% used
- **CPU**: Spikes are OK, sustained >80% needs investigation
- **Container Uptime**: Investigate if restarting frequently

### Current Status (as of last test)
- ✅ Disk: 13% used (3.7GB of 29GB)
- ✅ Memory: 9.4% used (363MB of 3.8GB)
- ✅ CPU: 6.2% average
- ✅ Container: Up 2 days, healthy
- ✅ Version: 1.5.14

## Troubleshooting

### Container Won't Start
```bash
./maintain-ec2.sh
# Choose 3 - View logs
# Choose 15 - Emergency rebuild (last resort)
```

### High Disk Usage
```bash
./maintain-ec2.sh
# Choose 9 - Check what's using space
# Choose 6 - Clean old backups
# Choose 12 - Clean old game data
```

### API Not Responding
```bash
./monitor-ec2.sh  # Check health status
./maintain-ec2.sh
# Choose 2 - Restart container
# Choose 3 - Check logs for errors
```

### Can't Connect via SSH
1. Check your internet connection
2. Verify key file exists: `ls -la ~/.ssh/liap-tui-tokyo-key.pem`
3. Check key permissions: `chmod 400 ~/.ssh/liap-tui-tokyo-key.pem`
4. Test direct SSH: `ssh -i ~/.ssh/liap-tui-tokyo-key.pem ubuntu@54.250.35.226`

## Best Practices

1. **Regular Monitoring**: Check health at least weekly
2. **Backup Schedule**: Weekly backups, monthly archives
3. **Disk Management**: Keep usage below 70%
4. **Update Planning**: Test updates locally first
5. **Emergency Contacts**: Keep AWS console access handy

## Script Customization

To use different servers, set environment variables:
```bash
export EC2_HOST="your-server-ip"
export KEY_PATH="/path/to/your/key.pem"
./monitor-ec2.sh
```

## Notes

- All scripts use SSH to connect remotely
- No deployment needed for monitoring
- Logs are saved locally, not on EC2
- Scripts have color-coded output:
  - 🟢 Green = Success
  - 🟡 Yellow = Warning/Info
  - 🔴 Red = Error
  - 🔵 Blue = Headers

## Emergency Procedures

If the server is down:
1. Try `./monitor-ec2.sh` to diagnose
2. Check AWS Console for instance status
3. Use `./maintain-ec2.sh` option 2 to restart container
4. If still down, check AWS billing (free tier limits)
5. Last resort: `./maintain-ec2.sh` option 15 for rebuild

---

Remember: Your Tokyo server (54.250.35.226) is already configured in all scripts!
