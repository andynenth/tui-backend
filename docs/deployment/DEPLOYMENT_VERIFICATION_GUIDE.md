# Deployment Verification Guide

Complete checklist to verify your Liap Tui deployment on EC2.

## Quick Verification Script

```bash
# Run from your local machine
./verify-deployment.sh https://34.233.7.20

# Or for HTTP (non-SSL)
./verify-deployment.sh http://34.233.7.20
```

## Manual Verification Checklist

### 1. 🏥 Core Health Checks

```bash
# Basic health
curl -k https://34.233.7.20/api/health
# Expected: {"status":"healthy","timestamp":...}

# Detailed health
curl -k https://34.233.7.20/api/health/detailed
# Expected: Detailed system info including database paths
```

### 2. 🎮 Game Functionality

1. **Browser Test**:
   - Visit https://34.233.7.20
   - Should see the game lobby
   - Create a room
   - Start a game with bots
   - Play a few turns

2. **WebSocket Test**:
   - Open browser DevTools > Network > WS
   - Should see active WebSocket connections
   - Check for "phase_change" messages during gameplay

### 3. 📊 Telemetry System

1. **Dashboard Access**:
   ```bash
   # Open in browser
   https://34.233.7.20/telemetry-dashboard
   ```

2. **Data Collection**:
   - Play the game for a minute
   - Refresh telemetry dashboard
   - Should see new events in Live Event feed
   - Check metrics are updating

3. **API Test**:
   ```bash
   # Check analytics
   curl -k https://34.233.7.20/api/analytics/bundle-load-stats?hours=1
   ```

### 4. 🗄️ Database Verification

**On EC2 Server**:
```bash
# SSH to server
ssh -i liap-tui-key-1755152170.pem ubuntu@34.233.7.20

# Check databases
ls -la /home/ubuntu/liap-tui-data/
# Should see:
# - game_events.db (>0 bytes)
# - telemetry_data.db (>0 bytes)

# Verify data
sudo docker exec liap-tui-backend-1 sqlite3 /app/data/game_events.db "SELECT COUNT(*) FROM events;"
sudo docker exec liap-tui-backend-1 sqlite3 /app/data/telemetry_data.db "SELECT COUNT(*) FROM telemetry_events;"
```

### 5. 🔍 Container & Logs

```bash
# On EC2 server
# Check containers running
sudo docker-compose ps
# Should show: liap-tui-backend-1 running on port 80/443

# Check logs
sudo docker-compose logs --tail=50
# Look for:
# - "Application startup complete"
# - "Telemetry database initialized"
# - No error messages

# Live logs
sudo docker-compose logs -f
# Then visit the site and verify requests are logged
```

### 6. 🔒 SSL Certificate (if using HTTPS)

```bash
# Check certificate
curl -vI https://34.233.7.20 2>&1 | grep -A 5 "SSL connection"

# Or use openssl
openssl s_client -connect 34.233.7.20:443 -servername 34.233.7.20 < /dev/null
```

### 7. 🚀 Performance Checks

```bash
# Response time test
time curl -k https://34.233.7.20/api/health

# Load test (be gentle!)
for i in {1..10}; do
  curl -k -s -o /dev/null -w "%{time_total}\n" https://34.233.7.20/api/health
done | awk '{sum+=$1} END {print "Average response time: " sum/NR "s"}'
```

## Common Issues & Solutions

### Issue: 502 Bad Gateway
- **Check**: Is container running? `sudo docker-compose ps`
- **Fix**: `sudo docker-compose restart`

### Issue: WebSocket Connection Failed
- **Check**: Browser console for errors
- **Fix**: Ensure using `wss://` for HTTPS sites

### Issue: Telemetry Not Recording
- **Check**: Database file exists and has write permissions
- **Fix**:
  ```bash
  sudo docker-compose exec backend ls -la /app/data/
  # If permission issues:
  sudo chmod 666 /home/ubuntu/liap-tui-data/telemetry_data.db
  ```

### Issue: Slow Performance
- **Check**: Container resources `sudo docker stats`
- **Check**: Database size `du -h /home/ubuntu/liap-tui-data/`
- **Fix**: May need to upgrade from t2.micro if consistently slow

## Monitoring Commands

```bash
# Real-time container stats
sudo docker stats

# Disk usage
df -h

# Memory usage
free -h

# Network connections
sudo netstat -tlnp
```

## Success Criteria

✅ All health endpoints return 200 OK
✅ Game loads and is playable
✅ WebSocket connections work
✅ Telemetry dashboard shows data
✅ Databases are being written to
✅ No errors in docker logs
✅ Response times < 1 second

## Next Steps

After verification:
1. Set up monitoring alerts
2. Configure backups for databases
3. Set up log rotation
4. Consider CloudWatch integration
5. Plan for scaling if needed
