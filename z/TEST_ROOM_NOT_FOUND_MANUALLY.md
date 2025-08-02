# Manual Testing Guide for Non-Existent Room Handling

## Setup

1. Start the server:
   ```bash
   ./start.sh
   ```

2. Open browser developer console (F12)

## Test 1: Non-Existent Room with Stored Session

1. **Create invalid session** in browser console:
   ```javascript
   localStorage.setItem('liap_tui_session', JSON.stringify({
     roomId: 'INVALID999',
     playerName: 'TestUser',
     sessionId: 'test-session',
     createdAt: Date.now(),
     lastActivity: Date.now(),
     gamePhase: null
   }));
   ```

2. **Refresh the page** (or navigate to http://localhost:5050)

3. **Expected behavior**:
   - Page redirects to `/game/INVALID999`
   - Shows "Waiting for Game" briefly
   - Error toast appears: "This game room no longer exists. The server may have restarted. Please create or join a new game."
   - After 3 seconds, redirects to start page
   - Check localStorage - session should be cleared

4. **Verify in console**:
   - Should see: `🚫 Room not found: {room_id: "INVALID999", ...}`
   - Should see: `Session cleared`

## Test 2: Valid Reconnection Still Works

1. **Create a real room**:
   - Go to start page
   - Enter name and go to lobby
   - Create a new room
   - Note the room ID (e.g., "ABC123")

2. **Simulate disconnect**:
   - Close the browser tab (don't use Leave Room button)

3. **Reconnect**:
   - Open new tab to http://localhost:5050
   - Should automatically redirect to the game room
   - Should reconnect successfully without room_not_found error

## Test 3: Server Restart Scenario

1. **Join a game room**
2. **Stop the server** (Ctrl+C in terminal)
3. **Start the server** again (./start.sh)
4. **Refresh the browser**
5. **Expected**: room_not_found event, clear message, redirect to start

## Test 4: Using the Test Script

Once server is running:
```bash
python test_room_not_found.py
```

Should output:
```
✅ Received room_not_found event
   Message: This game room no longer exists
   Suggestion: The server may have restarted. Please create or join a new game.
✅ Test PASSED - Non-existent room handled correctly
```

## Debugging

Check server logs for:
```
Sent room_not_found for non-existent room: INVALID999
```

Check browser console for:
```
🚫 Room not found: {room_id: "INVALID999", ...}
```