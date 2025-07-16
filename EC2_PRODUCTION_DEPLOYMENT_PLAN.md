# Liap Tui EC2 Production Deployment Plan
## WebSocket Multiplayer Game on AWS EC2

### Executive Summary
This plan focuses on deploying the Liap Tui real-time multiplayer board game on AWS EC2 with production-ready architecture, monitoring, auto-scaling, and high availability.

---

## Current State Analysis

### What We Have:
- **Single Docker container** with both backend and static frontend
- **WebSocket-first architecture** for real-time gameplay
- **In-memory state management** (rooms, games, players)
- **No database** - all state is ephemeral
- **Local development setup** with docker-compose

### Production Requirements:
- High availability (multiple availability zones)
- Auto-scaling for traffic spikes
- Zero-downtime deployments
- Monitoring and alerting
- Backup and disaster recovery
- Security best practices

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   Route 53 (DNS)                         │
│                 (liap-tui.yourdomain.com)               │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────┐
│                   CloudFront CDN                         │
│              (Static assets caching only)                │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────┐
│              Application Load Balancer                   │
│          (WebSocket sticky sessions enabled)             │
└─────────────────────────┬───────────────────────────────┘
                          │
        ┌─────────────────┴─────────────────┐
        │                                   │
┌───────┴────────┐                 ┌───────┴────────┐
│  Auto Scaling  │                 │  Auto Scaling  │
│   Group (AZ1)  │                 │   Group (AZ2)  │
├────────────────┤                 ├────────────────┤
│ EC2 Instance 1 │                 │ EC2 Instance 3 │
│ EC2 Instance 2 │                 │ EC2 Instance 4 │
└────────────────┘                 └────────────────┘
        │                                   │
        └─────────────────┬─────────────────┘
                          │
                   ┌──────┴──────┐
                   │  ElastiCache │
                   │   (Redis)    │
                   │              │
                   │ Shared State │
                   └──────────────┘
```

---

## Phase 1: State Externalization (Week 1)

Since WebSocket connections are sticky to specific EC2 instances, we need shared state for:
- Room discovery (which rooms exist)
- Player tracking (which players are in which rooms)
- Game state backup (for recovery)

### 1.1 Add Redis for Shared State

```python
# backend/adapters/redis_state.py
import redis
import json
from typing import Optional, Dict, List

class RedisStateAdapter:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.pubsub = self.redis.pubsub()
    
    # Room Registry (for room discovery)
    def register_room(self, room_id: str, instance_id: str, room_data: dict):
        """Register room with instance ownership"""
        self.redis.hset("rooms", room_id, json.dumps({
            "instance_id": instance_id,
            "created_at": datetime.utcnow().isoformat(),
            **room_data
        }))
        self.redis.expire(f"rooms:{room_id}", 3600)  # 1 hour TTL
    
    def get_all_rooms(self) -> List[dict]:
        """Get all active rooms across instances"""
        rooms = []
        for room_id, data in self.redis.hgetall("rooms").items():
            rooms.append(json.loads(data))
        return rooms
    
    # State Backup (for recovery)
    def backup_game_state(self, room_id: str, game_state: dict):
        """Backup game state for recovery"""
        self.redis.setex(
            f"game_state:{room_id}",
            300,  # 5 minute TTL
            json.dumps(game_state)
        )
    
    # Cross-instance messaging
    def publish_room_event(self, event_type: str, data: dict):
        """Publish events for cross-instance coordination"""
        self.redis.publish("room_events", json.dumps({
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }))
```

### 1.2 Update Application

```python
# backend/shared_instances.py
import os
from adapters.redis_state import RedisStateAdapter

# Add Redis adapter
redis_url = os.getenv("REDIS_URL")
if redis_url:
    redis_state = RedisStateAdapter(redis_url)
else:
    redis_state = None  # Fallback for local dev

# Instance identification
INSTANCE_ID = os.getenv("INSTANCE_ID", socket.gethostname())
```

---

## Phase 2: EC2 Configuration (Week 2)

### 2.1 Optimized EC2 Setup

```bash
# User data script for EC2 instances
#!/bin/bash
# Install Docker
amazon-linux-extras install docker -y
service docker start
usermod -a -G docker ec2-user

# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
rpm -U ./amazon-cloudwatch-agent.rpm

# Configure CloudWatch
cat > /opt/aws/amazon-cloudwatch-agent/etc/config.json << EOF
{
  "metrics": {
    "namespace": "LiapTui",
    "metrics_collected": {
      "cpu": {
        "measurement": ["cpu_usage_idle", "cpu_usage_iowait"],
        "metrics_collection_interval": 60
      },
      "disk": {
        "measurement": ["used_percent"],
        "metrics_collection_interval": 60,
        "resources": ["*"]
      },
      "mem": {
        "measurement": ["mem_used_percent"],
        "metrics_collection_interval": 60
      }
    }
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/liap-tui/app.log",
            "log_group_name": "liap-tui-app",
            "log_stream_name": "{instance_id}"
          }
        ]
      }
    }
  }
}
EOF

# Start CloudWatch agent
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
    -a fetch-config -m ec2 -s -c file:/opt/aws/amazon-cloudwatch-agent/etc/config.json

# Pull and run application
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_REPO
docker pull $ECR_REPO:latest
docker run -d \
  --name liap-tui \
  --restart unless-stopped \
  -p 5050:5050 \
  -e REDIS_URL=$REDIS_URL \
  -e INSTANCE_ID=$(ec2-metadata --instance-id | cut -d " " -f 2) \
  -e ENV=production \
  -v /var/log/liap-tui:/app/logs \
  $ECR_REPO:latest
```

### 2.2 Auto Scaling Configuration

```json
{
  "AutoScalingGroupName": "liap-tui-asg",
  "MinSize": 2,
  "MaxSize": 10,
  "DesiredCapacity": 4,
  "HealthCheckType": "ELB",
  "HealthCheckGracePeriod": 300,
  "TargetGroupARNs": ["arn:aws:elasticloadbalancing:..."],
  "MetricsCollection": [
    {
      "Granularity": "1Minute",
      "Metrics": ["GroupDesiredCapacity", "GroupInServiceInstances"]
    }
  ]
}
```

### 2.3 Scaling Policies

```json
{
  "ScaleUpPolicy": {
    "MetricType": "ALBRequestCountPerTarget",
    "TargetValue": 1000,
    "ScaleUpCooldown": 60
  },
  "ScaleDownPolicy": {
    "MetricType": "ALBRequestCountPerTarget",
    "TargetValue": 500,
    "ScaleDownCooldown": 300
  },
  "CPUPolicy": {
    "MetricType": "CPUUtilization",
    "TargetValue": 70
  }
}
```

---

## Phase 3: Load Balancer & Networking (Week 3)

### 3.1 Application Load Balancer

```yaml
# ALB Configuration
ALB:
  Type: application
  Scheme: internet-facing
  IpAddressType: ipv4
  SecurityGroups:
    - !Ref ALBSecurityGroup
  Subnets:
    - !Ref PublicSubnet1
    - !Ref PublicSubnet2
  
TargetGroup:
  Port: 5050
  Protocol: HTTP
  HealthCheck:
    Path: /api/health
    IntervalSeconds: 30
    TimeoutSeconds: 5
    HealthyThresholdCount: 2
    UnhealthyThresholdCount: 3
  TargetGroupAttributes:
    - Key: stickiness.enabled
      Value: true
    - Key: stickiness.type
      Value: lb_cookie
    - Key: stickiness.lb_cookie.duration_seconds
      Value: 86400  # 24 hours for game sessions
```

### 3.2 Security Groups

```yaml
ALBSecurityGroup:
  Ingress:
    - Protocol: tcp
      FromPort: 80
      ToPort: 80
      CidrIp: 0.0.0.0/0
    - Protocol: tcp
      FromPort: 443
      ToPort: 443
      CidrIp: 0.0.0.0/0
  Egress:
    - Protocol: tcp
      FromPort: 5050
      ToPort: 5050
      DestinationSecurityGroup: !Ref EC2SecurityGroup

EC2SecurityGroup:
  Ingress:
    - Protocol: tcp
      FromPort: 5050
      ToPort: 5050
      SourceSecurityGroup: !Ref ALBSecurityGroup
    - Protocol: tcp
      FromPort: 22
      ToPort: 22
      CidrIp: 10.0.0.0/16  # VPC CIDR for SSH bastion
  Egress:
    - Protocol: -1
      CidrIp: 0.0.0.0/0  # Allow all outbound
```

---

## Phase 4: Deployment Pipeline (Week 4)

### 4.1 GitHub Actions CI/CD

```yaml
# .github/workflows/deploy.yml
name: Deploy to EC2

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1
      
      - name: Build and push Docker image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: liap-tui
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
      
      - name: Update Auto Scaling Group
        run: |
          # Trigger instance refresh for rolling update
          aws autoscaling start-instance-refresh \
            --auto-scaling-group-name liap-tui-asg \
            --preferences MinHealthyPercentage=90,InstanceWarmup=60
```

### 4.2 Blue-Green Deployment Option

```bash
#!/bin/bash
# blue_green_deploy.sh

# Create new launch template version
NEW_VERSION=$(aws ec2 create-launch-template-version \
  --launch-template-name liap-tui-lt \
  --source-version '$Latest' \
  --launch-template-data "{\"ImageId\":\"$NEW_AMI_ID\"}" \
  --query 'LaunchTemplateVersion.VersionNumber' \
  --output text)

# Create new ASG with new version
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name liap-tui-asg-green \
  --launch-template LaunchTemplateName=liap-tui-lt,Version=$NEW_VERSION \
  --min-size 2 \
  --max-size 10 \
  --desired-capacity 4 \
  --target-group-arns $TARGET_GROUP_ARN

# Wait for instances to be healthy
aws autoscaling wait describe-auto-scaling-groups \
  --auto-scaling-group-names liap-tui-asg-green \
  --query 'AutoScalingGroups[0].Instances[?HealthStatus==`Healthy`]' \
  --output text

# Switch traffic (update ALB target group)
# Monitor for issues
# If good, terminate old ASG
# If bad, revert target group
```

---

## Phase 5: Monitoring & Observability (Week 5)

### 5.1 CloudWatch Dashboard

```json
{
  "DashboardName": "LiapTui-Production",
  "DashboardBody": {
    "widgets": [
      {
        "type": "metric",
        "properties": {
          "metrics": [
            ["AWS/ApplicationELB", "ActiveConnectionCount"],
            ["AWS/ApplicationELB", "RequestCount"],
            ["AWS/EC2", "CPUUtilization", {"stat": "Average"}],
            ["CWAgent", "mem_used_percent", {"stat": "Average"}]
          ],
          "period": 300,
          "stat": "Sum",
          "region": "us-east-1",
          "title": "System Metrics"
        }
      },
      {
        "type": "metric",
        "properties": {
          "metrics": [
            ["LiapTui", "WebSocketConnections"],
            ["LiapTui", "ActiveGames"],
            ["LiapTui", "TotalPlayers"]
          ],
          "period": 60,
          "stat": "Average",
          "region": "us-east-1",
          "title": "Game Metrics"
        }
      }
    ]
  }
}
```

### 5.2 Application Metrics

```python
# backend/api/services/metrics.py
import boto3
from datetime import datetime

cloudwatch = boto3.client('cloudwatch')

def publish_metrics():
    """Publish custom metrics to CloudWatch"""
    metrics = []
    
    # WebSocket connections
    metrics.append({
        'MetricName': 'WebSocketConnections',
        'Value': len(socket_manager.connections),
        'Unit': 'Count',
        'Timestamp': datetime.utcnow()
    })
    
    # Active games
    metrics.append({
        'MetricName': 'ActiveGames',
        'Value': len([r for r in room_manager.rooms.values() if r.game_started]),
        'Unit': 'Count',
        'Timestamp': datetime.utcnow()
    })
    
    # Total players
    total_players = sum(len(r.players) for r in room_manager.rooms.values())
    metrics.append({
        'MetricName': 'TotalPlayers',
        'Value': total_players,
        'Unit': 'Count',
        'Timestamp': datetime.utcnow()
    })
    
    # Publish to CloudWatch
    cloudwatch.put_metric_data(
        Namespace='LiapTui',
        MetricData=metrics
    )

# Run every 60 seconds
async def metrics_loop():
    while True:
        try:
            publish_metrics()
        except Exception as e:
            logger.error(f"Failed to publish metrics: {e}")
        await asyncio.sleep(60)
```

### 5.3 Alarms

```yaml
Alarms:
  HighErrorRate:
    MetricName: 5XXError
    Statistic: Sum
    Period: 300
    EvaluationPeriods: 2
    Threshold: 10
    AlarmActions:
      - !Ref SNSTopic
  
  HighCPU:
    MetricName: CPUUtilization
    Statistic: Average
    Period: 300
    EvaluationPeriods: 2
    Threshold: 80
    AlarmActions:
      - !Ref ScaleUpPolicy
  
  WebSocketConnections:
    MetricName: WebSocketConnections
    Statistic: Sum
    Period: 60
    EvaluationPeriods: 3
    Threshold: 10000
    AlarmActions:
      - !Ref SNSTopic
```

---

## Phase 6: Production Hardening (Week 6)

### 6.1 Performance Optimization

```python
# backend/optimizations.py

# 1. Connection pooling for Redis
from redis import ConnectionPool

redis_pool = ConnectionPool(
    host='redis.example.com',
    port=6379,
    max_connections=50,
    decode_responses=True
)

# 2. Async task batching
async def batch_broadcast(messages):
    """Batch multiple broadcasts together"""
    tasks = []
    for room_id, message in messages:
        tasks.append(broadcast(room_id, message))
    await asyncio.gather(*tasks)

# 3. Memory optimization
import gc

async def cleanup_loop():
    """Periodic cleanup of finished games"""
    while True:
        # Remove finished games older than 1 hour
        current_time = datetime.utcnow()
        for room_id, room in list(room_manager.rooms.items()):
            if room.game_ended and (current_time - room.ended_at).seconds > 3600:
                await room_manager.remove_room(room_id)
        
        # Force garbage collection
        gc.collect()
        await asyncio.sleep(300)  # Every 5 minutes
```

### 6.2 Security Hardening

```yaml
# WAF Rules
WebACLRules:
  RateLimitRule:
    Priority: 1
    Statement:
      RateBasedStatement:
        Limit: 2000  # requests per 5 minutes per IP
        AggregateKeyType: IP
    Action:
      Block: {}
  
  GeoBlockRule:
    Priority: 2
    Statement:
      NotStatement:
        Statement:
          GeoMatchStatement:
            CountryCodes: [US, CA, GB, AU]  # Allowed countries
    Action:
      Block: {}
```

### 6.3 Backup and Recovery

```python
# backend/backup.py
async def backup_active_games():
    """Backup active game states to S3"""
    s3 = boto3.client('s3')
    
    for room_id, room in room_manager.rooms.items():
        if room.game_started and not room.game_ended:
            game_state = room.game.to_dict()
            
            # Upload to S3
            s3.put_object(
                Bucket='liap-tui-backups',
                Key=f'games/{datetime.utcnow().isoformat()}/{room_id}.json',
                Body=json.dumps(game_state),
                ServerSideEncryption='AES256'
            )

# Run every 5 minutes
asyncio.create_task(periodic_backup())
```

---

## Cost Optimization

### Estimated Monthly Costs (4 instances baseline)
- **EC2 t3.medium** (4 instances): ~$120
- **Application Load Balancer**: ~$16
- **ElastiCache t3.micro**: ~$12
- **CloudWatch Logs/Metrics**: ~$10
- **S3 Backups**: ~$1
- **Data Transfer**: ~$20
- **Total**: ~$179/month

### Cost Saving Options:
1. **Reserved Instances**: Save 30-50% with 1-year commitment
2. **Spot Instances**: Use for non-critical capacity (save 70%)
3. **Auto-scaling**: Scale down during off-peak hours
4. **CloudFront**: Reduce data transfer costs

---

## Operational Runbook

### Daily Tasks
- [ ] Check CloudWatch dashboard
- [ ] Review error logs
- [ ] Monitor active game count
- [ ] Check auto-scaling events

### Weekly Tasks
- [ ] Review performance metrics
- [ ] Analyze cost reports
- [ ] Update security patches
- [ ] Test backup recovery

### Incident Response
1. **High Error Rate**: Check logs, rollback if needed
2. **Performance Issues**: Scale up, check Redis
3. **Security Incident**: Enable WAF rules, review logs
4. **Data Loss**: Restore from S3 backups

---

## Success Criteria

### Performance
- WebSocket latency < 50ms (p95)
- API response time < 100ms (p95)
- Support 1000+ concurrent games
- 99.9% uptime

### Scalability
- Auto-scale from 2 to 10 instances
- Handle 10x traffic spikes
- Scale based on actual load

### Reliability
- Multi-AZ deployment
- Automated health checks
- Self-healing infrastructure
- Game state recovery

---

This EC2-focused plan provides a solid production deployment without the complexity of Lambda migration. The architecture is scalable, reliable, and maintains the real-time performance needed for your WebSocket-based game.