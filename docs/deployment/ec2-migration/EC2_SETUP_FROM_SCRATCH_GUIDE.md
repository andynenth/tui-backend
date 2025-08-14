# Setting Up EC2 From Scratch Guide

This guide explains how to set up a new EC2 instance from scratch, like we did today. Use this if you need to create a new server or move to a different AWS account.

## 📋 Prerequisites

1. **AWS Account** with Free Tier eligibility
2. **AWS CLI** installed on your computer
3. **Docker** installed locally
4. **Your project** with these files:
   - Dockerfile.prod
   - docker-compose.prod.yml
   - All the scripts we created

## 🚀 Phase 1: Prepare Your Code

### 1.1 Check Required Files

Make sure you have these files in your project:
- ✅ `Dockerfile.prod` - Builds your production image
- ✅ `docker-compose.prod.yml` - Production configuration
- ✅ `requirements.txt` - Python dependencies
- ✅ `package.json` - Frontend dependencies

### 1.2 Test Local Build

```bash
# Test that Docker build works
docker build -f Dockerfile.prod -t liap-tui:latest .
```

## 🖥️ Phase 2: Launch EC2 Instance

### Option A: Use the Script (Easiest)

```bash
# This will launch a new EC2 instance
./launch-ec2-instance.sh
```

The script will:
- Find Ubuntu 22.04 AMI
- Create SSH key pair
- Set up security groups
- Launch t2.micro instance
- Assign Elastic IP

### Option B: Manual AWS Console Method

1. **Go to EC2 Console**: https://console.aws.amazon.com/ec2/

2. **Launch Instance**:
   - Name: `liap-tui-game-server`
   - AMI: Ubuntu Server 22.04 LTS
   - Instance Type: t2.micro (Free tier)
   - Key pair: Create new or select existing
   - Network: Allow SSH, HTTP, HTTPS
   - Storage: 30GB gp3

3. **Allocate Elastic IP**:
   - Go to Elastic IPs
   - Allocate new address
   - Associate with your instance

4. **Save Connection Info**:
   ```bash
   EC2_IP=your-elastic-ip
   KEY_FILE=your-key.pem
   ```

## 🔧 Phase 3: Configure the Server

### 3.1 Connect to Server

```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

### 3.2 Run Setup Script

First, copy the setup script:
```bash
scp -i your-key.pem ec2-setup.sh ubuntu@your-ec2-ip:~/
```

Then run it:
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
chmod +x ec2-setup.sh
./ec2-setup.sh
exit
```

This installs:
- Docker & Docker Compose
- Creates directories for data/logs/backups
- Sets up automatic backups
- Configures firewall

### 3.3 Log Back In

```bash
# Need to log out and back in for Docker permissions
ssh -i your-key.pem ubuntu@your-ec2-ip
```

## 📦 Phase 4: Deploy Your Application

### 4.1 Update Configuration Files

Edit `deploy-ec2.sh`:
```bash
EC2_HOST="your-ec2-ip"
KEY_PATH="./your-key.pem"
```

Edit `docker-compose.prod.yml`:
```yaml
environment:
  - ALLOWED_ORIGINS=http://localhost,http://your-ec2-ip
```

### 4.2 Build and Deploy

```bash
# Build Docker image
docker build -f Dockerfile.prod -t liap-tui:latest .

# Deploy to EC2
./deploy-ec2.sh
```

### 4.3 Or Deploy Manually

```bash
# Save image
docker save liap-tui:latest | gzip > liap-tui.tar.gz

# Upload to EC2
scp -i your-key.pem liap-tui.tar.gz ubuntu@your-ec2-ip:~/

# Also upload docker-compose.yml
scp -i your-key.pem docker-compose.prod.yml ubuntu@your-ec2-ip:~/docker-compose.yml

# Connect to EC2
ssh -i your-key.pem ubuntu@your-ec2-ip

# Load and start
gzip -d -c liap-tui.tar.gz | docker load
docker-compose up -d

# Check if running
docker ps
exit
```

## ✅ Phase 5: Verify Everything Works

### 5.1 Check Health

```bash
curl http://your-ec2-ip/api/health
```

### 5.2 Test in Browser

Open http://your-ec2-ip in your browser

### 5.3 Check Logs

```bash
ssh -i your-key.pem ubuntu@your-ec2-ip "docker logs liap-tui-game"
```

## 💰 Phase 6: Set Up Cost Monitoring

### 6.1 AWS Billing Alerts

1. Go to: https://console.aws.amazon.com/billing/
2. Enable "Receive Billing Alerts"
3. Set up CloudWatch alarms for $1, $5, $10

### 6.2 Monitor Free Tier

```bash
./monitor-aws-costs.sh
```

## 🔐 Phase 7: Security & Backups

### 7.1 Test Backup

```bash
./backup-game-ec2.sh
```

### 7.2 Update All Scripts

Update these scripts with your new EC2 details:
- backup-ec2.sh
- monitor-ec2.sh
- All other scripts that reference EC2

## 📝 Important Notes

### Free Tier Limits
- 750 hours/month EC2 t2.micro
- 30GB EBS storage
- 15GB data transfer out

### Monthly Maintenance
1. Check AWS bill
2. Run security updates
3. Download backups
4. Check disk space

### If Something Goes Wrong
1. Check EC2 instance status in AWS Console
2. Check Security Group rules
3. Verify Docker is running
4. Check container logs

## 🆘 Troubleshooting Commands

```bash
# Check if instance is running
aws ec2 describe-instances --instance-ids i-xxxxxx

# Check security groups
aws ec2 describe-security-groups --group-ids sg-xxxxxx

# Restart instance if needed
aws ec2 reboot-instances --instance-ids i-xxxxxx

# Check system resources on EC2
ssh -i key.pem ubuntu@ip "free -m && df -h"
```

## 📊 What Success Looks Like

When everything is working:
- ✅ Can SSH to server
- ✅ Docker container running
- ✅ Health check returns 200 OK
- ✅ Game accessible in browser
- ✅ Backups working
- ✅ Monitoring scripts work

---

This process usually takes 30-60 minutes from start to finish.