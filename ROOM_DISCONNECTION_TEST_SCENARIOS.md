# Room Disconnection Test Scenarios

## How to Monitor Debug Logs

Start the application and monitor the logs for messages with these prefixes:
- 🔌 `[ROOM_DEBUG]` - WebSocket connection/disconnection events
- 📤 `[ROOM_DEBUG]` - Room event handling (leave_room, leave_game)
- 👤 `[ROOM_DEBUG]` - Player status changes
- 📊 `[ROOM_DEBUG]` - Room state snapshots
- 🗑️ `[ROOM_DEBUG]` - Room cleanup events
- 🧹 `[ROOM_DEBUG]` - Cleanup task iterations
- 🎮 `[ROOM_DEBUG]` - Game-related disconnections

## Pre-Game Disconnection Scenarios

### Test 1: Host Disconnects in Lobby
**Steps:**
1. Host creates a room
2. 1-2 other players join the room
3. Host clicks "Leave Room" or closes browser

**Expected Logs:**
```
📤 [ROOM_DEBUG] Received 'leave_room' event for room 'ABC123'
📊 [ROOM_DEBUG] Room state before leave: players=[...], host=HostName, started=false
👤 [ROOM_DEBUG] Player 'HostName' leaving room 'ABC123', is_host=true
🗑️ [ROOM_DEBUG] Room 'ABC123' deleted because host 'HostName' left
```

**Expected Behavior:**
- Room should be deleted immediately
- All players should receive `room_closed` event
- All players should return to lobby

### Test 2: Regular Player Disconnects in Lobby
**Steps:**
1. Host creates a room
2. 2-3 other players join
3. Non-host player clicks "Leave Room" or closes browser

**Expected Logs:**
```
📤 [ROOM_DEBUG] Received 'leave_room' event for room 'ABC123'
📊 [ROOM_DEBUG] Room state before leave: players=[...], host=HostName, started=false
👤 [ROOM_DEBUG] Player 'Player2' leaving room 'ABC123', is_host=false
👥 [ROOM_DEBUG] Regular player 'Player2' removed from room 'ABC123'
📊 [ROOM_DEBUG] Room state after leave: players=[...], host=HostName
```

**Expected Behavior:**
- Player should be removed from room
- Room should continue to exist
- Other players should see updated player list

## In-Game Disconnection Scenarios

### Test 3: Single Player Disconnects During Game
**Steps:**
1. Start a 4-player game
2. During gameplay, one player closes browser
3. Observe bot takeover

**Expected Logs:**
```
🔌 [ROOM_DEBUG] Handling disconnect for room 'ABC123', websocket_id=xxx
🎮 [ROOM_DEBUG] In-game disconnect detected for player 'Player1' in room 'ABC123'
👥 [ROOM_DEBUG] Room 'ABC123' player count: 3 humans, 1 bots
```

**Expected Behavior:**
- Disconnected player should be replaced by bot
- Game should continue
- Other players should be notified

### Test 4: All Players Disconnect (Cleanup Test)
**Steps:**
1. Start a 4-player game
2. All players close their browsers
3. Watch for cleanup

**Expected Logs:**
```
🔌 [ROOM_DEBUG] Handling disconnect for room 'ABC123'
👥 [ROOM_DEBUG] Room 'ABC123' player count: 0 humans, 4 bots
🤖 [ROOM_DEBUG] Room 'ABC123' has no human players, marked for cleanup
🗑️ [ROOM_DEBUG] Room 'ABC123' marked for cleanup at xxx, timeout=0s
🧹 [ROOM_DEBUG] Cleanup iteration X: Checking 1 rooms: ['ABC123']
🧹 [ROOM_DEBUG] Room 'ABC123' marked for cleanup
🗑️ [ROOM_DEBUG] Cleaning up abandoned room ABC123
```

**Expected Behavior:**
- Room should be marked for cleanup when last human leaves
- Cleanup task should detect and remove room after timeout
- All bot players should be removed

### Test 5: Player Reconnects Before Cleanup
**Steps:**
1. Start a game with 2 players
2. Both players disconnect
3. One player reconnects within timeout period

**Expected Logs:**
```
🗑️ [ROOM_DEBUG] Room 'ABC123' marked for cleanup
🔌 [ROOM_DEBUG] New WebSocket connection to room 'ABC123'
✅ [ROOM_DEBUG] Cleanup cancelled for room 'ABC123' - human player reconnected
```

**Expected Behavior:**
- Cleanup should be cancelled
- Player should resume control from bot
- Game should continue normally

## Edge Cases

### Test 6: Rapid Connect/Disconnect
**Steps:**
1. Join a room
2. Rapidly disconnect and reconnect multiple times

**Expected Logs:**
- Multiple connection/disconnection events
- State should remain consistent

### Test 7: Network Interruption vs Explicit Leave
**Steps:**
1. Test network disconnection (kill network)
2. Test explicit leave button
3. Compare behaviors

**Expected Results:**
- Network disconnect: Should trigger handle_disconnect
- Explicit leave: Should trigger leave_room event
- Both should have similar outcomes for room management

## Log Analysis Tips

1. **Check Event Order**: Ensure events happen in logical sequence
2. **Verify State Transitions**: Room state should update correctly after each event
3. **Monitor Cleanup Timing**: Cleanup should respect timeout configuration
4. **Watch for Errors**: Any exceptions or warnings in logs

## Configuration

Current cleanup timeout: `CLEANUP_TIMEOUT_SECONDS = 0` (immediate for testing)
For production, set to 30-60 seconds in `/backend/engine/room.py`