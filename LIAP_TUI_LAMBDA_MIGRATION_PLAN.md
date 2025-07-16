# Liap Tui Lambda Migration Plan
## Real-Time Multiplayer Game on Serverless Architecture

### Executive Summary
This plan outlines the migration of Liap Tui, a **WebSocket-based real-time multiplayer board game**, from EC2 to AWS Lambda. The key challenge is maintaining persistent WebSocket connections and game state in a serverless environment.

---

## Current Architecture Analysis

### What We Have:
- **FastAPI Backend** with WebSocket-first architecture
- **Real-time multiplayer** with 4 players per room
- **Stateful game sessions** with complex state machine
- **In-memory room/game management**
- **Event sourcing** for game history
- **No database** - all state is in-memory
- **Single Docker container** deployment

### Key Challenges for Lambda:
1. **WebSocket Connections**: Lambda doesn't maintain persistent connections
2. **Game State**: In-memory state doesn't work with Lambda's ephemeral nature
3. **Room Management**: Requires persistent storage across invocations
4. **Real-time Updates**: Need to broadcast to all players in a room

---

## Recommended Architecture: Hybrid Approach

### Why Not Pure Lambda?
- **WebSocket Limitations**: API Gateway WebSockets + Lambda = connection management overhead
- **State Management**: Would require DynamoDB for every state change (expensive & complex)
- **Latency**: Real-time games need sub-100ms responses
- **Cost**: Persistent connections via Lambda can be more expensive than EC2

### Optimal Solution: **ECS Fargate + Lambda**
```
┌─────────────────────────────────────────────────────────┐
│                   CloudFront CDN                         │
│                 (Static Assets Only)                     │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────┐
│                  Application Load Balancer               │
├─────────────────────────┬───────────────────────────────┤
│     WebSocket/Game      │          REST API             │
│    (ECS Fargate)        │     (Lambda Functions)        │
└─────────────────────────┴───────────────────────────────┘
         │                              │
         │                              │
    ┌────┴─────┐                 ┌─────┴──────┐
    │   ECS    │                 │   Lambda   │
    │ Fargate  │                 │ Functions  │
    │          │                 │            │
    │ Game     │                 │ - Health   │
    │ State    │                 │ - Stats    │
    │ Rooms    │                 │ - Metrics  │
    │ WebSocket│                 │ - Admin    │
    └──────────┘                 └────────────┘
         │                              │
         └──────────────┬───────────────┘
                        │
                 ┌──────┴──────┐
                 │  ElastiCache │
                 │   (Redis)    │
                 │              │
                 │ Shared State │
                 └──────────────┘
```

---

## Migration Strategy

### Phase 1: Prepare for Stateless Operations (Week 1-2)

#### 1.1 Externalize Game State
```python
# backend/adapters/redis_adapter.py
import redis.asyncio as redis
import json
from typing import Optional, Dict, Any

class RedisGameStateAdapter:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
    
    async def save_room(self, room_id: str, room_data: Dict[str, Any]):
        """Save room state to Redis with TTL"""
        await self.redis.setex(
            f"room:{room_id}",
            3600,  # 1 hour TTL
            json.dumps(room_data)
        )
    
    async def get_room(self, room_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve room state from Redis"""
        data = await self.redis.get(f"room:{room_id}")
        return json.loads(data) if data else None
    
    async def save_game_state(self, room_id: str, game_state: Dict[str, Any]):
        """Save game state machine data"""
        await self.redis.setex(
            f"game:{room_id}",
            3600,
            json.dumps(game_state)
        )
    
    async def publish_event(self, room_id: str, event: Dict[str, Any]):
        """Publish game events for real-time updates"""
        await self.redis.publish(
            f"room_events:{room_id}",
            json.dumps(event)
        )
```

#### 1.2 Update Room Manager
```python
# backend/room_manager.py
class RoomManager:
    def __init__(self, state_adapter: RedisGameStateAdapter):
        self.state_adapter = state_adapter
        self._local_cache = {}  # Keep local cache for performance
    
    async def create_room(self, room_id: str, host_name: str) -> Room:
        room = Room(room_id, host_name)
        await self.state_adapter.save_room(room_id, room.to_dict())
        self._local_cache[room_id] = room
        return room
    
    async def get_room(self, room_id: str) -> Optional[Room]:
        # Check local cache first
        if room_id in self._local_cache:
            return self._local_cache[room_id]
        
        # Fallback to Redis
        room_data = await self.state_adapter.get_room(room_id)
        if room_data:
            room = Room.from_dict(room_data)
            self._local_cache[room_id] = room
            return room
        return None
```

### Phase 2: Split REST API to Lambda (Week 3)

#### 2.1 Lambda Functions for Stateless Operations
```yaml
# serverless.yml
service: liap-tui-api

provider:
  name: aws
  runtime: python3.11
  environment:
    REDIS_URL: ${env:REDIS_URL}

functions:
  health:
    handler: src.lambdas.health.handler
    events:
      - http:
          path: /api/health
          method: GET
          cors: true
  
  healthDetailed:
    handler: src.lambdas.health.detailed_handler
    events:
      - http:
          path: /api/health/detailed
          method: GET
          cors: true
  
  systemStats:
    handler: src.lambdas.stats.system_handler
    events:
      - http:
          path: /api/system/stats
          method: GET
          cors: true
  
  roomStats:
    handler: src.lambdas.stats.room_handler
    events:
      - http:
          path: /api/debug/room-stats
          method: GET
          cors: true
    environment:
      REDIS_URL: ${env:REDIS_URL}
  
  eventStore:
    handler: src.lambdas.events.get_events_handler
    events:
      - http:
          path: /api/rooms/{room_id}/events
          method: GET
          cors: true

plugins:
  - serverless-python-requirements

custom:
  pythonRequirements:
    dockerizePip: true
    layer: true  # Create a Lambda Layer with dependencies
```

#### 2.2 Lambda Handler Example
```python
# src/lambdas/health.py
import json
from datetime import datetime
import os

def handler(event, context):
    """Basic health check endpoint"""
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps({
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "liap-tui-api",
            "version": os.environ.get("VERSION", "1.0.0")
        })
    }

# src/lambdas/stats.py
import json
import redis.asyncio as redis
import asyncio

def room_handler(event, context):
    """Get room statistics from Redis"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def get_stats():
        r = redis.from_url(os.environ["REDIS_URL"])
        
        # Get all room keys
        room_keys = await r.keys("room:*")
        rooms = []
        
        for key in room_keys:
            room_data = await r.get(key)
            if room_data:
                rooms.append(json.loads(room_data))
        
        await r.close()
        return {
            "total_rooms": len(rooms),
            "active_games": sum(1 for r in rooms if r.get("game_started")),
            "total_players": sum(len(r.get("players", [])) for r in rooms),
            "rooms": rooms
        }
    
    stats = loop.run_until_complete(get_stats())
    
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(stats)
    }
```

### Phase 3: Containerize WebSocket Service (Week 4)

#### 3.1 Optimized Dockerfile for Fargate
```dockerfile
# Dockerfile.fargate
FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

# Copy only WebSocket-related code
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY backend/engine ./backend/engine
COPY backend/api/routes/ws.py ./backend/api/routes/ws.py
COPY backend/socket_manager.py ./backend/socket_manager.py
COPY backend/room_manager.py ./backend/room_manager.py
COPY backend/shared_instances.py ./backend/shared_instances.py

ENV PYTHONPATH=/app
ENV WEBSOCKET_ONLY=true

# Health check for ALB
HEALTHCHECK --interval=30s --timeout=3s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

EXPOSE 8000

CMD ["uvicorn", "backend.websocket_app:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 3.2 WebSocket-Only App
```python
# backend/websocket_app.py
from fastapi import FastAPI
from backend.api.routes.ws import router as ws_router
from backend.adapters.redis_adapter import RedisGameStateAdapter
import os

app = FastAPI(title="Liap Tui WebSocket Service")

# Initialize Redis adapter
redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
state_adapter = RedisGameStateAdapter(redis_url)

# Update shared instances
from backend.shared_instances import shared_room_manager
shared_room_manager.state_adapter = state_adapter

# Mount WebSocket routes
app.include_router(ws_router)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "websocket"}
```

### Phase 4: Deploy Hybrid Architecture (Week 5)

#### 4.1 Terraform Configuration
```hcl
# infrastructure/terraform/main.tf

# ElastiCache Redis for shared state
resource "aws_elasticache_replication_group" "game_state" {
  replication_group_id = "liap-tui-game-state"
  description          = "Redis cluster for game state"
  engine              = "redis"
  node_type           = "cache.t3.micro"
  number_cache_clusters = 2
  automatic_failover_enabled = true
  
  subnet_group_name = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.redis.id]
}

# ECS Fargate for WebSocket service
resource "aws_ecs_service" "websocket" {
  name            = "liap-tui-websocket"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.websocket.arn
  desired_count   = 2
  launch_type     = "FARGATE"
  
  network_configuration {
    subnets         = aws_subnet.private[*].id
    security_groups = [aws_security_group.websocket.id]
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.websocket.arn
    container_name   = "websocket"
    container_port   = 8000
  }
  
  # Auto-scaling
  lifecycle {
    ignore_changes = [desired_count]
  }
}

# Auto-scaling for WebSocket service
resource "aws_appautoscaling_target" "websocket" {
  max_capacity       = 10
  min_capacity       = 2
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.websocket.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "websocket_cpu" {
  name               = "websocket-cpu-scaling"
  scaling_target_id  = aws_appautoscaling_target.websocket.id
  policy_type        = "TargetTrackingScaling"
  
  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 70.0
  }
}
```

#### 4.2 ALB Configuration for Mixed Traffic
```hcl
# ALB with path-based routing
resource "aws_lb_listener_rule" "api_lambda" {
  listener_arn = aws_lb_listener.main.arn
  priority     = 100
  
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.lambda.arn
  }
  
  condition {
    path_pattern {
      values = ["/api/*"]
    }
  }
  
  # Exclude WebSocket paths
  condition {
    path_pattern {
      values = ["/api/*"]
    }
  }
  
  condition {
    http_header {
      http_header_name = "Upgrade"
      values          = [""]
    }
  }
}

resource "aws_lb_listener_rule" "websocket" {
  listener_arn = aws_lb_listener.main.arn
  priority     = 50
  
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.websocket.arn
  }
  
  # WebSocket upgrade requests
  condition {
    http_header {
      http_header_name = "Upgrade"
      values          = ["websocket"]
    }
  }
}
```

### Phase 5: Testing & Migration (Week 6)

#### 5.1 Load Testing Script
```python
# tests/load_test_hybrid.py
import asyncio
import websockets
import aiohttp
import time
import statistics

async def test_websocket_latency(url, num_messages=100):
    """Test WebSocket message latency"""
    latencies = []
    
    async with websockets.connect(url) as ws:
        for i in range(num_messages):
            start = time.time()
            await ws.send(json.dumps({
                "event": "ping",
                "data": {"timestamp": start}
            }))
            response = await ws.recv()
            latencies.append((time.time() - start) * 1000)  # ms
    
    return {
        "avg_latency": statistics.mean(latencies),
        "p99_latency": statistics.quantiles(latencies, n=100)[98],
        "max_latency": max(latencies)
    }

async def test_api_latency(url, num_requests=100):
    """Test REST API latency via Lambda"""
    latencies = []
    
    async with aiohttp.ClientSession() as session:
        for i in range(num_requests):
            start = time.time()
            async with session.get(f"{url}/api/health") as resp:
                await resp.json()
                latencies.append((time.time() - start) * 1000)
    
    return {
        "avg_latency": statistics.mean(latencies),
        "p99_latency": statistics.quantiles(latencies, n=100)[98],
        "max_latency": max(latencies)
    }
```

---

## Cost Analysis

### Current EC2 Setup (Estimated Monthly)
- **EC2 t3.medium** (2 instances): ~$60
- **ALB**: ~$16
- **Data Transfer**: ~$20
- **Total**: ~$96/month

### Hybrid Architecture (Estimated Monthly)
- **Fargate** (2 tasks, 0.5 vCPU, 1GB): ~$36
- **Lambda** (1M requests, 128MB, 100ms avg): ~$2
- **ElastiCache** (t3.micro, multi-AZ): ~$24
- **ALB**: ~$16
- **Data Transfer**: ~$20
- **Total**: ~$98/month

### Benefits Despite Similar Cost:
1. **Auto-scaling**: Handle 10x traffic spikes automatically
2. **High Availability**: Multi-AZ by default
3. **Operational Simplicity**: No EC2 management
4. **Better Performance**: Redis faster than in-memory for multi-instance
5. **Partial Serverless**: REST API fully serverless

---

## Migration Timeline

### Week 1-2: State Externalization
- Implement Redis adapter
- Update room/game managers
- Test with local Redis

### Week 3: Lambda Functions
- Deploy REST endpoints to Lambda
- Keep WebSocket on EC2
- Test hybrid local setup

### Week 4: Containerize WebSocket
- Create Fargate-optimized container
- Test WebSocket service isolation
- Implement health checks

### Week 5: Deploy Infrastructure
- Provision ElastiCache
- Deploy ECS Fargate service
- Deploy Lambda functions
- Configure ALB routing

### Week 6: Migration & Testing
- Load test hybrid architecture
- Migrate traffic gradually (10% → 50% → 100%)
- Monitor performance metrics
- Optimize and tune

---

## Why This Approach?

### ✅ Pros:
1. **Maintains WebSocket Performance**: Real-time game needs low latency
2. **Leverages Serverless Where Possible**: REST API on Lambda
3. **Shared State**: Redis enables horizontal scaling
4. **Cost Neutral**: Similar cost but better architecture
5. **Future Proof**: Can scale WebSocket containers independently

### ❌ What We're NOT Doing:
1. **Pure Lambda**: Too complex for stateful WebSocket games
2. **DynamoDB for Game State**: Too slow for real-time updates
3. **API Gateway WebSockets**: Adds complexity and latency

---

## Alternative: Full Lambda (Not Recommended)

If you absolutely must use pure Lambda:

1. **API Gateway WebSockets** → Lambda handlers
2. **DynamoDB** for all state (expensive at scale)
3. **SQS** for game events
4. **Step Functions** for game state machine
5. **EventBridge** for broadcasting

**Problems**:
- Complex connection management
- Higher latency (100-300ms per action)
- Much higher cost at scale
- Poor developer experience

---

## Conclusion

The hybrid approach (ECS Fargate + Lambda) provides the best balance of:
- **Performance** for real-time gameplay
- **Scalability** for traffic spikes  
- **Cost efficiency** 
- **Operational simplicity**
- **Gradual migration path**

This architecture maintains the excellent WebSocket performance needed for real-time multiplayer games while leveraging serverless where it makes sense.