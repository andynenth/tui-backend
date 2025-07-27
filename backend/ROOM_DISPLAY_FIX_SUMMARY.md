# Room Display Fix Summary

## Problem
The frontend was showing "Waiting..." for all room slots instead of displaying the actual players and bots.

## Root Cause
Property name mismatch between backend and frontend:
- Frontend expects: `player.name`
- Backend was sending: `player.player_name`

## Fix Applied
Updated all room-related handlers in `api/adapters/room_adapters.py` to use `name` instead of `player_name`:

1. **_handle_create_room** (line 159)
2. **_handle_join_room** (line 276) 
3. **_handle_get_room_state** (line 433)
4. **_handle_add_bot** (line 521)
5. **_handle_remove_player** (line 619)

Also added `avatar_color` field to all responses for proper player display.

## Additional Fix
Updated `RoomPage.jsx` to pass `room_id` in the `get_room_state` request:
```javascript
// Before:
networkService.send(roomId, 'get_room_state', {});

// After:
networkService.send(roomId, 'get_room_state', { room_id: roomId });
```

## Result
- When a player creates a room, they should now see themselves + 3 bots
- The room display should show actual names instead of "Waiting..."
- All player information (name, is_bot, avatar_color) is properly sent to frontend

## Verification
The backend logs show:
1. Rooms are created with 4 players (1 human + 3 bots) ✅
2. Legacy sync is working correctly ✅
3. Room state includes all player data ✅

The fix ensures the frontend receives data in the expected format so it can display all players correctly.