# Tokyo Migration Guide with SSL

## Overview
Migrating your Liap Tui game from US-East (34.233.7.20) to Tokyo (ap-northeast-1) while maintaining SSL support.

## Step-by-Step Migration

### Step 1: Launch Tokyo EC2 Instance

1. **Using AWS Console**:
   - Region: **ap-northeast-1** (Tokyo)
   - AMI: Ubuntu 22.04 LTS (`ami-0d52744d6551d851e`)
   - Instance Type: t3.medium (or same as current)
   - Storage: 30GB (or same as current)
   - Security Group Rules:
     - SSH (22): Your IP
     - HTTP (80): 0.0.0.0/0
     - HTTPS (443): 0.0.0.0/0
     - Custom TCP (5050): 0.0.0.0/0 (for testing)

2. **Download the new key** as `liap-tui-key-tokyo.pem`
3. **Set permissions**: `chmod 400 ~/.ssh/liap-tui-key-tokyo.pem`

### Step 2: Initial Server Setup

1. **Copy setup script to Tokyo server**:
   ```bash
   scp -i ~/.ssh/liap-tui-key-tokyo.pem tokyo-server-setup.sh ubuntu@TOKYO_IP:~/
   ```

2. **SSH into Tokyo server**:
   ```bash
   ssh -i ~/.ssh/liap-tui-key-tokyo.pem ubuntu@TOKYO_IP
   ```

3. **Run setup script**:
   ```bash
   chmod +x tokyo-server-setup.sh
   sudo ./tokyo-server-setup.sh
   exit
   ```

### Step 3: First Deployment (HTTP only)

1. **Update deployment script**:
   ```bash
   # Edit deploy-ec2-ssl-tokyo-no-rebuild.sh
   # Change: EC2_HOST="YOUR_TOKYO_EC2_IP" to actual IP
   # Change: KEY_PATH to your Tokyo key path
   ```

2. **Build and deploy**:
   ```bash
   # Build the image locally
   docker-compose -f docker-compose.prod-local.yml build
   
   # Deploy to Tokyo
   ./deploy-ec2-ssl-tokyo-no-rebuild.sh
   ```

3. **Test HTTP access**:
   - Open: http://TOKYO_IP
   - Create a test room
   - Verify game works

### Step 4: DNS Migration

1. **Update DNS A Record**:
   - Login to your DNS provider
   - Change A record for `castellan.andynenth.dev`
   - From: `34.233.7.20` (old US server)
   - To: `TOKYO_IP` (new Tokyo server)

2. **Wait for propagation** (5-30 minutes)
   - Check: `nslookup castellan.andynenth.dev`
   - Should return Tokyo IP

### Step 5: SSL Setup on Tokyo

1. **SSH into Tokyo server**:
   ```bash
   ssh -i ~/.ssh/liap-tui-key-tokyo.pem ubuntu@TOKYO_IP
   ```

2. **Get SSL certificate**:
   ```bash
   # Stop any services on port 80
   sudo docker-compose down
   
   # Get certificate
   sudo certbot certonly --standalone -d castellan.andynenth.dev
   
   # Start services again
   docker-compose up -d
   exit
   ```

3. **Deploy with SSL**:
   ```bash
   # Run deployment again to configure nginx
   ./deploy-ec2-ssl-tokyo-no-rebuild.sh
   ```

### Step 6: Verify SSL

1. **Test HTTPS**: https://castellan.andynenth.dev
2. **Check certificate**: Should show Let's Encrypt
3. **Test game functionality**

### Step 7: Monitor and Cleanup

1. **Monitor Tokyo server** for 24-48 hours
2. **Keep old server** as backup
3. **After stable operation**:
   - Stop old EC2 instance
   - Create AMI backup (optional)
   - Terminate instance

## Latency Improvements

### Before (US-East):
- Vancouver → Server: ~80-100ms
- Thailand → Server: ~250-300ms

### After (Tokyo):
- Vancouver → Server: ~120ms ✅
- Thailand → Server: ~120ms ✅
- **Both players get balanced latency!**

## Rollback Plan

If issues occur:
1. Change DNS A record back to `34.233.7.20`
2. Old server still running
3. Investigate issues on Tokyo server

## Important Notes

- **Active games** will be lost during migration
- **Best time**: During low traffic (late night US/early morning Asia)
- **Backup**: Download game_events.db if you need history

## Quick Commands Reference

```bash
# SSH to Tokyo
ssh -i ~/.ssh/liap-tui-key-tokyo.pem ubuntu@TOKYO_IP

# Deploy to Tokyo
./deploy-ec2-ssl-tokyo-no-rebuild.sh

# Check logs
ssh -i ~/.ssh/liap-tui-key-tokyo.pem ubuntu@TOKYO_IP 'docker logs liap-tui-game'

# Monitor performance
ssh -i ~/.ssh/liap-tui-key-tokyo.pem ubuntu@TOKYO_IP 'docker stats'
```

## Cost Estimate

- Tokyo t3.medium: ~$0.0464/hour (similar to US regions)
- Data transfer during migration: minimal
- Monthly cost: ~$34 (same as current)