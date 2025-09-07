# Join Room Race Condition Fix Plan (V2)

## Executive Summary

The current join room implementation has a race condition where multiple players can pass the `is_full()` check simultaneously. This updated plan includes integration with the production investigation guide for monitoring the fix's effectiveness.

## Current State Analysis

### The Race Condition Still Exists

Looking at the current code (ws.py lines 624-673), the redundant checks are still present:

```python
# Check if room is full
if room.is_full():  # ← RACE CONDITION: Non-atomic check
    # send error
    continue

# Check if room has started  
if room.started:   # ← RACE CONDITION: Non-atomic check
    # send error
    continue

# Try to join the room
assigned_slot = await room.join_room(player_name)  # ← Lock acquired here
```

The fix hasn't been implemented yet.

## Updated Solution Design

### Core Changes Required

1. **Remove redundant checks** in ws.py (lines 624-647)
2. **Enhance AsyncRoom.join_room()** to return structured response
3. **Add investigation logging** per PRODUCTION_JOIN_INVESTIGATION_GUIDE_V2.md
4. **Store join events** in existing EventStore V2

### Phase 1: Enhanced AsyncRoom with Logging

**File**: `backend/engine/async_room.py`

```python
async def join_room(self, player_name: str) -> dict:
    """
    Allow a player to join the room asynchronously.
    Thread-safe with all validation inside the lock.
    
    Returns:
        dict: Structured response with success/failure details
    """
    join_start = time.time()
    
    # Log entry (per investigation guide)
    logger.info(f"JOIN_TRACE [{self.room_id}] Enter: player={player_name}, "
                f"time={join_start:.6f}, current_slots={[p.name if p else None for p in self.players]}")
    
    # Track lock wait time
    lock_wait_start = time.time()
    
    async with self._join_lock:
        lock_acquired_time = time.time()
        lock_wait_ms = (lock_acquired_time - lock_wait_start) * 1000
        
        logger.info(f"JOIN_TRACE [{self.room_id}] Lock acquired: player={player_name}, "
                    f"wait_ms={lock_wait_ms:.1f}")
        
        self._last_activity = datetime.now()
        
        # Check if game already started
        if self.started:
            result = {
                'success': False,
                'error': 'Cannot join: game already started',
                'error_type': 'game_started',
                'room_state': await self._get_room_state()
            }
        
        # Check if player already in room
        elif any(p and p.name == player_name for p in self.players):
            slot = next(i for i, p in enumerate(self.players) if p and p.name == player_name)
            result = {
                'success': True,
                'slot': slot,
                'already_joined': True,
                'room_state': await self._get_room_state()
            }
        
        else:
            # Try to find a slot (empty or bot)
            slot_found = False
            
            # First try empty slots
            for i, player in enumerate(self.players):
                if player is None:
                    self.players[i] = Player(
                        player_name,
                        is_bot=False,
                        available_colors=self._get_available_colors(),
                    )
                    self._total_joins += 1
                    result = {
                        'success': True,
                        'slot': i,
                        'replaced_bot': False,
                        'room_state': await self._get_room_state()
                    }
                    slot_found = True
                    break
            
            # If no empty slot, try replacing a bot
            if not slot_found:
                for i, player in enumerate(self.players):
                    if player and player.is_bot:
                        old_bot = player.name
                        self.players[i] = Player(
                            player_name,
                            is_bot=False,
                            available_colors=self._get_available_colors(),
                        )
                        self._total_joins += 1
                        result = {
                            'success': True,
                            'slot': i,
                            'replaced_bot': True,
                            'replaced_bot_name': old_bot,
                            'room_state': await self._get_room_state()
                        }
                        slot_found = True
                        break
            
            # No slots available
            if not slot_found:
                result = {
                    'success': False,
                    'error': 'Room is full',
                    'error_type': 'room_full', 
                    'room_state': await self._get_room_state()
                }
    
    # Calculate total time
    join_end = time.time()
    total_ms = (join_end - join_start) * 1000
    
    # Log exit
    logger.info(f"JOIN_TRACE [{self.room_id}] Exit: player={player_name}, "
                f"result={result['success']}, total_ms={total_ms:.1f}")
    
    # Store event for investigation (per guide)
    from backend.shared_event_store import event_store
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
            "room_state": result.get('room_state', {})
        },
        player_id=player_name
    )
    
    return result
```

### Phase 2: Simplified WebSocket Handler

**File**: `backend/api/routes/ws.py` (lines 603-698 need updating)

```python
elif event_name == "join_room":
    # Handle room joining from lobby (using validated data)
    room_id_to_join = event_data.get("room_id")
    player_name = event_data.get("player_name")
    
    try:
        # Get the room
        room = await room_manager.get_room(room_id_to_join)
        if not room:
            await registered_ws.send_json({
                "event": "error",
                "data": {
                    "message": "Room not found",
                    "type": "room_not_found",
                }
            })
            continue
        
        # REMOVED: Redundant is_full() check (lines 624-634)
        # REMOVED: Redundant started check (lines 637-647)
        # Let join_room handle ALL validation atomically
        
        result = await room.join_room(player_name)
        
        if result['success']:
            # Send success response
            await registered_ws.send_json({
                "event": "room_joined",
                "data": {
                    "room_id": room_id_to_join,
                    "player_name": player_name,
                    "assigned_slot": result['slot'],
                    "success": True,
                    "replaced_bot": result.get('replaced_bot', False),
                    "already_joined": result.get('already_joined', False),
                }
            })
            
            # Only broadcast room update if not already joined
            if not result.get('already_joined', False):
                room_summary = await room.summary()
                await broadcast(
                    room_id_to_join,
                    "room_update",
                    {
                        "players": room_summary["players"],
                        "host_name": room_summary["host_name"],
                        "room_id": room_id_to_join,
                        "started": room_summary.get("started", False),
                        "new_player": player_name,
                        "replaced_bot": result.get('replaced_bot_name'),
                    },
                )
                
                # Update lobby
                from .routes import notify_lobby_room_updated
                await notify_lobby_room_updated(room_summary)
        else:
            # Send error response with consistent format
            await registered_ws.send_json({
                "event": "error",
                "data": {
                    "message": result['error'],
                    "type": result['error_type'],
                    "room_state": result.get('room_state', {}),
                }
            })
            
    except Exception as e:
        logger.error(f"Unexpected error in join_room: {e}")
        await registered_ws.send_json({
            "event": "error",
            "data": {
                "message": "An unexpected error occurred",
                "type": "internal_error",
            }
        })
```

### Phase 3: Integration with Production Monitoring

Add these queries to monitor the fix effectiveness:

```sql
-- Monitor join success rate after fix deployment
SELECT 
    DATE(datetime(timestamp, 'unixepoch')) as date,
    COUNT(*) as total_attempts,
    SUM(CASE WHEN json_extract(payload, '$.success') = 1 THEN 1 ELSE 0 END) as successful,
    AVG(json_extract(payload, '$.lock_wait_ms')) as avg_lock_wait_ms,
    MAX(json_extract(payload, '$.lock_wait_ms')) as max_lock_wait_ms
FROM game_events_v2
WHERE event_type = 'join_attempt'
  AND timestamp > unixepoch('DEPLOYMENT_DATE')
GROUP BY date
ORDER BY date;

-- Detect any remaining race conditions
WITH concurrent_joins AS (
    SELECT 
        e1.room_id,
        e1.timestamp as t1,
        e2.timestamp as t2,
        json_extract(e1.payload, '$.success') as p1_success,
        json_extract(e2.payload, '$.success') as p2_success,
        json_extract(e1.payload, '$.error_type') as p1_error,
        json_extract(e2.payload, '$.error_type') as p2_error
    FROM game_events_v2 e1
    JOIN game_events_v2 e2 
      ON e1.room_id = e2.room_id 
      AND e1.id < e2.id
      AND ABS(e1.timestamp - e2.timestamp) < 0.5
    WHERE e1.event_type = 'join_attempt'
      AND e2.event_type = 'join_attempt'
      AND e1.timestamp > unixepoch('DEPLOYMENT_DATE')
)
SELECT 
    room_id,
    COUNT(*) as concurrent_pairs,
    -- This should be 0 after fix
    SUM(CASE WHEN p1_success = 1 AND p2_success = 1 
             AND p1_error IS NULL AND p2_error IS NULL 
        THEN 1 ELSE 0 END) as both_succeeded_same_slot
FROM concurrent_joins
GROUP BY room_id
HAVING concurrent_pairs > 0;
```

## Testing Strategy

### 1. Unit Tests (keep existing from V1)
- Test concurrent joins respect capacity
- Test bot replacement
- Test duplicate player handling

### 2. Integration Test with Logging
```python
async def test_join_logging_integration():
    """Verify join attempts are logged correctly"""
    room = AsyncRoom("test_room", "host")
    
    # Join and verify event stored
    result = await room.join_room("Player1")
    assert result['success']
    
    # Check event was stored
    events = await event_store.get_events_by_type(
        "test_room", 
        "join_attempt"
    )
    assert len(events) == 1
    assert events[0]['payload']['player_name'] == "Player1"
    assert events[0]['payload']['lock_wait_ms'] >= 0
```

### 3. Load Test with Monitoring
```python
async def load_test_with_monitoring():
    """Simulate high concurrent load and verify no race conditions"""
    room_id = "load_test_room"
    room = AsyncRoom(room_id, "host")
    
    # 100 concurrent join attempts
    players = [f"Player{i}" for i in range(100)]
    results = await asyncio.gather(*[
        room.join_room(p) for p in players
    ])
    
    # Verify correctness
    successful = sum(1 for r in results if r['success'])
    assert successful == 4  # Room capacity
    
    # Check for race conditions in logs
    events = await event_store.get_events_by_type(room_id, "join_attempt")
    
    # No two successful joins should happen within 1ms
    # (indicating they bypassed the lock)
    for i, e1 in enumerate(events):
        for e2 in events[i+1:]:
            if (e1['payload']['success'] and 
                e2['payload']['success'] and
                abs(e1['timestamp'] - e2['timestamp']) < 0.001):
                assert False, "Race condition detected!"
```

## Deployment Plan

1. **Pre-deployment**:
   - Enable JOIN_TRACE logging in production
   - Capture baseline metrics for 24 hours

2. **Deployment**:
   - Deploy AsyncRoom changes first (backward compatible)
   - Deploy WebSocket handler changes
   - Keep investigation logging enabled

3. **Post-deployment Monitoring** (first 48 hours):
   - Watch for lock timeout alerts
   - Monitor join success rates
   - Check for "both_succeeded_same_slot" occurrences
   - Review JOIN_TRACE logs for anomalies

4. **Success Criteria**:
   - Zero "both_succeeded_same_slot" events
   - Join success rate > 95% (excluding legitimate full rooms)
   - Average lock wait time < 50ms
   - No lock timeout errors

## Rollback Plan

If issues detected:
1. Revert ws.py changes only (keep AsyncRoom enhancements)
2. Analyze stored join_attempt events
3. Review JOIN_TRACE logs
4. Fix issues and redeploy

## Key Improvements in V2

1. **Production Monitoring**: Integrated with EventStore V2 for investigation
2. **Detailed Logging**: JOIN_TRACE entries per investigation guide
3. **Event Storage**: All join attempts stored for analysis
4. **Clear Metrics**: Success criteria based on actual data
5. **Current State**: Acknowledges the fix hasn't been implemented yet

This plan ensures the fix can be safely deployed and monitored in production.