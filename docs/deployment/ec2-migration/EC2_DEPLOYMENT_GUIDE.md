# EC2 Deployment Guide for Liap Tui

This guide walks you through deploying Liap Tui on AWS EC2 using Docker Compose with persistent database storage.

## Prerequisites

- AWS account with EC2 access
- SSH key pair for EC2 access
- Local Docker installation for building images
- Basic familiarity with AWS Console

## Step 1: Launch EC2 Instance

### 1.1 Launch Instance
1. Go to AWS EC2 Console
2. Click "Launch Instance"
3. Configure:
   - **Name**: `liap-tui-server`
   - **AMI**: Ubuntu Server 22.04 LTS (64-bit x86)
   - **Instance Type**: t2.micro (Free tier eligible)
   - **Key Pair**: Select existing or create new
   - **Network Settings**:
     - Allow SSH from your IP
     - Allow HTTP from anywhere (0.0.0.0/0)
   - **Storage**: 30 GB gp3 (Free tier max)

### 1.2 Elastic IP (Recommended)
1. Go to EC2 > Elastic IPs
2. Allocate new Elastic IP
3. Associate with your instance
4. Note the IP address

## Step 2: Initial EC2 Setup

### 2.1 Connect to EC2
```bash
ssh -i ~/.ssh/your-key.pem ubuntu@your-ec2-ip
```

### 2.2 Run Setup Script
Upload and run the setup script:
```bash
# On your local machine
scp -i ~/.ssh/your-key.pem ec2-setup.sh ubuntu@your-ec2-ip:~/

# On EC2
chmod +x ec2-setup.sh
./ec2-setup.sh
```

### 2.3 Logout and Login
```bash
exit
ssh -i ~/.ssh/your-key.pem ubuntu@your-ec2-ip
```

## Step 3: Deploy Application

### 3.1 Update Deployment Script
Edit `deploy-ec2.sh` on your local machine:
```bash
# Update these values
EC2_HOST="your-ec2-ip-here"
KEY_PATH="~/.ssh/your-key.pem"
```

### 3.2 Update docker-compose.prod.yml
Edit the ALLOWED_ORIGINS:
```yaml
- ALLOWED_ORIGINS=http://localhost,http://your-ec2-ip
```

### 3.3 Deploy
```bash
./deploy-ec2.sh
```

## Step 4: Verify Deployment

### 4.1 Check Health
```bash
curl http://your-ec2-ip/api/health
```

### 4.2 Access Game
Open browser: `http://your-ec2-ip`

### 4.3 Check Logs
```bash
# On EC2
docker logs liap-tui-game
```

## Step 5: Data Management

### 5.1 Manual Backup
```bash
# On EC2
./backup-game.sh
```

### 5.2 Download Backup
```bash
# On local machine
./backup-ec2.sh
```

### 5.3 Restore Backup
```bash
# Upload backup to EC2
scp -i ~/.ssh/your-key.pem backups/game_backup_20240114_120000.tar.gz ubuntu@your-ec2-ip:~/

# On EC2
docker-compose down
sudo rm -rf /home/ubuntu/liap-tui-data/*
sudo tar -xzf game_backup_20240114_120000.tar.gz -C /home/ubuntu/liap-tui-data/
docker-compose up -d
```

## Monitoring & Maintenance

### Health Monitoring
Health checks run automatically every 5 minutes. Check logs:
```bash
tail -f /home/ubuntu/logs/health-check.log
```

### Backup Monitoring
Daily backups run at 2 AM. Check logs:
```bash
tail -f /home/ubuntu/logs/backup.log
ls -la /home/ubuntu/backups/
```

### Container Management
```bash
# View running containers
docker ps

# View logs
docker logs -f liap-tui-game

# Restart container
docker-compose restart

# Stop container
docker-compose down

# Start container
docker-compose up -d
```

### System Monitoring
```bash
# CPU and Memory
htop

# Disk usage
df -h
ncdu /home/ubuntu/

# Network connections
sudo netstat -tulpn
```

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker logs liap-tui-game

# Check disk space
df -h

# Check permissions
ls -la /home/ubuntu/liap-tui-data/
```

### Database Issues
```bash
# Backup current database
./backup-game.sh

# Check database file
ls -la /home/ubuntu/liap-tui-data/

# Connect to container
docker exec -it liap-tui-game bash
```

### Network Issues
```bash
# Check security group
# Ensure port 80 is open in AWS Console

# Check container is listening
docker exec liap-tui-game netstat -tulpn

# Check nginx/reverse proxy if applicable
```

## Updates & Deployments

### Deploy New Version
```bash
# On local machine
./deploy-ec2.sh
```

### Rollback
```bash
# On EC2
docker-compose down
docker run liap-tui:previous-tag
```

## Security Best Practices

1. **SSH Access**
   - Use key-based authentication only
   - Restrict SSH to your IP in security group

2. **Application Security**
   - Keep Ubuntu packages updated: `sudo apt update && sudo apt upgrade`
   - Monitor logs for suspicious activity
   - Consider using HTTPS with Let's Encrypt

3. **Backup Security**
   - Download backups regularly
   - Store backups in multiple locations
   - Test restore procedures

## Cost Optimization

### Free Tier Usage
- t2.micro: 750 hours/month (1 instance 24/7)
- EBS: 30GB storage
- Data Transfer: 15GB/month out

### Cost Monitoring
- Set up billing alerts in AWS Console
- Monitor EC2 usage in Cost Explorer
- Stop instance when not needed (loses Elastic IP)

## Advanced Configuration

### Custom Domain
1. Register domain
2. Point A record to Elastic IP
3. Update ALLOWED_ORIGINS in docker-compose.yml
4. Redeploy

### HTTPS with Let's Encrypt
```bash
# Install Certbot
sudo apt install certbot

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com

# Update docker-compose to use certificates
```

### Performance Tuning
```yaml
# In docker-compose.yml
environment:
  - WORKERS=2  # Increase workers if needed
  - MAX_CONNECTIONS=100
```

## Migration from ECS

If migrating from ECS:

1. Export data from ECS
2. Stop ECS service
3. Import data to EC2
4. Update DNS if applicable
5. Monitor for 24-48 hours
6. Decommission ECS resources

## Support & Resources

- Game Documentation: See README.md
- AWS Documentation: https://docs.aws.amazon.com/ec2/
- Docker Documentation: https://docs.docker.com/

---

Remember to keep your deployment scripts and keys secure!
