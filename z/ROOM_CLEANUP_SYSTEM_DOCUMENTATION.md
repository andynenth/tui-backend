# Room Cleanup System Documentation

## Overview

The room cleanup system is designed to automatically remove game rooms when all human players have disconnected, preventing abandoned bot-only games from consuming server resources. The system uses a timeout-based approach with background task monitoring.

## System Architecture

### Key Components

1. **Room Cleanup State** (`backend/engine/room.py`)
   - `last_human_disconnect_time`: Timestamp when the last human player left
   - `cleanup_scheduled`: Boolean flag to prevent duplicate cleanup scheduling
   - `CLEANUP_TIMEOUT_SECONDS`: Configurable timeout (0 for testing, 30+ for production)

2. **Background Cleanup Task** (`backend/api/routes/ws.py`)
   - Async task that runs every 5 seconds
   - Checks all rooms for cleanup eligibility
   - Removes rooms that exceed the timeout threshold

3. **Startup Mechanism** (`backend/api/main.py`)
   - FastAPI startup event triggers the cleanup task
   - Fallback mechanism ensures task starts on first WebSocket connection

## How It Works

### 1. Human Player Disconnection Flow

When a human player disconnects from a game:

```python
# In ws.py handle_disconnect():
if player and not player.is_bot:
    # Convert to bot temporarily
    player.is_bot = True
    player.is_connected = False
    
    # Check if any humans remain
    room.mark_for_cleanup()
```

### 2. Room Marking for Cleanup

The `mark_for_cleanup()` method checks if any human players remain:

```python
def mark_for_cleanup(self):
    if not self.has_any_human_players():
        self.last_human_disconnect_time = time.time()
        self.cleanup_scheduled = True
```

### 3. Background Task Operation

The cleanup task runs continuously in the background:

```python
async def room_cleanup_task():
    while True:
        # Check ALL rooms (not just non-started ones)
        all_room_ids = list(room_manager.rooms.keys())
        
        for room_id in all_room_ids:
            room = room_manager.get_room(room_id)
            if room and room.should_cleanup():
                # Clean up the room
                await cleanup_room(room_id)
        
        await asyncio.sleep(5)  # Check every 5 seconds
```

### 4. Cleanup Eligibility Check

The `should_cleanup()` method determines if a room is ready for removal:

```python
def should_cleanup(self) -> bool:
    if not self.cleanup_scheduled:
        return False
    
    if self.last_human_disconnect_time is None:
        return False
    
    elapsed = time.time() - self.last_human_disconnect_time
    return elapsed >= self.CLEANUP_TIMEOUT_SECONDS
```

### 5. Human Reconnection Handling

If a human player reconnects before cleanup:

```python
# In ws.py when player reconnects:
if player.original_is_bot == False:
    player.is_bot = False
    player.is_connected = True
    room.cancel_cleanup()  # Cancels pending cleanup
```

## Configuration

### Timeout Settings

- **Testing**: `CLEANUP_TIMEOUT_SECONDS = 0` (immediate cleanup)
- **Production**: `CLEANUP_TIMEOUT_SECONDS = 30` (30-second grace period)

### Task Check Interval

- Background task checks every 5 seconds
- Can be adjusted in `room_cleanup_task()`

## Important Implementation Details

### 1. Room Discovery Issue

Initial implementation used `room_manager.list_rooms()`, which only returns non-started rooms:

```python
# ❌ WRONG - Misses started games
available_rooms = room_manager.list_rooms()

# ✅ CORRECT - Gets all rooms
all_room_ids = list(room_manager.rooms.keys())
```

### 2. Task Startup Reliability

The system includes a fallback mechanism because FastAPI startup events may not always fire:

```python
# Primary: FastAPI startup event
@app.on_event("startup")
async def startup_event():
    start_cleanup_task()

# Fallback: First WebSocket connection
async def websocket_endpoint(...):
    if not cleanup_task_started:
        start_cleanup_task()
```

### 3. Race Condition Prevention

The system uses flags to prevent multiple task instances:

```python
cleanup_task_started = False
cleanup_task = None

def start_cleanup_task():
    global cleanup_task_started, cleanup_task
    if cleanup_task_started:
        return  # Already running
    
    cleanup_task = asyncio.create_task(room_cleanup_task())
    cleanup_task_started = True
```

## Debug Logging

The system includes comprehensive debug logging:

1. **Room State Checks**: `🔍` emoji for state inspection
2. **Cleanup Operations**: `🧹` emoji for cleanup actions
3. **Cleanup Scheduling**: `🗑️` emoji for marking rooms
4. **Task Lifecycle**: `🚀` emoji for task startup

Example log sequence:
```
🔍 [Room ABC123] No human players found - all are bots!
🗑️ [Room ABC123] Marked for cleanup in 0s
🧹 [Room ABC123] should_cleanup: elapsed=0.05s, timeout=0s, should_cleanup=True
🧹 Cleaning up abandoned room ABC123
```

## Testing the System

1. **Create a game room** with human players
2. **Start the game** 
3. **Disconnect all human players** (close browser tabs)
4. **Monitor logs** to see cleanup process
5. **Verify room removal** after timeout expires

## Design Philosophy

1. **Bot Conversion**: Temporary mechanism to maintain game continuity
2. **Cleanup Timeout**: Grace period for reconnection
3. **Resource Management**: Prevent server overload from abandoned games
4. **User Experience**: Allow brief disconnections without game loss

## Future Enhancements

1. **Configurable Timeouts**: Per-room or per-game-phase timeouts
2. **Persistent Storage**: Save game state before cleanup
3. **Notification System**: Warn players before cleanup
4. **Analytics**: Track cleanup patterns and optimize timeouts
5. **Reconnection Token**: Allow rejoining with authentication