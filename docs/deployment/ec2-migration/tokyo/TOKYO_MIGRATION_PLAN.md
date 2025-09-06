# Migration Plan: Canada (ca-central-1) to Tokyo (ap-northeast-1)

## Current Setup
- **Current Region**: us-east-1 (N. Virginia) - based on EC2 IP
- **EC2 Instance**: 34.233.7.20
- **Deployment Method**: EC2 + Docker Compose

## Migration Steps

### 1. Launch New EC2 Instance in Tokyo
```bash
# Launch EC2 in ap-northeast-1 with same specs as current instance
# AMI: Ubuntu 22.04 LTS (ami-0d52744d6551d851e for Tokyo)
# Instance type: Same as current (likely t3.medium or similar)
# Security Group: Allow ports 80, 443, 22, 5050
```

### 2. Prepare the New EC2 Instance
```bash
# SSH into new Tokyo instance
ssh -i liap-tui-key-tokyo.pem ubuntu@<NEW_TOKYO_IP>

# Install Docker and Docker Compose
sudo apt-get update
sudo apt-get install -y docker.io docker-compose
sudo usermod -aG docker ubuntu
# Log out and back in

# Create necessary directories
mkdir -p ~/liap-tui-data
mkdir -p ~/logs
chmod 755 ~/logs
```

### 3. Update Deployment Script for Tokyo
Create `deploy-ec2-tokyo.sh`:
```bash
#!/bin/bash
# Tokyo EC2 deployment script

set -e

# Configuration
EC2_HOST="<NEW_TOKYO_IP>"  # Will be filled after instance creation
EC2_USER="ubuntu"
KEY_PATH="./liap-tui-key-tokyo.pem"  # New key for Tokyo region

# Rest of the script remains the same...
```

### 4. Migration Process

#### Phase 1: Test Deployment (Parallel Running)
1. Deploy to Tokyo instance
2. Test with some users
3. Keep Canada instance running

#### Phase 2: DNS Switch
1. Update DNS to point to Tokyo IP
2. Monitor for issues
3. Keep Canada instance as backup

#### Phase 3: Cleanup
1. After 24-48 hours stable operation
2. Terminate Canada instance
3. Delete old resources

## Latency Improvements

### Before (Canada/US-East):
- Vancouver → Server: ~80-100ms
- Thailand → Server: ~250-300ms

### After (Tokyo):
- Vancouver → Server: ~120ms
- Thailand → Server: ~120ms
- **Both players get balanced latency!**

## Cost Considerations
- Tokyo region pricing is similar to US regions
- Data transfer between regions during migration: minimal cost
- No additional costs for the application itself

## Rollback Plan
If issues arise:
1. Switch DNS back to Canada instance
2. Investigate and fix issues
3. Retry migration

## Timeline
- **Day 1**: Launch Tokyo instance, test deployment
- **Day 2**: Switch DNS, monitor
- **Day 3-4**: Observe stability
- **Day 5**: Decommission Canada instance

## Notes
- Active games will be lost during migration (warn players)
- SQLite database (game_events.db) can be copied if needed
- Consider scheduling migration during low-traffic period