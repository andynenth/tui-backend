# ECS to EC2 Migration Checklist

## ✅ Migration Status: COMPLETED

**Summary**: Successfully migrated Liap Tui from ECS to EC2 on August 14, 2025
- **EC2 Instance**: i-031f0be2cfed1ff2f
- **IP Address**: 34.233.7.20
- **Game URL**: http://34.233.7.20
- **Status**: Live and operational
- **Cost**: $0/month (AWS Free Tier)

## Pre-Migration Phase
- [ ] Review current ECS setup
  - [ ] Note current ECS cluster name: `liap-tui-cluster`
  - [ ] Note current ECS service name: `liap-tui-service`
  - [ ] Note ECR repository URI: `300079938592.dkr.ecr.us-east-1.amazonaws.com/liap-tui`
  - [ ] Check if any data exists in current deployment
  - [ ] Document current ALB DNS name

## Phase 1: Code Preparation ✅
- [x] Add DATABASE_PATH environment variable support to event_store_v2.py
- [x] Add DATABASE_PATH environment variable support to play_history_db.py
- [x] Update Dockerfile.prod to create /app/data directory
- [x] Create docker-compose.prod.yml with volume mapping
- [x] Create deploy-ec2.sh deployment script
- [x] Create backup-ec2.sh backup script
- [x] Create ec2-setup.sh for EC2 initialization
- [x] Test environment variable support locally
- [x] Create deployment documentation

## Phase 2: AWS EC2 Setup ✅
- [x] Launch EC2 instance
  - [x] Instance type: t2.micro
  - [x] AMI: Ubuntu 22.04 LTS
  - [x] Storage: 30GB gp3
  - [x] Create/select SSH key pair
  - [x] Note instance ID: i-031f0be2cfed1ff2f
- [x] Configure Security Group
  - [x] Port 22 (SSH) - Your IP only
  - [x] Port 80 (HTTP) - 0.0.0.0/0
  - [x] Port 443 (HTTPS) - 0.0.0.0/0 (future)
- [x] Allocate Elastic IP
  - [x] Elastic IP: 34.233.7.20
  - [x] Associate with instance
- [x] Connect via SSH and test connection

## Phase 3: EC2 Configuration ✅
- [x] Upload ec2-setup.sh to EC2
- [x] Run ec2-setup.sh script
- [x] Logout and login to apply docker group
- [x] Verify Docker installation: `docker --version`
- [x] Verify directories created:
  - [x] /home/ubuntu/liap-tui-data
  - [x] /home/ubuntu/backups
  - [x] /home/ubuntu/logs
- [x] Verify cron jobs: `crontab -l`

## Phase 4: Data Backup (if applicable)
- [x] Check if current ECS has any game data
- N/A - Fresh deployment (no existing ECS data to migrate)

## Phase 5: Deployment ✅
- [x] Update deploy-ec2.sh with:
  - [x] EC2_HOST="34.233.7.20"
  - [x] KEY_PATH="./liap-tui-key-1755152170.pem"
- [x] Update docker-compose.prod.yml:
  - [x] ALLOWED_ORIGINS includes EC2 IP
- [x] Run deployment: `./deploy-ec2.sh`
- [x] Verify deployment:
  - [x] Health check: `curl http://34.233.7.20/api/health`
  - [x] Access game in browser
  - [x] Check docker logs

## Phase 6: Data Migration (if applicable)
- N/A - Fresh deployment (no data to migrate)

## Phase 7: Testing ✅
- [x] Create test room
- [x] Play a complete game
- [x] Verify data persists after container restart
- [x] Test backup script: `./backup-game-ec2.sh`
- [x] Download and verify backup
- [x] Check automated health checks working
- [x] Monitor logs for 1 hour

## Phase 8: DNS Update (if applicable)
- [ ] Update DNS A record to EC2 Elastic IP
- [ ] Wait for DNS propagation
- [ ] Test with domain name
- [ ] Update ALLOWED_ORIGINS with domain
- [ ] Redeploy with domain configuration

## Phase 9: Monitoring Setup ✅
- [x] Verify cron jobs running:
  - [x] Daily backups at 2 AM
  - [x] Health checks every 5 minutes
- [x] Set up AWS CloudWatch alarms:
  - [x] Billing alerts created ($1, $5, $10)
  - [ ] CPU usage > 80% (optional)
  - [ ] Disk usage > 80% (optional)
  - [ ] Instance status checks (optional)
- [x] Document monitoring procedures

## Phase 10: ECS Decommission
- [ ] Monitor EC2 for 24-48 hours
- [ ] Confirm stable operation
- [ ] Final ECS backup (if needed)
- [ ] Stop ECS service:
  ```bash
  aws ecs update-service --cluster liap-tui-cluster --service liap-tui-service --desired-count 0
  ```
- [ ] Wait 7 days (safety period)
- [ ] Delete ECS resources:
  - [ ] Delete service
  - [ ] Delete cluster
  - [ ] Delete task definitions (keep latest)
  - [ ] Clean ECR images (keep latest 3)
  - [ ] Delete ALB (if not needed)
  - [ ] Delete target groups

## Post-Migration Tasks
- [ ] Update README.md with new deployment process
- [ ] Update CI/CD pipelines (if any)
- [ ] Document backup/restore procedures
- [ ] Create runbook for common operations
- [ ] Schedule monthly backup downloads
- [ ] Plan for HTTPS implementation

## Rollback Plan
If issues occur:
1. [ ] Keep ECS running for 7 days minimum
2. [ ] Document any issues encountered
3. [ ] Have ECS restart commands ready:
   ```bash
   aws ecs update-service --cluster liap-tui-cluster --service liap-tui-service --desired-count 1
   ```

## Success Criteria ✅
- [x] Application accessible on EC2
- [x] Database persists across restarts
- [x] Automated backups working
- [x] Health checks passing
- [x] Performance acceptable (<500ms response)
- [x] Zero data loss during migration
- [x] All game features working
- [x] Monitoring and alerts configured

## Sign-offs
- [ ] Development team approval
- [ ] Testing complete
- [ ] Documentation updated
- [ ] Stakeholders notified

---

**Migration Started**: August 13, 2025
**Migration Completed**: August 14, 2025
**Performed By**: Andy (with Claude)

---

## 📁 Important Files Created

### SSH Key
- `liap-tui-key-1755152170.pem` - Keep this safe!

### Deployment Scripts
- `deploy-ec2.sh` - Deploy updates to EC2
- `backup-game-ec2.sh` - Create backups
- `restore-backup.sh` - Restore from backup

### Monitoring Scripts
- `quick-monitor.sh` - Quick status check
- `monitor-ec2.sh` - Detailed monitoring
- `monitor-aws-costs.sh` - Check Free Tier usage
- `auto-monitor.sh` - Continuous monitoring

### Connection
- `connect-to-ec2.sh` - SSH to your server

### Documentation
- `EC2_DEPLOYMENT_GUIDE.md` - Complete deployment guide
- `EC2_OPERATIONS_GUIDE.md` - Daily operations manual
