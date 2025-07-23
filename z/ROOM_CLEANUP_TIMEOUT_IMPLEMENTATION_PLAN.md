# Room Cleanup Timeout Implementation Plan

## Problem Statement
Currently, when all human players disconnect from a game room (e.g., during page navigation), the room might be cleaned up too aggressively, preventing players from reconnecting. The system needs a smarter cleanup mechanism that distinguishes between temporary disconnections (page navigation) and truly abandoned games.

## System Design Philosophy
- **Bot Conversion**: When players disconnect, they're temporarily converted to bots to keep the game running
- **Reconnection Support**: Players can reconnect and resume control from bots
- **Resource Management**: Games with no human players should eventually be terminated to save resources
- **Timeout Mechanism**: A configurable timeout before cleanup (0 for testing, 30+ seconds for production)

## Current System Behavior
1. Player disconnects → Converted to bot (`is_bot = True`, `original_is_bot` preserves original state)
2. Player reconnects → Converted back to human (`is_bot = False`)
3. During page navigation: Disconnect → Navigate → Reconnect happens within milliseconds
4. Problem: Aggressive cleanup might delete room before reconnection completes

## Proposed Solution: Timeout-Based Cleanup

### Architecture Overview
```
Player Disconnects
    ↓
Check if any humans remain
    ↓
If no humans → Mark room for cleanup (set timer)
    ↓
Background task checks timers periodically
    ↓
If timeout exceeded → Clean up room
If human reconnects → Cancel cleanup
```

### Implementation Details

#### 1. Room Class Modifications (`backend/engine/room.py`)

```python
class Room:
    # Add class constant
    CLEANUP_TIMEOUT_SECONDS = 0  # 0 for testing, 30+ for production
    
    def __init__(self, room_id: str, host_name: str):
        # ... existing code ...
        self.last_human_disconnect_time = None  # When last human left
        self.cleanup_scheduled = False  # Flag to prevent duplicate scheduling
    
    def mark_for_cleanup(self):
        """Mark room for cleanup after all humans disconnect"""
        if not self.has_any_human_players():
            self.last_human_disconnect_time = time.time()
            self.cleanup_scheduled = True
            logger.info(f"Room {self.room_id} marked for cleanup")
    
    def cancel_cleanup(self):
        """Cancel pending cleanup when human reconnects"""
        self.last_human_disconnect_time = None
        self.cleanup_scheduled = False
        logger.info(f"Room {self.room_id} cleanup cancelled")
    
    def should_cleanup(self) -> bool:
        """Check if room should be cleaned up based on timeout"""
        if not self.cleanup_scheduled or self.last_human_disconnect_time is None:
            return False
        
        elapsed = time.time() - self.last_human_disconnect_time
        return elapsed >= self.CLEANUP_TIMEOUT_SECONDS
```

#### 2. WebSocket Disconnect Handler (`backend/api/routes/ws.py`)

```python
async def handle_disconnect(room_id: str, websocket: WebSocket):
    # ... existing disconnect logic ...
    
    # After converting player to bot
    if player and not player.is_bot:
        player.is_bot = True
        # ... existing code ...
        
        # Check if this was the last human
        if not room.has_any_human_players():
            room.mark_for_cleanup()
            logger.info(f"All players in room {room_id} are now bots. Cleanup scheduled in {Room.CLEANUP_TIMEOUT_SECONDS}s")
```

#### 3. WebSocket Reconnection Handler (`backend/api/routes/ws.py`)

```python
# In client_ready handler
if player and player.is_bot and not player.original_is_bot:
    # Human player reconnecting
    player.is_bot = False
    player.is_connected = True
    
    # Cancel any pending cleanup
    room.cancel_cleanup()
    
    logger.info(f"Player {player_name} reconnected, cleanup cancelled for room {room_id}")
```

#### 4. Background Cleanup Task (`backend/api/routes/ws.py` or new cleanup module)

```python
async def room_cleanup_task():
    """Background task to clean up abandoned rooms"""
    while True:
        try:
            rooms_to_cleanup = []
            
            # Check all rooms
            for room_id, room in room_manager.get_all_rooms().items():
                if room.should_cleanup():
                    rooms_to_cleanup.append(room_id)
            
            # Clean up rooms
            for room_id in rooms_to_cleanup:
                room = room_manager.get_room(room_id)
                if room and room.should_cleanup():  # Double-check
                    logger.info(f"Cleaning up abandoned room {room_id}")
                    
                    # Unregister from bot manager
                    bot_manager.unregister_game(room_id)
                    
                    # Broadcast room closed
                    await broadcast(room_id, "room_closed", {
                        "reason": "All players disconnected",
                        "timeout_seconds": Room.CLEANUP_TIMEOUT_SECONDS
                    })
                    
                    # Delete room
                    room_manager.delete_room(room_id)
                    
                    logger.info(f"Room {room_id} cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error in room cleanup task: {e}")
        
        # Run every 5 seconds
        await asyncio.sleep(5)

# Start the cleanup task when the server starts
asyncio.create_task(room_cleanup_task())
```

### Configuration Options

1. **CLEANUP_TIMEOUT_SECONDS**:
   - `0`: Immediate cleanup (for testing)
   - `30`: 30-second grace period (recommended for production)
   - `300`: 5-minute grace period (for slow connections)

2. **Cleanup Check Interval**: How often the background task runs (default: 5 seconds)

### Testing Plan

1. **Test with timeout=0**:
   - All humans disconnect → Room cleaned up immediately
   - Verify bots stop playing
   - Verify room is removed from room list

2. **Test with timeout=30**:
   - All humans disconnect → Room marked for cleanup
   - Reconnect within 30s → Cleanup cancelled, game continues
   - Wait 30s without reconnecting → Room cleaned up

3. **Test page navigation**:
   - Start game → Navigate to game page
   - Verify room is NOT cleaned up during navigation
   - Verify players reconnect successfully

### Logging Strategy

Add comprehensive logging to track:
- When rooms are marked for cleanup
- When cleanup is cancelled due to reconnection
- When cleanup actually occurs
- Any errors during cleanup process

Example log flow:
```
🔌 Player Andy disconnected from room ABC123
🔍 Converting Andy to bot
🔍 All players in room ABC123 are now bots. Cleanup scheduled in 30s
... (20 seconds later) ...
🔗 Player Andy reconnected to room ABC123
✅ Cleanup cancelled for room ABC123
```

### Benefits

1. **Prevents Premature Cleanup**: Page navigation won't trigger room deletion
2. **Cleans Abandoned Games**: Truly abandoned games are eventually removed
3. **Configurable**: Timeout can be adjusted based on needs
4. **Resource Efficient**: No permanent bot-only games consuming resources
5. **User-Friendly**: Players have time to reconnect after disconnections

### Migration Notes

- The `original_is_bot` field already exists in Player class
- The `has_any_human_players()` method is already implemented
- Only need to add timeout tracking and background cleanup task

### Future Enhancements

1. **Per-Room Timeouts**: Different timeout values for different room types
2. **Warning Notifications**: Warn remaining bots before cleanup
3. **Cleanup Statistics**: Track how many rooms are cleaned up and why
4. **Reconnection Grace Period**: Extend timeout if reconnection attempt detected