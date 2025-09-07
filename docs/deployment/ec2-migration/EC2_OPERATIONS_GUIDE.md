# EC2 Operations Guide for Liap Tui

This guide covers day-to-day operations, monitoring, and maintenance for Liap Tui deployed on AWS EC2.

## Table of Contents

1. [Quick Reference](#quick-reference)
2. [Daily Operations](#daily-operations)
3. [Monitoring](#monitoring)
4. [Backup & Recovery](#backup--recovery)
5. [Performance Tuning](#performance-tuning)
6. [Security](#security)
7. [Troubleshooting](#troubleshooting)
8. [Emergency Procedures](#emergency-procedures)

## Quick Reference

### Essential Commands

```bash
# Check status
./monitor-ec2.sh

# View logs
ssh -i ~/.ssh/your-key.pem ubuntu@your-ec2-ip
docker logs -f liap-tui-game

# Restart container
docker-compose restart

# Create backup
./backup-game.sh

# Deploy update
./deploy-ec2.sh
```

### Key Locations on EC2

- **Application**: `/home/ubuntu/docker-compose.yml`
- **Database**: `/home/ubuntu/liap-tui-data/game_events.db`
- **Backups**: `/home/ubuntu/backups/`
- **Logs**: `/home/ubuntu/logs/`
- **Scripts**: `/home/ubuntu/*.sh`

## Daily Operations

### Morning Checks

1. **System Health**
   ```bash
   ./monitor-ec2.sh
   ```
   - Verify container is running
   - Check API health endpoint
   - Review resource usage

2. **Backup Verification**
   ```bash
   ssh -i ~/.ssh/your-key.pem ubuntu@your-ec2-ip
   ls -la /home/ubuntu/backups/
   ```
   - Confirm nightly backup completed
   - Check backup file size

3. **Log Review**
   ```bash
   # Recent errors
   docker logs liap-tui-game 2>&1 | grep ERROR | tail -20

   # Health check failures
   tail -20 /home/ubuntu/logs/health-check.log | grep "❌"
   ```

### Routine Maintenance

#### Weekly Tasks

1. **Backup Download**
   ```bash
   ./backup-ec2.sh
   ```
   - Download latest backup to local
   - Verify backup integrity

2. **Disk Space Check**
   ```bash
   ./maintain-ec2.sh
   # Select option 9 (Check disk usage)
   ```
   - Clean up if >80% full
   - Remove old Docker images

3. **Security Updates**
   ```bash
   ssh -i ~/.ssh/your-key.pem ubuntu@your-ec2-ip
   sudo apt update
   sudo apt list --upgradable
   ```

#### Monthly Tasks

1. **Full System Backup**
   - Download all backups
   - Test restore procedure
   - Archive to S3 or external storage

2. **Performance Review**
   - Analyze game statistics
   - Check response times
   - Review resource trends

3. **Security Audit**
   - Review access logs
   - Check for unusual activity
   - Update security groups if needed

## Monitoring

### Using monitor-ec2.sh

The monitoring script provides comprehensive system status:

```bash
# Set environment variable for easy use
export EC2_HOST=your-ec2-ip
export KEY_PATH=~/.ssh/your-key.pem

# Run monitoring
./monitor-ec2.sh
```

### Key Metrics to Watch

1. **System Resources**
   - CPU Usage: Should stay <70%
   - Memory: Should stay <80%
   - Disk: Alert at >80%

2. **Application Health**
   - API Response: Should be <500ms
   - Active Connections: Monitor for spikes
   - Container Uptime: Should be stable

3. **Database Growth**
   - Size increase rate
   - Number of games per day
   - Backup size trends

### Setting Up Alerts

#### CloudWatch Alarms

```bash
# CPU Alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "liap-tui-high-cpu" \
  --alarm-description "Alert when CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
```

#### Custom Health Check

Add to crontab:
```bash
*/5 * * * * /home/ubuntu/health-check.sh
```

## Backup & Recovery

### Backup Strategy

1. **Automated Daily Backups**
   - Run at 2 AM via cron
   - Keep last 7 days locally
   - Monthly archives to S3

2. **Manual Backups**
   ```bash
   # Before major changes
   ./maintain-ec2.sh
   # Select option 4 (Create manual backup)
   ```

3. **Backup Verification**
   ```bash
   # Test restore locally
   ./test-persistence.sh
   ```

### Recovery Procedures

#### Data Recovery

1. **From Recent Backup**
   ```bash
   ./restore-ec2.sh backups/game_backup_20240114_020000.tar.gz
   ```

2. **Point-in-Time Recovery**
   - Stop container
   - Replace database file
   - Restart container

#### Full System Recovery

1. **Launch New EC2**
   - Use same AMI and configuration
   - Run `ec2-setup.sh`

2. **Restore Data**
   ```bash
   ./deploy-ec2.sh
   ./restore-ec2.sh latest_backup.tar.gz
   ```

3. **Update DNS**
   - Point to new Elastic IP
   - Update ALLOWED_ORIGINS

## Performance Tuning

### Container Optimization

1. **Resource Limits**
   ```yaml
   # In docker-compose.yml
   services:
     liap-tui:
       deploy:
         resources:
           limits:
             cpus: '1.5'
             memory: 1G
           reservations:
             cpus: '0.5'
             memory: 512M
   ```

2. **Application Tuning**
   ```bash
   # Environment variables
   WORKERS=2  # Increase if CPU allows
   MAX_CONNECTIONS=200
   ```

### Database Optimization

1. **Regular Maintenance**
   ```bash
   # Vacuum database monthly
   docker exec liap-tui-game sqlite3 /app/data/game_events.db "VACUUM;"
   ```

2. **Index Optimization**
   ```sql
   -- Add indexes for common queries
   CREATE INDEX idx_room_started ON game_summaries(room_id, started_at);
   ```

### Network Optimization

1. **Enable Compression**
   - Configure in nginx if using reverse proxy
   - Reduces bandwidth usage

2. **CDN for Static Assets**
   - Use CloudFront for global users
   - Cache static files

## Security

### Access Control

1. **SSH Key Management**
   - Rotate keys quarterly
   - Use different keys for different environments
   - Never share private keys

2. **Security Groups**
   ```bash
   # Review current rules
   aws ec2 describe-security-groups --group-ids sg-xxxxxx
   ```

3. **Application Security**
   - Keep dependencies updated
   - Monitor for CVEs
   - Use environment variables for secrets

### Monitoring Security

1. **Access Logs**
   ```bash
   # Check for unusual access patterns
   sudo tail -f /var/log/auth.log
   ```

2. **Failed Logins**
   ```bash
   # Monitor SSH attempts
   sudo grep "Failed password" /var/log/auth.log | tail -20
   ```

3. **Network Traffic**
   ```bash
   # Check active connections
   sudo netstat -tulpn | grep ESTABLISHED
   ```

## Troubleshooting

### Common Issues

#### Container Won't Start

```bash
# Check logs
docker logs liap-tui-game

# Check disk space
df -h

# Check permissions
ls -la /home/ubuntu/liap-tui-data/

# Try manual start
docker-compose up
```

#### High Memory Usage

```bash
# Check for memory leaks
docker stats liap-tui-game

# Restart container
docker-compose restart

# Check for zombie rooms
curl http://localhost/api/system/stats
```

#### Database Corruption

```bash
# Check database integrity
docker exec liap-tui-game sqlite3 /app/data/game_events.db "PRAGMA integrity_check;"

# Restore from backup if needed
./restore-ec2.sh last_known_good_backup.tar.gz
```

### Debug Mode

1. **Enable Debug Logging**
   ```yaml
   environment:
     - DEBUG=true
     - LOG_LEVEL=DEBUG
   ```

2. **Interactive Container Access**
   ```bash
   docker exec -it liap-tui-game bash
   ```

3. **Database Queries**
   ```bash
   docker exec -it liap-tui-game sqlite3 /app/data/game_events.db
   ```

## Emergency Procedures

### Container Crash Loop

1. **Stop Container**
   ```bash
   docker-compose down
   ```

2. **Check Logs**
   ```bash
   docker logs liap-tui-game > crash.log
   tail -100 crash.log
   ```

3. **Emergency Rebuild**
   ```bash
   ./maintain-ec2.sh
   # Select option 15 (Emergency rebuild)
   ```

### Data Loss

1. **Stop All Operations**
   ```bash
   docker-compose down
   ```

2. **Assess Damage**
   ```bash
   ls -la /home/ubuntu/liap-tui-data/
   file /home/ubuntu/liap-tui-data/game_events.db
   ```

3. **Restore from Backup**
   ```bash
   # Find latest backup
   ls -t /home/ubuntu/backups/ | head -5

   # Restore
   ./restore-ec2.sh /home/ubuntu/backups/[latest_backup]
   ```

### EC2 Instance Failure

1. **Launch Replacement**
   - Use same AMI
   - Same instance type
   - Same security group

2. **Quick Setup**
   ```bash
   # On new instance
   ./ec2-setup.sh
   ```

3. **Restore Service**
   ```bash
   # Deploy application
   ./deploy-ec2.sh

   # Restore data
   ./restore-ec2.sh latest_backup.tar.gz
   ```

### Rollback Procedure

1. **Identify Last Good State**
   ```bash
   # Check Docker images
   docker images | grep liap-tui
   ```

2. **Rollback Container**
   ```bash
   # Tag current as backup
   docker tag liap-tui:latest liap-tui:backup

   # Use previous version
   docker tag liap-tui:v1.0.0 liap-tui:latest
   docker-compose up -d
   ```

## Best Practices

1. **Always Backup Before Changes**
   - Manual backup before deployments
   - Verify backup completed

2. **Test in Staging First**
   - Use docker-compose.test.yml locally
   - Verify changes work

3. **Monitor After Changes**
   - Watch logs for 30 minutes
   - Check performance metrics

4. **Document Everything**
   - Keep deployment log
   - Note any issues and resolutions

5. **Regular Maintenance**
   - Don't skip weekly tasks
   - Address issues promptly

## Support Contacts

- **AWS Support**: Via AWS Console
- **Application Issues**: Check GitHub Issues
- **Emergency**: Have backup admin contact

---

Remember: When in doubt, create a backup first!