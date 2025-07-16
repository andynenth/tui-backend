# Budget-Optimized EC2 Deployment Plan for Liap Tui
## Progressive Scaling for WebSocket Multiplayer Game

### Executive Summary
This plan provides a budget-conscious approach to deploying Liap Tui, starting from $20/month and scaling as your player base grows. It's specifically designed for how your game actually works: in-memory state, WebSocket connections, and room-based multiplayer.

---

## Current Architecture Reality

Your game uses:
- **In-memory room storage**: `RoomManager` stores rooms in Python dict
- **In-memory connections**: `SocketManager` tracks WebSockets by room  
- **No database**: Everything lives in application memory
- **Single instance design**: Not built for multi-instance state sharing

This means:
- ✅ Simple and fast for single instance
- ❌ Rooms are lost on restart
- ❌ Can't share rooms across instances
- ❌ Limited by single server capacity

---

## Phase 1: Launch on a Budget ($20/month)

### Architecture (0-100 concurrent players)
```
┌─────────────────────────────────────┐
│       CloudFlare CDN (Free)         │
│    (DDoS Protection + Caching)      │
└────────────────┬────────────────────┘
                 │
         ┌───────┴────────┐
         │   Elastic IP   │
         │   ($3.60/mo)   │
         └───────┬────────┘
                 │
         ┌───────┴────────┐
         │  EC2 t3.small  │
         │   ($15/mo)     │
         │                │
         │  Docker App    │
         │  - FastAPI     │
         │  - WebSocket   │
         │  - In-Memory   │
         └────────────────┘
```

### Implementation Checklist

#### 1.1 Code Preparations
- [ ] **Add Graceful Shutdown** (`backend/socket_manager.py`)
  ```python
  async def graceful_shutdown(self):
      """Notify players before restart"""
      shutdown_msg = {
          "event": "server_shutdown",
          "data": {
              "message": "Server restarting in 30 seconds",
              "reconnect_delay": 30
          }
      }
      
      # Broadcast to all rooms
      for room_id in list(self.room_connections.keys()):
          await self.broadcast(room_id, "server_shutdown", shutdown_msg["data"])
      
      # Wait for messages to send
      await asyncio.sleep(2)
      
      # Close connections cleanly
      for room_id, connections in list(self.room_connections.items()):
          for ws in list(connections):
              await self.unregister(room_id, ws)
  ```

- [ ] **Add Health Monitoring** (`backend/api/routes/routes.py`)
  ```python
  @router.get("/health/detailed")
  async def health_detailed():
      """Detailed health with resource usage"""
      import psutil
      
      return {
          "status": "healthy",
          "timestamp": datetime.utcnow().isoformat(),
          "resources": {
              "cpu_percent": psutil.cpu_percent(interval=1),
              "memory_percent": psutil.virtual_memory().percent,
              "memory_mb": psutil.virtual_memory().used / 1024 / 1024
          },
          "game_stats": {
              "active_rooms": len(room_manager.rooms),
              "active_connections": sum(
                  len(conns) for conns in socket_manager.room_connections.values()
              ),
              "active_games": len([
                  r for r in room_manager.rooms.values() 
                  if r.game_started and not r.game_ended
              ])
          }
      }
  ```

- [ ] **Optimize Docker Image**
  ```dockerfile
  # Dockerfile.production
  FROM python:3.11-slim AS builder
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install --user --no-cache-dir -r requirements.txt

  FROM python:3.11-slim
  WORKDIR /app
  
  # Install only runtime dependencies
  RUN apt-get update && apt-get install -y --no-install-recommends \
      curl \
      && rm -rf /var/lib/apt/lists/*
  
  # Copy installed packages
  COPY --from=builder /root/.local /root/.local
  
  # Copy application
  COPY backend/ ./backend/
  COPY static/ ./backend/static/
  
  ENV PATH=/root/.local/bin:$PATH
  ENV PYTHONPATH=/app
  ENV PYTHONUNBUFFERED=1
  
  # Create non-root user
  RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
  USER appuser
  
  HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD curl -f http://localhost:5050/api/health || exit 1
  
  EXPOSE 5050
  CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "5050", "--workers", "1"]
  ```

#### 1.2 AWS Setup
- [ ] **Launch EC2 Instance**
  ```bash
  # User data script
  #!/bin/bash
  # Install Docker
  yum update -y
  amazon-linux-extras install docker -y
  service docker start
  usermod -a -G docker ec2-user
  
  # Install docker-compose
  curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
  chmod +x /usr/local/bin/docker-compose
  
  # Create app directory
  mkdir -p /home/ec2-user/app
  chown ec2-user:ec2-user /home/ec2-user/app
  
  # Install CloudWatch agent (free tier includes basic metrics)
  wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
  rpm -U ./amazon-cloudwatch-agent.rpm
  ```

- [ ] **Security Group Rules**
  - Inbound: 
    - HTTP (80) from CloudFlare IPs only
    - HTTPS (443) from CloudFlare IPs only  
    - SSH (22) from your IP only
    - Custom TCP (5050) from anywhere (temporarily, for testing)
  - Outbound: All traffic allowed

- [ ] **Elastic IP**
  - Allocate and associate to instance
  - Update CloudFlare DNS to point to Elastic IP

#### 1.3 Deployment Process
- [ ] **Initial Deploy Script**
  ```bash
  #!/bin/bash
  # deploy.sh
  
  # Build and push to ECR (or Docker Hub for free tier)
  docker build -t liap-tui:latest .
  docker tag liap-tui:latest your-dockerhub/liap-tui:latest
  docker push your-dockerhub/liap-tui:latest
  
  # On EC2 instance
  ssh ec2-user@your-elastic-ip << 'EOF'
    docker pull your-dockerhub/liap-tui:latest
    docker stop liap-tui || true
    docker rm liap-tui || true
    docker run -d \
      --name liap-tui \
      --restart unless-stopped \
      -p 5050:5050 \
      -v /home/ec2-user/logs:/app/logs \
      -e ENVIRONMENT=production \
      your-dockerhub/liap-tui:latest
  EOF
  ```

#### 1.4 Free Monitoring Setup
- [ ] **Local Metrics Logging**
  ```python
  # backend/monitoring.py
  import asyncio
  import json
  import psutil
  from datetime import datetime
  
  async def metrics_logger():
      """Log metrics locally (free alternative to CloudWatch)"""
      while True:
          try:
              metrics = {
                  "timestamp": datetime.utcnow().isoformat(),
                  "cpu_percent": psutil.cpu_percent(interval=1),
                  "memory_mb": psutil.virtual_memory().used / 1024 / 1024,
                  "memory_percent": psutil.virtual_memory().percent,
                  "connections": sum(len(c) for c in socket_manager.room_connections.values()),
                  "active_rooms": len(room_manager.rooms),
                  "active_games": len([r for r in room_manager.rooms.values() if r.game_started])
              }
              
              # Rotate log daily
              log_file = f"/app/logs/metrics_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
              with open(log_file, "a") as f:
                  f.write(json.dumps(metrics) + "\n")
                  
              # Alert if resources are high
              if metrics["cpu_percent"] > 80 or metrics["memory_percent"] > 85:
                  print(f"ALERT: High resource usage - CPU: {metrics['cpu_percent']}%, Memory: {metrics['memory_percent']}%")
                  
          except Exception as e:
              print(f"Metrics error: {e}")
              
          await asyncio.sleep(60)  # Log every minute
  
  # Add to your app startup
  asyncio.create_task(metrics_logger())
  ```

- [ ] **Simple Monitoring Dashboard**
  ```python
  # backend/api/routes/monitoring.py
  @router.get("/metrics/dashboard")
  async def metrics_dashboard():
      """Simple HTML dashboard for metrics"""
      return HTMLResponse("""
      <html>
      <head>
          <title>Liap Tui Metrics</title>
          <meta http-equiv="refresh" content="30">
      </head>
      <body>
          <h1>Game Metrics</h1>
          <div id="metrics"></div>
          <script>
              fetch('/api/health/detailed')
                  .then(r => r.json())
                  .then(data => {
                      document.getElementById('metrics').innerHTML = `
                          <p>CPU: ${data.resources.cpu_percent}%</p>
                          <p>Memory: ${data.resources.memory_percent}%</p>
                          <p>Active Games: ${data.game_stats.active_games}</p>
                          <p>Connections: ${data.game_stats.active_connections}</p>
                      `;
                  });
          </script>
      </body>
      </html>
      """)
  ```

---

## Phase 2: Growing Player Base ($41/month)

### When to Upgrade
- CPU consistently >70%
- Memory usage >80%
- 80+ concurrent players
- Response time >100ms
- Daily active games >100

### Architecture (100-500 concurrent players)
```
┌─────────────────────────────────────┐
│       CloudFlare CDN (Free)         │
└────────────────┬────────────────────┘
                 │
┌────────────────┴────────────────────┐
│      Application Load Balancer      │
│         ($16/month)                 │
│    (Sticky Sessions Enabled)        │
└────────────────┬────────────────────┘
                 │
      ┌──────────┴──────────┐
      │                     │
┌─────┴──────┐        ┌────┴───────┐
│  EC2 #1    │        │   EC2 #2   │
│ t3.micro   │        │  t3.micro  │
│ ($7.50/mo) │        │ ($7.50/mo) │
└────────────┘        └────────────┘

Note: Each instance manages its own rooms.
Players stick to one instance per session.
```

### Implementation Changes

#### 2.1 Sticky Session Configuration
```yaml
# ALB Target Group settings
TargetGroupAttributes:
  - Key: stickiness.enabled
    Value: "true"
  - Key: stickiness.type  
    Value: "app_cookie"
  - Key: stickiness.app_cookie.cookie_name
    Value: "LIAPTUI_INSTANCE"
  - Key: stickiness.app_cookie.duration_seconds
    Value: "86400"  # 24 hours
```

#### 2.2 Instance Identification
```python
# backend/api/main.py
import os
import socket

# Add instance ID to responses
INSTANCE_ID = os.getenv("INSTANCE_ID", socket.gethostname()[:8])

@app.middleware("http")
async def add_instance_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Instance-ID"] = INSTANCE_ID
    return response
```

#### 2.3 Simple Auto-Scaling
```json
{
  "AutoScalingGroup": {
    "MinSize": 1,
    "MaxSize": 4,
    "DesiredCapacity": 2,
    "TargetGroupARNs": ["${ALB_TARGET_GROUP_ARN}"],
    "HealthCheckType": "ELB",
    "HealthCheckGracePeriod": 300,
    "Metrics": [
      {
        "MetricName": "CPUUtilization",
        "TargetValue": 70
      }
    ]
  }
}
```

---

## Phase 3: Shared State Architecture ($77/month)

### When to Upgrade
- Need room discovery across instances
- Want zero-downtime deployments
- 500+ concurrent players
- Revenue justifies extra complexity

### Architecture Changes
```
Add:
┌──────────────┐
│ ElastiCache  │
│    Redis     │
│  ($12/mo)    │
└──────────────┘

Used for:
- Room discovery
- Game state backup  
- Deployment coordination
```

### Implementation
```python
# backend/adapters/redis_manager.py
import redis
import json
from typing import Optional

class RedisManager:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.instance_id = os.getenv("INSTANCE_ID", socket.gethostname())
    
    def register_room(self, room_id: str, room_summary: dict):
        """Register room for cross-instance discovery"""
        self.redis.hset(
            "rooms",
            room_id,
            json.dumps({
                **room_summary,
                "instance_id": self.instance_id,
                "updated_at": datetime.utcnow().isoformat()
            })
        )
        self.redis.expire(f"rooms", 3600)  # 1 hour TTL
    
    def get_all_rooms(self) -> list:
        """Get rooms from all instances"""
        rooms = []
        for room_data in self.redis.hvals("rooms"):
            room = json.loads(room_data)
            # Skip stale rooms
            updated = datetime.fromisoformat(room["updated_at"])
            if datetime.utcnow() - updated < timedelta(minutes=5):
                rooms.append(room)
        return rooms
    
    def backup_game_state(self, room_id: str, game_state: dict):
        """Backup active game for recovery"""
        self.redis.setex(
            f"game_backup:{room_id}",
            300,  # 5 minute TTL
            json.dumps(game_state)
        )
```

---

## Cost Optimization Tips

### 1. Use AWS Free Tier (First Year)
- 750 hours t2.micro EC2 (enough for 1 instance)
- 750 hours Elastic Load Balancer
- 15GB data transfer
- **Save ~$30/month first year**

### 2. Reserved Instances (After 6 months)
- 1-year reserved: Save 30%
- 3-year reserved: Save 50%
- Convertible reserved: Flexibility to change instance types

### 3. Scheduled Scaling
```python
# Scale down during quiet hours (2 AM - 10 AM)
{
  "ScheduledActions": [
    {
      "ScheduledActionName": "ScaleDown",
      "Schedule": "cron(0 2 * * ? *)",
      "MinSize": 1,
      "DesiredCapacity": 1
    },
    {
      "ScheduledActionName": "ScaleUp",
      "Schedule": "cron(0 10 * * ? *)",
      "MinSize": 2,
      "DesiredCapacity": 2
    }
  ]
}
```

### 4. CloudFlare Optimization
- Cache all static assets (JS, CSS, images)
- Enable Brotli compression
- Use CloudFlare Workers for simple API caching (free tier: 100k requests/day)

### 5. Alternative Providers
If AWS is too expensive:
- **Hetzner Cloud**: €4.51/month (~$5) per server
- **DigitalOcean**: $6/month droplets
- **Vultr**: $6/month instances
- **Oracle Cloud**: Free tier includes 4 OCPU ARM instance

---

## Deployment Checklist

### Before Going Live
- [ ] Implement graceful shutdown
- [ ] Add health endpoints
- [ ] Set up basic monitoring
- [ ] Test with 10 concurrent games
- [ ] Document deployment process
- [ ] Set up CloudFlare
- [ ] Configure backups

### Launch Day
- [ ] Deploy to single t3.small
- [ ] Monitor resources closely
- [ ] Have scaling plan ready
- [ ] Watch for memory leaks
- [ ] Track player feedback

### First Week
- [ ] Analyze peak usage times
- [ ] Identify performance bottlenecks  
- [ ] Plan scaling triggers
- [ ] Optimize Docker image size
- [ ] Review costs daily

---

## Troubleshooting Guide

### High Memory Usage
```python
# Add periodic cleanup
async def cleanup_abandoned_rooms():
    """Remove empty/abandoned rooms"""
    while True:
        current_time = datetime.utcnow()
        rooms_to_remove = []
        
        for room_id, room in room_manager.rooms.items():
            # Remove if empty for 5 minutes
            if len(room.players) == 0:
                if not hasattr(room, '_empty_since'):
                    room._empty_since = current_time
                elif (current_time - room._empty_since).seconds > 300:
                    rooms_to_remove.append(room_id)
            else:
                room._empty_since = None
        
        for room_id in rooms_to_remove:
            del room_manager.rooms[room_id]
            
        await asyncio.sleep(60)  # Check every minute
```

### Connection Leaks
```python
# Add connection timeout
async def connection_healthcheck():
    """Remove dead connections"""
    while True:
        for room_id, connections in list(socket_manager.room_connections.items()):
            for ws in list(connections):
                try:
                    # Send ping
                    await ws.send_json({"event": "ping"})
                except:
                    # Remove dead connection
                    await socket_manager.unregister(room_id, ws)
        
        await asyncio.sleep(30)  # Every 30 seconds
```

### Deployment Issues
1. **Always backup first**: `docker exec liap-tui python -c "print(room_manager.list_rooms())"`
2. **Test health endpoint**: `curl http://localhost:5050/api/health`
3. **Check logs**: `docker logs liap-tui --tail 100`
4. **Monitor connections**: Watch active WebSocket count during deployment

---

## Summary

This budget-optimized plan lets you:
1. **Start at $20/month** with room for 100 concurrent players
2. **Scale to $41/month** when you need high availability  
3. **Add shared state at $77/month** for true horizontal scaling

The key is starting simple and scaling based on actual usage, not hypothetical requirements. Your game's in-memory architecture is perfect for Phase 1, and you can add complexity only when player growth justifies it.