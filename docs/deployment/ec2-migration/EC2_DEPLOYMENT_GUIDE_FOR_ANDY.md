# EC2 Deployment Guide for Andy

This guide will help you deploy updates to your Liap Tui game on EC2. Follow these steps whenever you make changes to your code.

## 🔑 Quick Info
- **Your EC2 IP**: 34.233.7.20
- **Game URL**: http://34.233.7.20
- **SSH Key**: liap-tui-key-1755152170.pem

## 📋 Pre-Deployment Checklist

Before deploying, make sure you have:
- [ ] Tested your changes locally
- [ ] Committed your code to git
- [ ] Your SSH key file (`liap-tui-key-1755152170.pem`) in the project directory

## 🚀 Method 1: Quick Deploy (Recommended)

This is the easiest way - just run one command:

```bash
./deploy-ec2.sh
```

This script will:
1. Build your Docker image locally
2. Save it as a compressed file
3. Upload it to your EC2 server
4. Load it on the server
5. Restart your game

**Note**: This takes 5-10 minutes depending on your internet speed.

## 🛠️ Method 2: Manual Deploy (Step by Step)

If the script fails or you want to do it manually:

### Step 1: Build the Docker Image
```bash
docker build -f Dockerfile.prod -t liap-tui:latest .
```

### Step 2: Save the Image
```bash
docker save liap-tui:latest | gzip > liap-tui-latest.tar.gz
```

### Step 3: Upload to EC2
```bash
scp -i liap-tui-key-1755152170.pem liap-tui-latest.tar.gz ubuntu@34.233.7.20:~/
```

### Step 4: Connect to EC2
```bash
ssh -i liap-tui-key-1755152170.pem ubuntu@34.233.7.20
```

### Step 5: Load the New Image (on EC2)
```bash
# Load the Docker image
gzip -d -c liap-tui-latest.tar.gz | docker load

# Stop the current container
docker stop liap-tui-game

# Start with new image
docker start liap-tui-game

# Check if it's running
docker ps

# Exit SSH
exit
```

### Step 6: Verify Deployment
Open http://34.233.7.20 in your browser to check if the game is working.

## 🔧 Common Tasks

### Check Game Status
```bash
./quick-monitor.sh
```

### View Game Logs
```bash
ssh -i liap-tui-key-1755152170.pem ubuntu@34.233.7.20 "docker logs liap-tui-game --tail 50"
```

### Restart Game
```bash
ssh -i liap-tui-key-1755152170.pem ubuntu@34.233.7.20 "docker restart liap-tui-game"
```

### Create Backup
```bash
./backup-game-ec2.sh
```

### Connect to Server
```bash
./connect-to-ec2.sh
```

## 🐛 Troubleshooting

### Problem: "Permission denied" when using SSH
**Solution**: Make sure your key has the right permissions:
```bash
chmod 400 liap-tui-key-1755152170.pem
```

### Problem: Docker image build fails
**Solution**: Make sure you're in the project directory and Docker is running:
```bash
cd /Users/nrw/python/tui-project/liap-tui
docker --version  # Should show Docker version
```

### Problem: Game not accessible after deploy
**Solution**: Check if container is running:
```bash
ssh -i liap-tui-key-1755152170.pem ubuntu@34.233.7.20 "docker ps"
```

If not running, check logs:
```bash
ssh -i liap-tui-key-1755152170.pem ubuntu@34.233.7.20 "docker logs liap-tui-game --tail 100"
```

### Problem: Deploy script fails
**Solution**: Try the manual method above, or check:
- Is Docker running locally?
- Do you have internet connection?
- Is the EC2 instance running? (Check AWS Console)

## 💰 Cost Monitoring

Check your AWS costs regularly:
```bash
./monitor-aws-costs.sh
```

Remember: You have 750 hours free per month for the first year.

## 🔐 Security Reminders

1. **Never share your SSH key** (`liap-tui-key-1755152170.pem`)
2. **Keep backups** - Run `./backup-game-ec2.sh` weekly
3. **Update server** - Monthly, run:
   ```bash
   ssh -i liap-tui-key-1755152170.pem ubuntu@34.233.7.20
   sudo apt update && sudo apt upgrade -y
   exit
   ```

## 📝 Development Workflow

When you make changes to your code:

1. **Test locally first**:
   ```bash
   ./start.sh  # Run local development server
   ```

2. **Check code quality**:
   ```bash
   cd frontend && npm run lint
   cd ../backend && black . && pylint engine/ api/
   ```

3. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Your change description"
   ```

4. **Deploy to EC2**:
   ```bash
   ./deploy-ec2.sh
   ```

5. **Verify deployment**:
   ```bash
   ./quick-monitor.sh
   ```

## 🆘 Getting Help

If something goes wrong:

1. Check the logs first
2. Try restarting the container
3. Check if EC2 instance is running in AWS Console
4. Make sure you haven't exceeded Free Tier limits

## 📚 File Reference

- **SSH Key**: `liap-tui-key-1755152170.pem` - Your server access key
- **Deploy Script**: `deploy-ec2.sh` - Automated deployment
- **Monitor Script**: `quick-monitor.sh` - Check server status
- **Backup Script**: `backup-game-ec2.sh` - Create backups
- **Docker Config**: `docker-compose.prod.yml` - Production configuration

## 🎯 Quick Commands Cheat Sheet

```bash
# Deploy updates
./deploy-ec2.sh

# Check status
./quick-monitor.sh

# View logs
ssh -i liap-tui-key-1755152170.pem ubuntu@34.233.7.20 "docker logs liap-tui-game --tail 50"

# Restart game
ssh -i liap-tui-key-1755152170.pem ubuntu@34.233.7.20 "docker restart liap-tui-game"

# Create backup
./backup-game-ec2.sh

# Check costs
./monitor-aws-costs.sh

# Connect to server
./connect-to-ec2.sh
```

---

Remember: Your game is live at http://34.233.7.20 - test it after each deployment!
