# Production Join Issue Investigation Guide (V2)

## Overview

This guide provides comprehensive instructions for gathering data when concurrent join issues occur in production. It's designed to work with the existing EventStore V2 database schema and infrastructure.

## Quick Response Checklist

When an issue is reported:

1. **Capture Timestamp**: Note exact time of issue (UTC)
2. **Identify Room**: Get room_id where issue occurred
3. **Collect Player Info**: Names of affected players
4. **Export Events**: Query game_events_v2 table for the time window
5. **Check Logs**: Extract JOIN_TRACE logs if available

## Data Collection Using Existing Infrastructure

### 1. Enhanced Logging for Join Operations

Add these log points to capture join race conditions without changing the database:

```python
# In AsyncRoom.join_room()
async def join_room(self, player_name: str) -> dict:
    join_start = time.time()
    
    # Log entry with timestamp
    logger.info(f"JOIN_TRACE [{self.room_id}] Enter: player={player_name}, "
                f"time={join_start:.6f}, current_slots={[p.name if p else None for p in self.players]}")
    
    # Track if we're waiting for lock
    lock_wait_start = time.time()
    
    async with self._join_lock:
        lock_acquired_time = time.time()
        lock_wait_ms = (lock_acquired_time - lock_wait_start) * 1000
        
        # Log when lock acquired
        logger.info(f"JOIN_TRACE [{self.room_id}] Lock acquired: player={player_name}, "
                    f"wait_ms={lock_wait_ms:.1f}")
        
        # ... existing join logic ...
        
        # Before returning, store join attempt event
        join_end = time.time()
        total_ms = (join_end - join_start) * 1000
        
        # Store in existing event store
        await event_store.store_event(
            self.room_id,
            "join_attempt",
            {
                "player_name": player_name,
                "success": result.get('success', False),
                "error_type": result.get('error_type'),
                "slot": result.get('slot'),
                "lock_wait_ms": lock_wait_ms,
                "total_ms": total_ms,
                "room_state": {
                    "player_count": len([p for p in self.players if p]),
                    "human_count": len([p for p in self.players if p and not p.is_bot])
                }
            },
            player_id=player_name
        )
        
    # Log exit
    logger.info(f"JOIN_TRACE [{self.room_id}] Exit: player={player_name}, "
                f"result={result['success']}, total_ms={total_ms:.1f}")
    
    return result
```

### 2. Query Existing Database for Join Issues

The current schema (game_events_v2) already supports investigation queries:

```sql
-- Find all join attempts for a room in a time window
SELECT 
    id,
    room_id,
    event_type,
    timestamp,
    player_id,
    json_extract(payload, '$.success') as success,
    json_extract(payload, '$.error_type') as error_type,
    json_extract(payload, '$.lock_wait_ms') as lock_wait_ms,
    json_extract(payload, '$.total_ms') as total_ms
FROM game_events_v2
WHERE room_id = 'ROOM_ID_HERE'
  AND event_type = 'join_attempt'
  AND timestamp BETWEEN ? AND ?
ORDER BY timestamp;

-- Detect concurrent joins (within 1 second window)
WITH join_windows AS (
    SELECT 
        room_id,
        player_id,
        timestamp,
        LAG(timestamp) OVER (PARTITION BY room_id ORDER BY timestamp) as prev_timestamp,
        json_extract(payload, '$.success') as success
    FROM game_events_v2
    WHERE event_type = 'join_attempt'
      AND timestamp > unixepoch('now') - 3600  -- Last hour
)
SELECT 
    room_id,
    COUNT(*) as concurrent_attempts,
    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
    MIN(timestamp - prev_timestamp) as min_gap_seconds
FROM join_windows
WHERE timestamp - prev_timestamp < 1.0  -- Within 1 second
GROUP BY room_id
HAVING COUNT(*) > 3;  -- At least 4 rapid attempts

-- Failed joins analysis
SELECT 
    json_extract(payload, '$.error_type') as error_type,
    COUNT(*) as count,
    AVG(json_extract(payload, '$.lock_wait_ms')) as avg_lock_wait_ms
FROM game_events_v2
WHERE event_type = 'join_attempt'
  AND json_extract(payload, '$.success') = 0
  AND timestamp > unixepoch('now') - 3600
GROUP BY error_type
ORDER BY count DESC;
```

### 3. Add Join-Specific Event Types

Extend the existing event store with join-specific events:

```python
# Add to SemanticEventType enum
class SemanticEventType(Enum):
    # ... existing types ...
    JOIN_ATTEMPT = "join_attempt"
    JOIN_LOCK_ACQUIRED = "join_lock_acquired"
    JOIN_SUCCESS = "join_success"
    JOIN_FAILED = "join_failed"
    JOIN_CONCURRENT = "join_concurrent"  # Multiple joins detected
```

### 4. Production Monitoring Using Existing Tools

#### A. Log Aggregation (CloudWatch/ELK)

Create log filters for JOIN_TRACE:

```bash
# CloudWatch Insights query
fields @timestamp, @message
| filter @message like /JOIN_TRACE/
| parse @message /JOIN_TRACE \[(?<room_id>[^\]]+)\] (?<action>\w+): player=(?<player>[^,]+)/
| stats count(*) as attempts, 
        sum(action = "Lock acquired") as locks_acquired,
        avg(lock_wait_ms) as avg_lock_wait
by room_id
| sort attempts desc
```

#### B. Real-time Alerting

Add to existing health monitoring:

```python
# In health_monitor.py
async def check_join_health(self) -> Dict[str, Any]:
    """Monitor join operation health"""
    
    # Query recent join attempts
    cursor = self.conn.execute("""
        SELECT 
            COUNT(*) as total_attempts,
            SUM(CASE WHEN json_extract(payload, '$.success') = 1 THEN 1 ELSE 0 END) as successful,
            AVG(json_extract(payload, '$.lock_wait_ms')) as avg_lock_wait_ms,
            MAX(json_extract(payload, '$.lock_wait_ms')) as max_lock_wait_ms
        FROM game_events_v2
        WHERE event_type = 'join_attempt'
          AND timestamp > unixepoch('now') - 300  -- Last 5 minutes
    """)
    
    stats = cursor.fetchone()
    
    # Define thresholds
    health = {
        'total_attempts': stats[0] or 0,
        'success_rate': (stats[1] / stats[0] * 100) if stats[0] > 0 else 100,
        'avg_lock_wait_ms': stats[2] or 0,
        'max_lock_wait_ms': stats[3] or 0,
        'status': 'healthy'
    }
    
    # Check thresholds
    if health['max_lock_wait_ms'] > 3000:  # 3 second lock wait
        health['status'] = 'degraded'
        health['alert'] = 'High lock contention detected'
    
    if health['success_rate'] < 80:
        health['status'] = 'unhealthy'
        health['alert'] = 'Low join success rate'
    
    return health
```

### 5. Debugging Tools

#### A. Join Timeline Visualizer

```python
async def visualize_join_timeline(room_id: str, start_time: float, end_time: float):
    """Create visual timeline of join attempts"""
    
    events = await event_store.get_events_by_type(
        room_id, 
        "join_attempt",
        start_time,
        end_time
    )
    
    # Create timeline
    timeline = []
    for event in events:
        timeline.append({
            'time': event['timestamp'],
            'player': event['player_id'],
            'success': event['payload'].get('success'),
            'duration_ms': event['payload'].get('total_ms'),
            'lock_wait_ms': event['payload'].get('lock_wait_ms')
        })
    
    # Sort by time
    timeline.sort(key=lambda x: x['time'])
    
    # Print visual representation
    print(f"Join Timeline for Room {room_id}")
    print("=" * 80)
    
    for i, event in enumerate(timeline):
        t = datetime.fromtimestamp(event['time'])
        status = "✓" if event['success'] else "✗"
        wait = event['lock_wait_ms'] or 0
        
        # Visual bar for wait time
        bar = "█" * int(wait / 100)  # Each block = 100ms
        
        print(f"{t.strftime('%H:%M:%S.%f')[:-3]} {status} {event['player']:15} "
              f"Wait: {wait:6.1f}ms {bar}")
```

#### B. Concurrent Join Detector

```python
async def detect_concurrent_joins(time_window: int = 3600) -> List[Dict]:
    """Detect rooms with concurrent join issues"""
    
    query = """
    WITH join_pairs AS (
        SELECT 
            e1.room_id,
            e1.player_id as player1,
            e2.player_id as player2,
            e1.timestamp as t1,
            e2.timestamp as t2,
            ABS(e1.timestamp - e2.timestamp) as time_diff,
            json_extract(e1.payload, '$.success') as p1_success,
            json_extract(e2.payload, '$.success') as p2_success
        FROM game_events_v2 e1
        JOIN game_events_v2 e2 
          ON e1.room_id = e2.room_id 
          AND e1.id < e2.id
          AND ABS(e1.timestamp - e2.timestamp) < 0.5  -- Within 500ms
        WHERE e1.event_type = 'join_attempt'
          AND e2.event_type = 'join_attempt'
          AND e1.timestamp > unixepoch('now') - ?
    )
    SELECT 
        room_id,
        COUNT(*) as concurrent_pairs,
        MIN(time_diff) as min_gap_seconds,
        SUM(CASE WHEN p1_success = 1 AND p2_success = 1 THEN 1 ELSE 0 END) as both_succeeded
    FROM join_pairs
    GROUP BY room_id
    ORDER BY concurrent_pairs DESC
    """
    
    cursor = event_store.conn.execute(query, (time_window,))
    return [dict(row) for row in cursor.fetchall()]
```

### 6. Emergency Response Procedures

#### A. Enable Detailed Join Logging

```python
# Add to room manager
class RoomManager:
    def __init__(self):
        self.detailed_join_logging = False
        
    async def enable_join_debugging(self, room_id: str = None):
        """Enable detailed join logging for debugging"""
        self.detailed_join_logging = True
        logger.setLevel(logging.DEBUG)
        
        if room_id:
            logger.info(f"JOIN_DEBUG: Enabled for room {room_id}")
            # Start monitoring specific room
            asyncio.create_task(self.monitor_room_joins(room_id))
    
    async def monitor_room_joins(self, room_id: str):
        """Monitor joins for a specific room"""
        while self.detailed_join_logging:
            # Check for concurrent joins
            recent = await detect_concurrent_joins_for_room(room_id, 60)
            if recent:
                logger.warning(f"JOIN_DEBUG: Concurrent joins detected: {recent}")
            
            await asyncio.sleep(5)
```

#### B. Join Rate Limiter (Emergency)

```python
class JoinRateLimiter:
    """Emergency rate limiter for join operations"""
    
    def __init__(self, max_joins_per_second: int = 10):
        self.max_joins_per_second = max_joins_per_second
        self.join_times = defaultdict(deque)
    
    async def check_rate_limit(self, room_id: str, player_name: str) -> bool:
        """Check if join should be rate limited"""
        now = time.time()
        
        # Clean old entries
        self.join_times[room_id] = deque(
            t for t in self.join_times[room_id] 
            if now - t < 1.0
        )
        
        # Check rate
        if len(self.join_times[room_id]) >= self.max_joins_per_second:
            logger.warning(f"JOIN_RATELIMIT: Room {room_id} hit rate limit")
            
            # Store rate limit event
            await event_store.store_event(
                room_id,
                "join_rate_limited",
                {
                    "player_name": player_name,
                    "current_rate": len(self.join_times[room_id]),
                    "limit": self.max_joins_per_second
                },
                player_id=player_name
            )
            return False
        
        # Record this attempt
        self.join_times[room_id].append(now)
        return True
```

### 7. Investigation SQL Queries

```sql
-- Complete join investigation report
WITH join_stats AS (
    SELECT 
        room_id,
        COUNT(*) as total_attempts,
        COUNT(DISTINCT player_id) as unique_players,
        SUM(CASE WHEN json_extract(payload, '$.success') = 1 THEN 1 ELSE 0 END) as successful,
        AVG(json_extract(payload, '$.lock_wait_ms')) as avg_lock_wait,
        MAX(json_extract(payload, '$.lock_wait_ms')) as max_lock_wait,
        MIN(timestamp) as first_attempt,
        MAX(timestamp) as last_attempt
    FROM game_events_v2
    WHERE event_type = 'join_attempt'
      AND room_id = ?
      AND timestamp BETWEEN ? AND ?
    GROUP BY room_id
)
SELECT 
    *,
    (last_attempt - first_attempt) as duration_seconds,
    CASE 
        WHEN total_attempts > 10 AND duration_seconds < 5 THEN 'JOIN_STORM'
        WHEN max_lock_wait > 3000 THEN 'HIGH_CONTENTION'
        WHEN successful < total_attempts * 0.8 THEN 'HIGH_FAILURE_RATE'
        ELSE 'NORMAL'
    END as diagnosis
FROM join_stats;
```

## Data Export for Analysis

```bash
# Export join events for a specific time window
sqlite3 game_events.db <<EOF
.mode csv
.headers on
.output join_investigation_$(date +%Y%m%d_%H%M%S).csv
SELECT 
    datetime(timestamp, 'unixepoch') as time,
    room_id,
    player_id,
    json_extract(payload, '$.success') as success,
    json_extract(payload, '$.error_type') as error_type,
    json_extract(payload, '$.slot') as slot,
    json_extract(payload, '$.lock_wait_ms') as lock_wait_ms,
    json_extract(payload, '$.total_ms') as total_ms
FROM game_events_v2
WHERE event_type = 'join_attempt'
  AND timestamp BETWEEN unixepoch('2024-01-01 12:00:00') AND unixepoch('2024-01-01 13:00:00')
ORDER BY timestamp;
EOF
```

## Summary

This guide leverages the existing EventStore V2 infrastructure to investigate join issues without requiring database schema changes. Key points:

1. **Uses existing tables**: All data stored in game_events_v2 with JSON payload
2. **Minimal code changes**: Only adds logging and event storage
3. **SQL-based analysis**: Leverages SQLite's JSON functions
4. **Production-ready**: Can be deployed immediately
5. **Backward compatible**: Works with existing monitoring tools

The approach provides comprehensive investigation capabilities while maintaining system stability.