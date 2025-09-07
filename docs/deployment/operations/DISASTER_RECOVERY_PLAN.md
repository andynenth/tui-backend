# Disaster Recovery Plan for Liap Tui

## Overview

This document outlines the disaster recovery procedures for Liap Tui deployed on AWS EC2. It covers various failure scenarios and provides step-by-step recovery instructions.

## Table of Contents

1. [Critical Information](#critical-information)
2. [Failure Scenarios](#failure-scenarios)
3. [Recovery Procedures](#recovery-procedures)
4. [Preventive Measures](#preventive-measures)
5. [Testing Schedule](#testing-schedule)
6. [Contact Information](#contact-information)

## Critical Information

### Infrastructure Details
- **Instance Type**: t2.micro (or as configured)
- **Region**: us-east-1 (or your region)
- **Availability Zone**: Single AZ deployment
- **Database**: SQLite in `/home/ubuntu/liap-tui-data/`
- **Backups**: `/home/ubuntu/backups/` (7 days retention)

### Recovery Time Objectives (RTO)
- **Minor Issues**: < 15 minutes
- **Container Failure**: < 30 minutes
- **Instance Failure**: < 1 hour
- **Complete Rebuild**: < 2 hours

### Recovery Point Objectives (RPO)
- **Maximum Data Loss**: 24 hours (daily backups)
- **Recommended**: < 1 hour with increased backup frequency

## Failure Scenarios

### 1. Application Crash (Container Failure)

**Symptoms:**
- Game not accessible
- Health check failing
- Container not running

**Severity:** Medium

**Recovery Time:** 5-15 minutes

### 2. EC2 Instance Failure

**Symptoms:**
- Cannot SSH to instance
- Instance status check failing
- Complete service outage

**Severity:** High

**Recovery Time:** 30-60 minutes

### 3. Data Corruption

**Symptoms:**
- Games not loading
- Database errors in logs
- Inconsistent game state

**Severity:** High

**Recovery Time:** 15-30 minutes

### 4. Security Breach

**Symptoms:**
- Unauthorized access detected
- Suspicious activity in logs
- Data tampering evidence

**Severity:** Critical

**Recovery Time:** 1-4 hours

### 5. AWS Region Outage

**Symptoms:**
- Multiple AWS services unavailable
- Cannot access EC2 console
- Regional connectivity issues

**Severity:** Critical

**Recovery Time:** Depends on AWS

## Recovery Procedures

### Scenario 1: Application Crash Recovery

```bash
# 1. Check container status
ssh -i ~/.ssh/your-key.pem ubuntu@your-ec2-ip
docker ps -a

# 2. Check logs for error
docker logs liap-tui-game --tail 100

# 3. Restart container
docker-compose restart

# 4. If restart fails, rebuild
docker-compose down
docker-compose up -d

# 5. Verify recovery
curl http://localhost/api/health
```

### Scenario 2: EC2 Instance Recovery

#### Option A: Reboot Instance
```bash
# From AWS Console or CLI
aws ec2 reboot-instances --instance-ids i-xxxxxxxxxxxxx

# Wait 2-3 minutes, then verify
ssh -i ~/.ssh/your-key.pem ubuntu@your-ec2-ip
```

#### Option B: Launch Replacement Instance

1. **Launch New Instance**
   ```bash
   # Use same configuration as failed instance
   # AMI: Ubuntu 22.04 LTS
   # Type: t2.micro
   # Security Group: Same as original
   ```

2. **Setup New Instance**
   ```bash
   # Copy setup script
   scp -i ~/.ssh/your-key.pem ec2-setup.sh ubuntu@new-ec2-ip:~/

   # Run setup
   ssh -i ~/.ssh/your-key.pem ubuntu@new-ec2-ip
   ./ec2-setup.sh
   ```

3. **Deploy Application**
   ```bash
   # Update deploy script with new IP
   ./deploy-ec2.sh
   ```

4. **Restore Data**
   ```bash
   # Download latest backup from S3 or local
   ./restore-ec2.sh backups/latest_backup.tar.gz
   ```

5. **Update DNS/Load Balancer**
   - Point domain to new Elastic IP
   - Update any hardcoded IPs

### Scenario 3: Data Corruption Recovery

1. **Stop Application**
   ```bash
   ssh -i ~/.ssh/your-key.pem ubuntu@your-ec2-ip
   docker-compose down
   ```

2. **Verify Corruption**
   ```bash
   # Check database integrity
   sqlite3 /home/ubuntu/liap-tui-data/game_events.db "PRAGMA integrity_check;"
   ```

3. **Backup Corrupted Data**
   ```bash
   cp /home/ubuntu/liap-tui-data/game_events.db /home/ubuntu/corrupted_backup_$(date +%Y%m%d).db
   ```

4. **Restore from Backup**
   ```bash
   # Find latest good backup
   ls -la /home/ubuntu/backups/

   # Restore
   rm /home/ubuntu/liap-tui-data/game_events.db
   tar -xzf /home/ubuntu/backups/game_backup_YYYYMMDD_HHMMSS.tar.gz -C /home/ubuntu/liap-tui-data/
   ```

5. **Restart Application**
   ```bash
   docker-compose up -d
   ```

### Scenario 4: Security Breach Recovery

1. **Immediate Actions**
   ```bash
   # Isolate instance (remove from load balancer if applicable)
   # Change security group to block all traffic except your IP

   # Stop application
   ssh -i ~/.ssh/your-key.pem ubuntu@your-ec2-ip
   docker-compose down
   ```

2. **Assess Damage**
   ```bash
   # Check logs for breach timeline
   grep -i "failed\|unauthorized\|error" /var/log/auth.log
   docker logs liap-tui-game > breach_logs.txt

   # Check for modified files
   find /home/ubuntu -type f -mtime -1 -ls
   ```

3. **Secure the System**
   ```bash
   # Change all passwords
   # Rotate SSH keys
   # Update security groups
   # Apply all security updates
   sudo apt update && sudo apt upgrade -y
   ```

4. **Clean Recovery**
   ```bash
   # Launch new instance
   # Deploy fresh application
   # Restore data from pre-breach backup
   # Implement additional security measures
   ```

### Scenario 5: Regional Outage Recovery

1. **Verify AWS Status**
   - Check https://status.aws.amazon.com/
   - Confirm regional outage

2. **Activate DR Region** (if configured)
   ```bash
   # Deploy to backup region
   # Use cross-region backup
   # Update DNS to point to DR region
   ```

3. **Wait for Recovery**
   - Monitor AWS status
   - Prepare for failback

## Preventive Measures

### 1. Automated Backups
```bash
# Increase backup frequency (every 6 hours)
crontab -e
0 */6 * * * /home/ubuntu/backup-game.sh
```

### 2. Multi-Region Backups
```bash
# Sync backups to S3
aws s3 sync /home/ubuntu/backups/ s3://your-backup-bucket/liap-tui/
```

### 3. Monitoring Setup
```bash
# CloudWatch Alarms
- CPU > 80%
- Disk > 85%
- Instance health checks
- Application health endpoint
```

### 4. Security Hardening
```bash
# Run security audit regularly
./security-audit-ec2.sh

# Implement recommendations
# Enable MFA
# Use AWS Systems Manager
```

## Testing Schedule

### Monthly Tests
- [ ] Container restart procedure
- [ ] Backup restoration test
- [ ] Health check verification

### Quarterly Tests
- [ ] Full instance recovery
- [ ] Security breach simulation
- [ ] Performance under load

### Annual Tests
- [ ] Complete DR drill
- [ ] Regional failover (if applicable)
- [ ] Documentation review

## Recovery Scripts

### Quick Recovery Script
```bash
#!/bin/bash
# quick-recovery.sh
echo "Starting quick recovery..."

# Check what's running
docker ps -a

# Restart container
docker-compose restart

# Wait for health
sleep 30

# Verify
if curl -f http://localhost/api/health; then
    echo "Recovery successful!"
else
    echo "Recovery failed - escalate to next procedure"
fi
```

### Data Recovery Script
```bash
#!/bin/bash
# data-recovery.sh
BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

# Stop application
docker-compose down

# Backup current data
mv /home/ubuntu/liap-tui-data/game_events.db /home/ubuntu/game_events.db.corrupted

# Restore from backup
tar -xzf $BACKUP_FILE -C /home/ubuntu/liap-tui-data/

# Start application
docker-compose up -d

echo "Data recovery complete"
```

## Contact Information

### Primary Contacts
- **System Administrator**: [Name] - [Email] - [Phone]
- **Backup Administrator**: [Name] - [Email] - [Phone]
- **AWS Account Owner**: [Name] - [Email] - [Phone]

### Vendor Support
- **AWS Support**: [Support Plan Level]
- **Docker Support**: Community
- **Ubuntu Support**: Community

### Escalation Path
1. On-call Engineer
2. Team Lead
3. Infrastructure Manager
4. CTO/VP Engineering

## Important URLs

- **Application**: http://your-domain.com
- **AWS Console**: https://console.aws.amazon.com/
- **Monitoring Dashboard**: [CloudWatch URL]
- **Documentation**: [GitHub/Wiki URL]

## Recovery Checklist

### Pre-Recovery
- [ ] Identify failure scenario
- [ ] Notify stakeholders
- [ ] Access recovery documentation
- [ ] Gather necessary credentials

### During Recovery
- [ ] Follow specific scenario procedures
- [ ] Document actions taken
- [ ] Communicate progress
- [ ] Test recovery at each step

### Post-Recovery
- [ ] Verify full functionality
- [ ] Document root cause
- [ ] Update procedures if needed
- [ ] Schedule post-mortem meeting

## Appendix

### A. Common Commands
```bash
# Check system health
./monitor-ec2.sh

# Create manual backup
./backup-ec2.sh

# Restore from backup
./restore-ec2.sh backup_file.tar.gz

# View logs
docker logs -f liap-tui-game

# Database check
sqlite3 /home/ubuntu/liap-tui-data/game_events.db "PRAGMA integrity_check;"
```

### B. AWS CLI Commands
```bash
# List instances
aws ec2 describe-instances --filters "Name=tag:Name,Values=liap-tui*"

# Create AMI backup
aws ec2 create-image --instance-id i-xxxxx --name "liap-tui-backup-$(date +%Y%m%d)"

# List snapshots
aws ec2 describe-snapshots --owner-ids self
```

### C. Recovery Time Tracking
| Scenario | Target RTO | Actual RTO | Date | Notes |
|----------|------------|------------|------|-------|
| Container Crash | 15 min | - | - | - |
| Instance Failure | 60 min | - | - | - |
| Data Corruption | 30 min | - | - | - |

---

**Document Version**: 1.0
**Last Updated**: 2024-01-14
**Review Schedule**: Quarterly
