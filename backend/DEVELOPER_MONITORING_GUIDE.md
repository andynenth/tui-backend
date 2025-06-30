# 🛠️ Developer Guide: Accessing Monitoring Information

## **Quick Reference: How Developers Get Monitoring Data**

### **1. 📡 Real-Time System Health**

#### **Basic Health Check**
```bash
curl http://localhost:5050/api/health
```
**Use Case:** Load balancer checks, quick "is it alive?" verification

#### **Detailed System Status**  
```bash
curl http://localhost:5050/api/health/detailed | jq .
```
**Use Case:** Debugging performance issues, capacity planning

#### **Prometheus Metrics**
```bash
curl http://localhost:5050/api/health/metrics
```
**Use Case:** Grafana dashboards, automated monitoring

### **2. 🔍 Log Analysis (When LOG_TO_FILES=true)**

#### **Live Error Monitoring**
```bash
tail -f logs/errors.log | jq .
```
**Shows:** Real-time errors with full context

#### **Performance Bottlenecks**
```bash
jq 'select(.duration_ms > 500)' logs/performance.log
```
**Shows:** All operations taking longer than 500ms

#### **Player Session Issues**
```bash
grep '"player_id": "Alice"' logs/game_events.log | jq .
```
**Shows:** Complete history for specific player

## **🎯 Real-World Developer Scenarios**

### **Scenario 1: "Game is Running Slow"**

**Step 1: Check System Health**
```bash
curl localhost:5050/api/health/detailed | jq '.health.metrics'
```
*What you see:*
```json
{
  "memory": {"status": "warning", "value": 87.2},
  "cpu": {"status": "healthy", "value": 45.3},
  "database": {"status": "healthy", "response_ms": 156}
}
```
*Diagnosis:* High memory usage (87.2% > 85% threshold)

**Step 2: Find Performance Issues**
```bash
jq 'select(.duration_ms > 1000)' logs/performance.log | tail -5
```
*What you see:*
```json
{"operation": "get_game_state", "duration_ms": 1250, "room_id": "ROOM123"}
{"operation": "broadcast_message", "duration_ms": 1100, "room_id": "ROOM456"}
```
*Diagnosis:* Slow database queries and message broadcasting

**Step 3: Check if Recovery Happened**
```bash
grep '"procedure"' logs/game_events.log | tail -3
```
*What you see:*
```json
{"procedure": "memory_pressure", "success": true, "connections_removed": 15}
```
*Diagnosis:* System automatically cleaned up stale connections

### **Scenario 2: "Player Can't Connect"**

**Step 1: Find Player's Connection Attempts**
```bash
grep '"player_id": "Bob"' logs/websocket.log | jq .
```
*What you see:*
```json
{"event_type": "connection_attempt", "player_id": "Bob", "success": false, "error": "room_full"}
{"event_type": "connection_attempt", "player_id": "Bob", "success": false, "error": "timeout"}
```

**Step 2: Check Room Status**
```bash
grep '"room_id": "ROOM789"' logs/game_events.log | tail -5
```
*What you see:*
```json
{"event_type": "room_full", "room_id": "ROOM789", "players": 4}
{"event_type": "connection_timeout", "room_id": "ROOM789", "duration_ms": 5000}
```

**Step 3: Trace Complete Operation**
```bash
grep '"correlation_id": "req_abc123"' logs/* | sort
```
*What you see:* Complete flow from connection attempt to failure

### **Scenario 3: "Memory Leak Suspected"**

**Step 1: Memory Trend Analysis**
```bash
grep memory_percent logs/performance.log | jq '.memory_percent' | tail -20
```
*What you see:*
```
67.2
68.1
69.3
70.5
...
85.2
87.1
```
*Diagnosis:* Gradual memory increase over time

**Step 2: Check Recovery Actions**
```bash
jq 'select(.procedure == "memory_pressure")' logs/game_events.log
```
*What you see:*
```json
{"procedure": "memory_pressure", "success": true, "memory_before": 91.2, "memory_after": 68.5}
```

## **🚨 Automated Alerting for Developers**

### **Slack Integration Example**
```bash
#!/bin/bash
# monitor_health.sh - Run every 5 minutes via cron

HEALTH=$(curl -s localhost:5050/api/health/detailed)
STATUS=$(echo $HEALTH | jq -r '.health.overall_status')

if [ "$STATUS" != "healthy" ]; then
    MESSAGE="🚨 Liap Tui Health Alert: $STATUS"
    DETAILS=$(echo $HEALTH | jq '.health.metrics')
    
    curl -X POST -H 'Content-type: application/json' \
         --data "{\"text\":\"$MESSAGE\",\"attachments\":[{\"text\":\"$DETAILS\"}]}" \
         $SLACK_WEBHOOK_URL
fi
```

### **Discord Bot Integration**
```python
import asyncio
import aiohttp
import json

async def check_game_health():
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:5050/api/health/detailed') as resp:
            health = await resp.json()
            
            if health['health']['overall_status'] != 'healthy':
                await send_discord_alert(health)

async def send_discord_alert(health_data):
    # Send formatted health data to Discord channel
    pass
```

## **📊 Dashboard Setup Examples**

### **Grafana Dashboard Queries**

**System Health Panel:**
```promql
# Memory usage over time
liap_memory_usage_percent

# Active players
liap_websocket_connections_total

# Response time 95th percentile
histogram_quantile(0.95, rate(liap_response_time_ms_bucket[5m]))
```

**Game Analytics Panel:**
```promql
# Games per hour
increase(liap_rooms_total[1h])

# Average game duration
avg(liap_game_duration_minutes)

# Error rate
rate(liap_errors_total[5m])
```

### **ELK Stack Queries**

**Kibana Searches:**
```json
{
  "query": {
    "bool": {
      "must": [
        {"range": {"@timestamp": {"gte": "now-1h"}}},
        {"term": {"level": "ERROR"}}
      ]
    }
  }
}
```

## **🔧 Developer Debugging Workflow**

### **Production Issue Investigation**

**1. First Response (2 minutes)**
```bash
# Quick health check
curl localhost:5050/api/health

# Recent errors
tail -20 logs/errors.log | jq .

# System status
curl localhost:5050/api/health/detailed | jq '.health.overall_status'
```

**2. Deep Dive (10 minutes)**
```bash
# Error analysis
jq 'select(.level == "ERROR")' logs/errors.log | tail -10

# Performance issues
jq 'select(.duration_ms > 1000)' logs/performance.log | tail -10

# Resource usage
grep memory_percent logs/performance.log | tail -5
```

**3. Root Cause Analysis (30 minutes)**
```bash
# Trace specific user issue
grep '"player_id": "affected_user"' logs/* | sort

# Find correlated events
grep '"correlation_id": "problem_request"' logs/* | sort

# Check recovery attempts
jq 'select(.procedure)' logs/game_events.log | tail -5
```

### **Daily Health Monitoring**

**Morning Check Script:**
```bash
#!/bin/bash
echo "🌅 Daily Liap Tui Health Report"
echo "================================"

# Overall status
STATUS=$(curl -s localhost:5050/api/health | jq -r '.status')
echo "Overall Status: $STATUS"

# Error count (last 24h)
ERROR_COUNT=$(grep "$(date -d yesterday '+%Y-%m-%d')" logs/errors.log | wc -l)
echo "Errors (24h): $ERROR_COUNT"

# Performance summary
AVG_RESPONSE=$(jq '.duration_ms' logs/performance.log | tail -100 | awk '{sum+=$1} END {print sum/NR}')
echo "Avg Response Time: ${AVG_RESPONSE}ms"

# Active games
ACTIVE_GAMES=$(curl -s localhost:5050/api/health/metrics | grep liap_active_games_total | awk '{print $2}')
echo "Active Games: $ACTIVE_GAMES"
```

## **🎯 Summary: Developer Information Access**

| **Information Type** | **Access Method** | **Use Case** |
|---------------------|-------------------|--------------|
| **Real-time Health** | HTTP APIs | Load balancer checks, quick status |
| **Historical Performance** | Log file queries | Trend analysis, capacity planning |
| **Error Investigation** | Structured log search | Bug fixing, root cause analysis |
| **User Sessions** | Correlation ID tracing | Customer support, UX issues |
| **System Recovery** | Recovery procedure logs | Automated fix verification |
| **Metrics & KPIs** | Prometheus endpoints | Dashboards, alerting |

**Bottom Line:** Developers get complete visibility through:
- **Immediate feedback** via HTTP health endpoints
- **Historical analysis** via structured JSON logs  
- **Proactive alerts** via monitoring tool integration
- **Complete request tracing** via correlation IDs
- **Automatic diagnosis** via recovery procedure logs

The system tells developers exactly what's happening, when it happened, and what actions were taken to fix it automatically! 🚀