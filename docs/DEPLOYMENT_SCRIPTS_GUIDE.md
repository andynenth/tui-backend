# Deployment Scripts Guide

This guide provides detailed documentation for all deployment, monitoring, and maintenance scripts used in the Liap Tui project.

## Table of Contents

1. [Deployment Scripts](#deployment-scripts)
2. [Monitoring Scripts](#monitoring-scripts)
3. [Backup & Recovery Scripts](#backup--recovery-scripts)
4. [Maintenance Scripts](#maintenance-scripts)
5. [Billing & Cost Management](#billing--cost-management)
6. [Testing & Validation](#testing--validation)
7. [Emergency & Cleanup](#emergency--cleanup)
8. [Quick Reference](#quick-reference)

---

## Deployment Scripts

### deploy-ec2.sh
**Purpose**: Main deployment script for updating the game on EC2

**Usage**:
```bash
./deploy-ec2.sh
```

**What it does**:
1. Builds production Docker image locally
2. Compresses image as tarball
3. Transfers to EC2 via SCP
4. Deploys with zero-downtime using Docker Compose
5. Cleans up temporary files

**Prerequisites**:
- SSH key file: `liap-tui-key-1755152170.pem` with 400 permissions
- Docker running locally
- EC2 instance accessible at 34.233.7.20

**Time**: ~2-5 minutes

---

### version-and-deploy.sh
**Purpose**: Deploy with automatic version tagging and release notes

**Usage**:
```bash
./version-and-deploy.sh [major|minor|patch]
```

**Example**:
```bash
./version-and-deploy.sh minor  # Bumps 1.4.2 -> 1.5.0
./version-and-deploy.sh patch  # Bumps 1.4.2 -> 1.4.3
```

**What it does**:
1. Updates version in `frontend/package.json` using npm
2. Runs the standard deployment process

**Version System Architecture**:
The application uses a multi-layered version detection system for reliability:

1. **Frontend (Build Time)**:
   - Version from `package.json` is injected via esbuild as `__APP_VERSION__`
   - Build process creates a `VERSION` file with the current version
   - Version displays on start page via `VersionDisplay` component

2. **Backend (Runtime)** - checks in priority order:
   - `APP_VERSION` environment variable (highest priority)
   - `/app/VERSION` file (created during build)
   - `/app/frontend-package.json` (copied during Docker build)
   - `frontend/package.json` (development fallback)
   - Default: '1.0.0'

3. **Version Verification**:
   - `deploy-ec2.sh` automatically verifies version after deployment
   - Compares local `package.json` with deployed API `/api/health`
   - Shows warning if versions don't match

4. **Manual Version Override**:
   ```bash
   # Via environment variable in docker-compose.prod.yml
   APP_VERSION=1.5.0 docker-compose up -d
   ```

**Benefits**:
- Automatic version synchronization between frontend and backend
- Multiple fallbacks ensure version is always available
- Deployment verification catches version mismatches
- Version visible in both UI and API health endpoint

---

### deploy-to-aws.sh
**Purpose**: Legacy AWS deployment script (may use older infrastructure)

**Usage**:
```bash
./deploy-to-aws.sh [environment]
```

**Note**: Check if this uses ECS or older infrastructure. Consider using `deploy-ec2.sh` instead.

---

### launch-ec2-instance.sh
**Purpose**: Create a new EC2 instance from scratch

**Usage**:
```bash
./launch-ec2-instance.sh
```

**What it does**:
1. Launches t2.micro instance (free tier eligible)
2. Configures security groups
3. Assigns Elastic IP
4. Sets up initial SSH access
5. Installs Docker and Docker Compose

**When to use**:
- Setting up new environment
- Disaster recovery
- Creating staging instance

**Output**: Instance ID, public IP, and connection instructions

---

### ec2-setup.sh
**Purpose**: Configure a fresh EC2 instance for Liap Tui

**Usage**:
```bash
# Run on EC2 instance after SSH
./ec2-setup.sh
```

**What it does**:
1. Updates system packages
2. Installs Docker and Docker Compose
3. Sets up application directories
4. Configures firewall rules
5. Creates systemd service for auto-start
6. Sets up log rotation

**Prerequisites**: Must be run on EC2 instance with sudo access

---

## Monitoring Scripts

### monitor-ec2.sh
**Purpose**: Real-time monitoring of EC2 instance and application

**Usage**:
```bash
./monitor-ec2.sh [--continuous]
```

**Displays**:
- CPU and memory usage
- Active game rooms and connections
- WebSocket latency
- Docker container status
- Disk usage
- Recent errors from logs

**Options**:
- `--continuous`: Updates every 30 seconds
- `--json`: Output in JSON format

---

### auto-monitor.sh
**Purpose**: Automated monitoring with alerts

**Usage**:
```bash
./auto-monitor.sh start|stop|status
```

**Features**:
- Runs monitoring in background
- Sends alerts for:
  - High CPU/memory (>80%)
  - Low disk space (<10%)
  - Container failures
  - High error rates
- Logs to `/var/log/liap-tui-monitor.log`

**Configuration**: Edit script for email/Slack webhooks

---

### quick-monitor.sh
**Purpose**: Quick health check snapshot

**Usage**:
```bash
./quick-monitor.sh
```

**Output**:
```
✅ API Health: OK
✅ WebSocket: 23 connections
✅ Active Games: 5
✅ CPU: 12%
✅ Memory: 45%
✅ Disk: 72% free
```

**Use case**: Quick status check before deployments

---

### monitor-aws-costs.sh
**Purpose**: Track AWS spending and free tier usage

**Usage**:
```bash
./monitor-aws-costs.sh [--month YYYY-MM]
```

**Shows**:
- Current month costs
- Free tier usage remaining
- Cost breakdown by service
- Projected monthly cost
- Alerts for unexpected charges

**Example output**:
```
Current Month: $0.00
Free Tier Usage:
  - EC2: 423/750 hours used
  - EBS: 8/30 GB used
  - Data Transfer: 2/15 GB used
Status: ✅ Within free tier
```

---

## Backup & Recovery Scripts

### backup-ec2.sh
**Purpose**: Complete EC2 instance backup

**Usage**:
```bash
./backup-ec2.sh [--full|--incremental]
```

**What it backs up**:
- EBS volume snapshot
- Application configuration
- Docker images
- SQLite database
- Nginx configuration

**Storage**: Amazon S3 with lifecycle policies

**Schedule**: Set up cron for daily backups:
```bash
0 2 * * * /home/ubuntu/backup-ec2.sh --incremental
```

---

### backup-game-ec2.sh
**Purpose**: Backup only game data (faster)

**Usage**:
```bash
./backup-game-ec2.sh
```

**Backs up**:
- SQLite database
- Game event logs
- Player statistics

**Use case**: Before major updates or maintenance

---

### restore-backup.sh
**Purpose**: Restore from backup

**Usage**:
```bash
./restore-backup.sh <backup-id> [--dry-run]
```

**Example**:
```bash
# List available backups
./restore-backup.sh --list

# Restore specific backup
./restore-backup.sh backup-20240115-0200

# Test restore without applying
./restore-backup.sh backup-20240115-0200 --dry-run
```

**Options**:
- `--dry-run`: Show what would be restored
- `--data-only`: Restore only database
- `--config-only`: Restore only configuration

---

### restore-ec2.sh
**Purpose**: Complete EC2 disaster recovery

**Usage**:
```bash
./restore-ec2.sh <snapshot-id>
```

**Process**:
1. Creates new EC2 instance from snapshot
2. Restores all configurations
3. Updates DNS/Elastic IP
4. Validates application health

**Time**: ~10-15 minutes

---

### rollback.sh
**Purpose**: Quick rollback to previous version

**Usage**:
```bash
# Rollback to previous version
./rollback.sh

# Rollback to specific version
./rollback.sh v1.2.3
```

**How it works**:
- Keeps last 5 Docker images on EC2
- Switches container to previous version
- Preserves database (no data loss)
- Updates version tracking

**Time**: <1 minute

---

## Maintenance Scripts

### maintain-ec2.sh
**Purpose**: Routine maintenance tasks

**Usage**:
```bash
./maintain-ec2.sh [--auto-confirm]
```

**Tasks performed**:
1. Clean Docker unused images/containers
2. Rotate logs
3. Update system packages
4. Optimize SQLite database (VACUUM)
5. Clear temporary files
6. Update security patches

**Schedule**: Run weekly during low-traffic hours

---

### phase2-checklist.sh
**Purpose**: Validate production readiness

**Usage**:
```bash
./phase2-checklist.sh
```

**Checks**:
- [ ] SSL certificate valid
- [ ] Backups configured
- [ ] Monitoring active
- [ ] Security groups correct
- [ ] Auto-scaling ready
- [ ] Disaster recovery tested
- [ ] Performance benchmarks met

**Output**: Checklist with pass/fail status

---

## Billing & Cost Management

### setup-billing-alerts.sh
**Purpose**: Configure AWS billing alerts

**Usage**:
```bash
./setup-billing-alerts.sh
```

**Sets up alerts for**:
- Monthly budget exceeded ($10 default)
- Daily spend spike (>$1)
- Free tier limit approaching (80%)
- Unexpected service charges

---

### setup-billing-alerts-interactive.sh
**Purpose**: Interactive billing alert configuration

**Usage**:
```bash
./setup-billing-alerts-interactive.sh
```

**Prompts for**:
- Email for alerts
- Monthly budget limit
- Services to monitor
- Alert thresholds

---

### setup-billing-alerts-auto.sh
**Purpose**: Automated billing alert setup with defaults

**Usage**:
```bash
./setup-billing-alerts-auto.sh <email>
```

**Default settings**:
- $10/month budget
- 80% warning threshold
- Daily cost anomaly detection
- All services monitored

---

### aws-free-tier-check.sh
**Purpose**: Check free tier usage and limits

**Usage**:
```bash
./aws-free-tier-check.sh
```

**Shows**:
- Current usage vs limits
- Days remaining in free tier
- Services approaching limits
- Recommendations to stay free

**Example output**:
```
EC2 t2.micro: 423/750 hours (56%)
EBS Storage: 8.2/30 GB (27%)
Data Transfer: 2.1/15 GB (14%)
Free Tier Expires: 245 days
Status: ✅ Safe
```

---

## Testing & Validation

### test-persistence.sh
**Purpose**: Verify data persistence across deployments

**Usage**:
```bash
./test-persistence.sh
```

**Tests**:
1. Creates test game room
2. Simulates gameplay
3. Deploys new version
4. Verifies data intact
5. Checks WebSocket reconnection
6. Validates game state

**Success criteria**: All game data preserved after deployment

---

## Emergency & Cleanup

### emergency_cleanup.sh
**Purpose**: Emergency resource cleanup to prevent charges

**Usage**:
```bash
./emergency_cleanup.sh [--confirm]
```

**Actions**:
- Stops all EC2 instances
- Deletes unattached EBS volumes
- Removes old snapshots
- Clears S3 buckets (with confirm)
- Releases Elastic IPs

**WARNING**: Destructive operation - use only in emergencies

**Safety**: Requires `--confirm` flag and additional prompt

---

### connect-to-ec2.sh
**Purpose**: Quick SSH connection to EC2

**Usage**:
```bash
./connect-to-ec2.sh
```

**Features**:
- Auto-finds instance IP
- Sets correct SSH parameters
- Forwards useful ports
- Opens in new terminal tab

**Custom commands**:
```bash
# Connect and tail logs
./connect-to-ec2.sh --logs

# Connect and enter Docker container
./connect-to-ec2.sh --docker
```

---

## Quick Reference

### Daily Operations

| Task | Script | Time |
|------|--------|------|
| Deploy update | `./deploy-ec2.sh` | 2-5 min |
| Quick health check | `./quick-monitor.sh` | 5 sec |
| View costs | `./monitor-aws-costs.sh` | 10 sec |
| Connect to server | `./connect-to-ec2.sh` | 5 sec |

### Weekly Maintenance

| Task | Script | Schedule |
|------|--------|----------|
| Full backup | `./backup-ec2.sh --full` | Sunday 2 AM |
| Maintenance | `./maintain-ec2.sh` | Sunday 3 AM |
| Cost review | `./monitor-aws-costs.sh` | Monday morning |

### Emergency Procedures

| Situation | Script | Action |
|-----------|--------|--------|
| High costs | `./emergency_cleanup.sh` | Stop unnecessary resources |
| Server down | `./restore-ec2.sh` | Restore from snapshot |
| Bad deploy | `./rollback.sh` | Revert to previous version |
| Data corruption | `./restore-backup.sh` | Restore database only |

### Best Practices

1. **Before Deployment**:
   ```bash
   ./quick-monitor.sh  # Check health
   ./backup-game-ec2.sh  # Backup data
   ./deploy-ec2.sh  # Deploy
   ./test-persistence.sh  # Verify
   ```

2. **Cost Management**:
   ```bash
   # Weekly cost check
   ./monitor-aws-costs.sh
   ./aws-free-tier-check.sh
   ```

3. **Monitoring Setup**:
   ```bash
   # One-time setup
   ./setup-billing-alerts-auto.sh your-email@example.com
   ./auto-monitor.sh start
   ```

4. **Disaster Recovery Prep**:
   ```bash
   # Test monthly
   ./backup-ec2.sh --full
   ./restore-backup.sh <backup-id> --dry-run
   ```

---

## Troubleshooting

### Common Issues

**Deployment fails**:
- Check SSH key permissions: `chmod 400 liap-tui-key-*.pem`
- Verify EC2 instance is running
- Check disk space: `./quick-monitor.sh`

**High costs**:
- Run `./aws-free-tier-check.sh`
- Check for unattached resources
- Review CloudWatch logs for anomalies

**Performance issues**:
- Use `./monitor-ec2.sh --continuous`
- Check `./maintain-ec2.sh` was run recently
- Review container logs

### Support

For issues with scripts:
1. Check script has execute permissions: `chmod +x script-name.sh`
2. Run with debug mode: `bash -x script-name.sh`
3. Check prerequisites are installed
4. Review logs in `/var/log/liap-tui/`

---

## Script Development Guidelines

When creating new scripts:

1. **Header Template**:
   ```bash
   #!/bin/bash
   # Purpose: Clear description
   # Usage: script-name.sh [options]
   # Prerequisites: List requirements
   ```

2. **Error Handling**:
   ```bash
   set -e  # Exit on error
   set -u  # Exit on undefined variable
   ```

3. **Logging**:
   ```bash
   LOG_FILE="/var/log/liap-tui/script-name.log"
   echo "[$(date)] Message" >> $LOG_FILE
   ```

4. **Colors for Output**:
   ```bash
   GREEN='\033[0;32m'
   RED='\033[0;31m'
   NC='\033[0m'
   echo -e "${GREEN}✅ Success${NC}"
   ```

This guide is maintained alongside the scripts. For the latest updates, check the repository.