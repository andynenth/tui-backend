# EC2 + Docker Compose Migration Plan for AWS Free Tier

## Overview

This document outlines the migration from ECS to a simpler EC2 + Docker Compose setup that's more suitable for AWS Free Tier users and provides easy database persistence.

## Current State
- **Deployment**: AWS ECS with task definitions
- **Database**: SQLite stored inside container (data lost on restart)
- **Complexity**: High (ECS cluster, services, task definitions, ALB)
- **Cost Risk**: ECS can exceed free tier limits

## Target State
- **Deployment**: Single EC2 instance with Docker Compose
- **Database**: SQLite with Docker volume persistence
- **Complexity**: Low (just EC2 + Docker)
- **Cost**: Free tier friendly (t2.micro instance)

## Benefits of Migration

1. **Simplicity**: Deploy with `docker-compose up -d`
2. **Database Persistence**: Built-in Docker volume support
3. **Cost Effective**: Only uses EC2 free tier
4. **Easy Backups**: Simple volume backup commands
5. **Local Testing**: Same docker-compose works locally
6. **Direct Control**: SSH access for debugging

## Implementation Plan

### Phase 1: Code Changes (Week 1)

#### 1.1 Add Environment Variable Support for Database Path

**File: `backend/services/event_store_v2.py`**
```python
import os
from pathlib import Path

def __init__(self, db_path: Optional[str] = None):
    if db_path is None:
        # Check environment variable first
        env_db_path = os.getenv('DATABASE_PATH')
        if env_db_path:
            self.db_path = env_db_path
            # Ensure directory exists
            db_dir = Path(self.db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
        else:
            # Fall back to current behavior
            current_dir = Path(__file__).resolve()
            project_root = current_dir.parent.parent.parent
            self.db_path = str(project_root / "game_events.db")
    else:
        self.db_path = db_path
```

**File: `backend/services/play_history_db.py`**
```python
# Same changes as above
```

#### 1.2 Update Dockerfile.prod

Add data directory creation:
```dockerfile
# After line 33, add:
# Create data directory for database with correct permissions
RUN mkdir -p /app/data && chown -R appuser:appuser /app/data

# The existing chown on line 43 becomes:
RUN chown -R appuser:appuser /app
```

#### 1.3 Create docker-compose.prod.yml

```yaml
version: '3.8'

services:
  liap-tui:
    build:
      context: .
      dockerfile: Dockerfile.prod
    image: liap-tui:latest
    container_name: liap-tui-game
    ports:
      - "80:5050"
    volumes:
      # Database persistence
      - game_data:/app/data
      # Logs persistence (optional)
      - ./logs:/app/logs
    environment:
      # Database
      - DATABASE_PATH=/app/data/game_events.db

      # Application settings
      - API_HOST=0.0.0.0
      - API_PORT=5050
      - DEBUG=false

      # Game settings
      - MAX_SCORE=50
      - MAX_ROUNDS=20
      - BOT_ENABLED=true

      # CORS (update with your domain later)
      - ALLOWED_ORIGINS=http://localhost,http://YOUR_EC2_IP

    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5050/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

volumes:
  game_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /home/ubuntu/liap-tui-data
```

#### 1.4 Create Deployment Scripts

**File: `deploy-ec2.sh`**
```bash
#!/bin/bash
# Simplified deployment for EC2 + Docker Compose

set -e

# Configuration
EC2_HOST="your-ec2-ip-here"
EC2_USER="ubuntu"
KEY_PATH="~/.ssh/your-key.pem"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🚀 Starting EC2 deployment...${NC}"

# Build production image locally
echo -e "${GREEN}🏗️  Building production image...${NC}"
docker build -f Dockerfile.prod -t liap-tui:latest .

# Save image to tarball
echo -e "${GREEN}📦 Saving Docker image...${NC}"
docker save liap-tui:latest | gzip > liap-tui-latest.tar.gz

# Transfer files to EC2
echo -e "${GREEN}📤 Transferring files to EC2...${NC}"
scp -i ${KEY_PATH} liap-tui-latest.tar.gz ${EC2_USER}@${EC2_HOST}:~/
scp -i ${KEY_PATH} docker-compose.prod.yml ${EC2_USER}@${EC2_HOST}:~/docker-compose.yml

# Deploy on EC2
echo -e "${GREEN}🔄 Deploying on EC2...${NC}"
ssh -i ${KEY_PATH} ${EC2_USER}@${EC2_HOST} << 'ENDSSH'
  # Load Docker image
  docker load < liap-tui-latest.tar.gz

  # Create data directory if not exists
  mkdir -p /home/ubuntu/liap-tui-data

  # Stop existing container
  docker-compose down || true

  # Start new container
  docker-compose up -d

  # Cleanup
  rm liap-tui-latest.tar.gz

  echo "✅ Deployment complete!"
ENDSSH

# Cleanup local file
rm liap-tui-latest.tar.gz

echo -e "${GREEN}✅ EC2 deployment successful!${NC}"
echo -e "${GREEN}🌐 Application URL: http://${EC2_HOST}${NC}"
```

**File: `backup-ec2.sh`**
```bash
#!/bin/bash
# Backup game database from EC2

EC2_HOST="your-ec2-ip-here"
EC2_USER="ubuntu"
KEY_PATH="~/.ssh/your-key.pem"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create local backup directory
mkdir -p backups

# Create backup on EC2
ssh -i ${KEY_PATH} ${EC2_USER}@${EC2_HOST} << ENDSSH
  cd ~
  docker run --rm \
    -v liap-tui-game_data:/data \
    -v \$(pwd):/backup \
    alpine tar czf /backup/game_backup_${TIMESTAMP}.tar.gz -C /data .
ENDSSH

# Download backup
scp -i ${KEY_PATH} ${EC2_USER}@${EC2_HOST}:~/game_backup_${TIMESTAMP}.tar.gz ./backups/

# Cleanup remote backup
ssh -i ${KEY_PATH} ${EC2_USER}@${EC2_HOST} "rm ~/game_backup_${TIMESTAMP}.tar.gz"

echo "✅ Backup saved to: backups/game_backup_${TIMESTAMP}.tar.gz"
```

### Phase 2: AWS Setup (Week 1)

#### 2.1 Launch EC2 Instance

1. **Launch EC2 Instance**:
   - AMI: Ubuntu 22.04 LTS
   - Instance Type: t2.micro (free tier)
   - Storage: 30GB (free tier max)
   - Security Group:
     - Port 22 (SSH) - Your IP
     - Port 80 (HTTP) - 0.0.0.0/0
     - Port 443 (HTTPS) - 0.0.0.0/0 (future)

2. **Install Docker on EC2**:
```bash
# Connect to EC2
ssh -i your-key.pem ubuntu@your-ec2-ip

# Install Docker
sudo apt update
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker ubuntu
# Logout and login again for group changes

# Create data directory
mkdir -p /home/ubuntu/liap-tui-data
```

### Phase 3: Migration Steps (Week 2)

#### 3.1 Pre-Migration Checklist

- [ ] Backup current ECS database (if any data exists)
- [ ] Test docker-compose.prod.yml locally
- [ ] Update EC2_HOST in deployment scripts
- [ ] Ensure EC2 security group is configured

#### 3.2 Migration Process

1. **Stop ECS Service** (prevent new data during migration):
   ```bash
   aws ecs update-service --cluster liap-tui-cluster --service liap-tui-service --desired-count 0
   ```

2. **Export Data from ECS** (if needed):
   - SSH into ECS container
   - Copy game_events.db
   - Download to local machine

3. **Deploy to EC2**:
   ```bash
   ./deploy-ec2.sh
   ```

4. **Import Existing Data** (if any):
   ```bash
   scp -i ~/.ssh/your-key.pem game_events.db ubuntu@your-ec2-ip:~/
   ssh -i ~/.ssh/your-key.pem ubuntu@your-ec2-ip
   docker cp game_events.db liap-tui-game:/app/data/
   ```

5. **Verify Deployment**:
   - Check health: `http://your-ec2-ip/api/health`
   - Test game creation
   - Verify data persistence after container restart

6. **Update DNS** (if using custom domain):
   - Point domain to EC2 Elastic IP
   - Update ALLOWED_ORIGINS in docker-compose

### Phase 4: Post-Migration (Week 2)

#### 4.1 Setup Automated Backups

Add to EC2 crontab:
```bash
# Daily backup at 2 AM
0 2 * * * /home/ubuntu/backup-game.sh

# backup-game.sh content:
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d)
docker run --rm \
  -v liap-tui-game_data:/data \
  -v /home/ubuntu/backups:/backup \
  alpine tar czf /backup/game_backup_${TIMESTAMP}.tar.gz -C /data .

# Keep only last 7 backups
cd /home/ubuntu/backups
ls -t game_backup_*.tar.gz | tail -n +8 | xargs -r rm
```

#### 4.2 Setup Monitoring

1. **CloudWatch Alarms**:
   - CPU usage > 80%
   - Disk usage > 80%
   - Instance health check failures

2. **Application Monitoring**:
   ```bash
   # Add to crontab
   */5 * * * * curl -f http://localhost/api/health || systemctl restart docker
   ```

#### 4.3 Documentation Updates

Update README with:
- New deployment process
- Backup/restore procedures
- Troubleshooting guide
- EC2 maintenance tasks

### Phase 5: Cleanup (Week 3)

1. **Remove ECS Resources**:
   ```bash
   # After confirming EC2 is stable
   aws ecs delete-service --cluster liap-tui-cluster --service liap-tui-service --force
   aws ecs delete-cluster --cluster liap-tui-cluster
   ```

2. **Remove unused resources**:
   - ECR images (keep latest few)
   - ALB (if not needed)
   - Target groups
   - Task definitions

## Cost Comparison

### Current (ECS):
- ECS Service: Potential charges
- ALB: ~$16/month after free tier
- ECR Storage: Accumulating
- Data Transfer: Variable

### New (EC2 + Docker):
- EC2 t2.micro: Free tier (750 hrs/month)
- EBS Storage: Free tier (30GB)
- Data Transfer: Free tier (15GB/month)
- **Total**: $0 for first year

## Rollback Plan

If issues arise:

1. **Quick Rollback**:
   ```bash
   # Restart ECS service
   aws ecs update-service --cluster liap-tui-cluster --service liap-tui-service --desired-count 1
   ```

2. **Data Recovery**:
   - Restore from EC2 backup
   - Import to ECS if needed

## Success Criteria

- [ ] Application accessible on EC2
- [ ] Database persists after container restart
- [ ] Automated backups working
- [ ] Health checks passing
- [ ] Performance acceptable (< 500ms response)
- [ ] Zero data loss during migration

## Timeline

- **Week 1**: Code changes and local testing
- **Week 1**: EC2 setup and initial deployment
- **Week 2**: Migration and monitoring setup
- **Week 3**: Cleanup and documentation

## Questions to Answer

1. **Domain/DNS**: Do you have a custom domain to point to EC2?
2. **Data Size**: How much data in current ECS deployment?
3. **Downtime**: Acceptable downtime window for migration?
4. **Backup Frequency**: Daily backups sufficient?

## Next Steps

1. Review and approve this plan
2. Create feature branch for code changes
3. Test locally with docker-compose
4. Proceed with EC2 setup

---

This migration will significantly simplify your infrastructure while ensuring reliable database persistence and staying within AWS Free Tier limits!
