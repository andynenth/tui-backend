# Room Management System Implementation Plan

## Current System Analysis

Based on the codebase analysis, the room management system already handles pre-game disconnections correctly:

### 1. Pre-Game Disconnection Handling

#### 1.1 Host Disconnects in Lobby (`leave_room` event)
**Current Implementation** (backend/api/routes/ws.py:796-855):
- ✅ Room is closed immediately
- ✅ All players receive `room_closed` event
- ✅ Room is deleted from room_manager
- ✅ Lobby is updated with new room list

**Code Reference**:
```python
# backend/api/routes/ws.py:818-831
if is_host_leaving:
    await broadcast(room_id, "room_closed", {
        "message": f"Room closed by host {player_name}",
        "reason": "host_left"
    })
    room_manager.delete_room(room_id)
```

**Status**: ✅ Working as expected - NO CHANGES NEEDED

#### 1.2 Regular Player Disconnects in Lobby (`leave_room` event)
**Current Implementation** (backend/api/routes/ws.py:856-890):
- ✅ Player is removed from room
- ✅ Others receive `room_update` event
- ✅ Room continues to exist

**Code Reference**:
```python
# backend/api/routes/ws.py:857-873
room.exit_room(player_name)
updated_summary = room.summary()
await broadcast(room_id, "room_update", {
    "players": updated_summary["players"],
    "host_name": updated_summary["host_name"],
    "room_id": room_id,
    "started": updated_summary.get("started", False)
})
```

**Status**: ✅ Working as expected - NO CHANGES NEEDED

### 2. In-Game Disconnection Handling

#### 2.1 Current Implementation Analysis
The system already has a working disconnection handling mechanism:

**Files Involved**:
- `backend/api/routes/ws.py`: WebSocket disconnect handler
- `backend/engine/room.py`: Room cleanup logic
- `backend/engine/player.py`: Player state management

**Current Flow**:
1. Player disconnects → `handle_disconnect()` called
2. Player converted to bot temporarily (`player.is_bot = True`)
3. If all players are bots → `room.mark_for_cleanup()`
4. Background task checks every 5 seconds → `room_cleanup_task()`
5. If timeout exceeded → room deleted

### 3. Issues Found

#### Issue 1: Inconsistent Event Naming
- `leave_room` vs `leave_game` events have similar implementations
- Both check if host is leaving and close room accordingly

#### Issue 2: Missing WebSocket Cleanup on Disconnect
- Log shows warnings: "WebSocket ID not found in mapping"
- Connection manager not properly tracking disconnections

## Implementation-Ready Changes

### Phase 1: Fix WebSocket Connection Tracking ✅

**File**: `backend/api/routes/ws.py`

**Change 1**: Ensure WebSocket ID is tracked on connection
```python
# Line 151: websocket_endpoint function
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    # Generate unique ID for this websocket
    websocket._ws_id = str(uuid.uuid4())
    
    # Register with connection manager immediately
    if room_id != "lobby":
        # Track the connection even before client_ready
        await connection_manager.track_connection(room_id, websocket._ws_id)
```

**Change 2**: Clean up connection on disconnect
```python
# Line 147: handle_disconnect function
async def handle_disconnect(room_id: str, websocket: WebSocket):
    try:
        websocket_id = getattr(websocket, '_ws_id', None)
        if websocket_id:
            # Always try to clean up the connection
            await connection_manager.remove_connection(websocket_id)
```

### Phase 2: Consolidate Event Handling ❌ (Not Needed)

After analysis, `leave_room` and `leave_game` serve different purposes:
- `leave_room`: Pre-game lobby exit
- `leave_game`: In-game exit (future enhancement)

**Recommendation**: Keep both events separate for future extensibility

### Phase 3: Enhance Room Cleanup Configuration ✅

**File**: `backend/engine/room.py`

**Change**: Make cleanup timeout configurable
```python
# Line 27: Add configuration
import os

class Room:
    # Get timeout from environment variable, default to 30 seconds
    CLEANUP_TIMEOUT_SECONDS = int(os.getenv('ROOM_CLEANUP_TIMEOUT', '30'))
```

**File**: `.env` (create if not exists)
```
ROOM_CLEANUP_TIMEOUT=30
```

### Phase 4: Add Cleanup Logging ✅

**File**: `backend/api/routes/ws.py`

**Change**: Add minimal logging for production monitoring
```python
# Line 1477: In room_cleanup_task
if room and room.should_cleanup():
    logger.info(f"Cleaning up abandoned room {room_id}")
    # ... existing cleanup code ...
    logger.info(f"Room {room_id} cleaned up successfully")
```

## Testing Checklist

### Pre-Game Disconnection Tests
- [ ] Host leaves room → Room deleted, all players notified
- [ ] Regular player leaves → Room updated, continues to exist
- [ ] Multiple players leave → Room state stays consistent

### In-Game Disconnection Tests
- [ ] Single player disconnects → Bot takes over
- [ ] All players disconnect → Room cleaned up after timeout
- [ ] Player reconnects before cleanup → Cleanup cancelled

### Edge Cases
- [ ] Rapid connect/disconnect cycles
- [ ] Network interruption vs explicit leave
- [ ] Multiple rooms with same scenarios

## Deployment Steps

1. **Update Environment Variables**
   ```bash
   echo "ROOM_CLEANUP_TIMEOUT=30" >> .env
   ```

2. **Apply Code Changes**
   - Fix WebSocket tracking in `ws.py`
   - Add environment variable support in `room.py`

3. **Test in Development**
   ```bash
   ./start.sh
   # Run through testing checklist
   ```

4. **Monitor Logs**
   - Check for "WebSocket ID not found" warnings
   - Verify cleanup messages appear

## Summary

The room management system is already well-implemented and handles the specified scenarios correctly:

✅ **Host disconnects in lobby** → Room closes (WORKING)
✅ **Regular player disconnects in lobby** → Room continues (WORKING)
✅ **In-game disconnections** → Bot replacement + cleanup (WORKING)

**Minimal changes needed**:
1. Fix WebSocket connection tracking to eliminate warnings
2. Make cleanup timeout configurable via environment variable
3. Keep existing event structure (leave_room vs leave_game)

The system is production-ready with these minor enhancements.