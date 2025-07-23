# Async Architecture Integration Plan

## Current Status
The async implementation exists but needs minor fixes. The files are:
- `backend/engine/async_room_manager.py` - AsyncRoomManager class (complete)
- `backend/engine/async_room.py` - AsyncRoom class (imports sync Game)
- `backend/engine/async_game.py` - AsyncGame class (inherits from Game)
- `backend/engine/state_machine/async_game_adapter.py` - Adapter for sync/async bridge

## Specific Issues Found
1. **AsyncRoom.py line 14**: Imports `from .game import Game` instead of `from .async_game import AsyncGame`
2. **AsyncRoom.py line 39**: Type hint uses `Optional[Game]` instead of `Optional[AsyncGame]`
3. **AsyncRoom.py line 256**: Creates `Game(self.players)` instead of `AsyncGame(self.players)`
4. **WebSocket handlers**: All room_manager method calls need await added

## Integration Steps Required

### Step 1: Fix AsyncRoom to use AsyncGame (3 lines to change)
```python
# Line 14: Change import
from .game import Game  → from .async_game import AsyncGame

# Line 39: Update type hint
self.game: Optional[Game] = None  → self.game: Optional[AsyncGame] = None

# Line 256: Use AsyncGame constructor
self.game = Game(self.players)  → self.game = AsyncGame(self.players)
```

### Step 2: Update WebSocket Handler Calls (35 locations)
In `backend/api/routes/ws.py`, add await to all room_manager calls:
- **1x** `room_manager.create_room(player_name)` → `await room_manager.create_room(player_name)`
- **23x** `room_manager.get_room(room_id)` → `await room_manager.get_room(room_id)`
- **7x** `room_manager.list_rooms()` → `await room_manager.list_rooms()`
- **3x** `room_manager.delete_room(room_id)` → `await room_manager.delete_room(room_id)`
- **1x** `room_manager.rooms` → This property access needs special handling

### Step 3: Update Room Method Calls
- Room methods that need await:
  - `join_room_safe()` → Already async (no change needed)
  - `start_game_safe()` → Already async (no change needed)
  - Other room methods may need async versions

### Step 4: Test Async Integration
- Create test script to verify async operations work
- Test concurrent room operations
- Verify async locks prevent race conditions

## Why Async Architecture Matters
1. **Concurrent Operations**: Multiple rooms can process actions simultaneously
2. **Better Performance**: Non-blocking I/O for database operations (future)
3. **Thread Safety**: Async locks prevent race conditions in game state
4. **Scalability**: Can handle more concurrent players

## Example Code Changes

### Before (Sync):
```python
# In ws.py
room = room_manager.get_room(room_id)
if room:
    result = await room.join_room_safe(player_name)
```

### After (Async):
```python
# In ws.py
room = await room_manager.get_room(room_id)
if room:
    result = await room.join_room_safe(player_name)
```

## Risk Assessment
- **Low Risk**: Only 4 lines need changing in async_room.py
- **Medium Risk**: 35 locations in ws.py need await added
- **Main Challenge**: Ensuring all await chains are properly connected
- **Rollback Plan**: Can revert to sync RoomManager if issues arise

## Testing Approach
1. Make the 3 changes to async_room.py first
2. Update shared_instances.py to use AsyncRoomManager
3. Add await to room_manager calls one at a time
4. Test basic operations: create room, join room, start game
5. Test concurrent operations with multiple rooms