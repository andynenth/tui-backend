# Non-Existent Room Handling Implementation Plan

## Problem Statement

### Current Behavior
When a user's browser has a stored session pointing to a room that no longer exists (typically after server restart), they experience:
1. Automatic redirect to `/game/{roomId}` on app load
2. Successful WebSocket connection to `/ws/{roomId}` (server accepts any room_id)
3. Stuck on "Waiting for Game" screen indefinitely
4. No error messages or way to escape

### Root Cause
The WebSocket endpoint (`/ws/{room_id}`) accepts connections for ANY room_id without validating if the room exists. Since the room doesn't exist, no game data is ever sent, leaving users stuck.

### Impact
- Poor user experience after server restarts
- Users must manually clear browser data or wait for 24-hour session expiry
- Confusion about why the game won't load

## Solution Overview

### Smart Room Validation Approach
Instead of rejecting connections to non-existent rooms (which could break valid reconnections), we will:
1. Accept the WebSocket connection initially
2. Send a specific `room_not_found` event if the room doesn't exist
3. Let the frontend handle this gracefully with proper user messaging

### Why This Approach?
- **Preserves reconnection logic**: Valid reconnections continue to work
- **Graceful handling**: Users get clear information instead of connection errors
- **Future-proof**: Compatible with potential room recovery mechanisms
- **Better UX**: Friendly messages and clear next steps

## Implementation Details

### Backend Changes

#### File: `backend/api/routes/ws.py`

**Location**: After line 276 (after WebSocket registration)

**Add room validation check**:
```python
# After: registered_ws = await register(room_id, websocket)
# Add:

# Check if room exists (excluding lobby)
if room_id != "lobby":
    room = room_manager.get_room(room_id)
    if not room:
        # Send room_not_found event
        await registered_ws.send_json({
            "event": "room_not_found",
            "data": {
                "room_id": room_id,
                "message": "This game room no longer exists",
                "suggestion": "The server may have restarted. Please create or join a new game.",
                "timestamp": asyncio.get_event_loop().time()
            }
        })
        logger.info(f"Sent room_not_found for non-existent room: {room_id}")
        # Continue running to allow frontend to handle gracefully
```

### Frontend Changes

#### 1. File: `frontend/src/services/NetworkService.ts`

**Verify event propagation**: Ensure `room_not_found` events are properly dispatched to listeners (should work with existing event system).

#### 2. File: `frontend/src/pages/GamePage.jsx`

**Location**: In the `useEffect` that sets up event listeners (around line 100)

**Add room_not_found handler**:
```javascript
// Add to the effect that sets up NetworkService listeners
useEffect(() => {
  if (!networkService || !roomId) return;

  const listeners = [];

  // Add room_not_found handler
  const handleRoomNotFound = (event) => {
    console.log('🚫 Room not found:', event.detail);
    
    // Show toast notification
    const message = event.detail.data?.message || 'This game room no longer exists';
    const suggestion = event.detail.data?.suggestion || 'Please return to the start page';
    
    // Clear invalid session
    clearSession();
    
    // Show error toast (using existing toast system)
    if (window.showToast) {
      window.showToast({
        type: 'error',
        title: 'Room Not Found',
        message: `${message}. ${suggestion}`,
        duration: 8000
      });
    }
    
    // Redirect to start page after short delay
    setTimeout(() => {
      navigate('/');
    }, 3000);
  };

  networkService.addEventListener('room_not_found', handleRoomNotFound);
  listeners.push(() => 
    networkService.removeEventListener('room_not_found', handleRoomNotFound)
  );

  // ... existing listeners ...

  return () => {
    listeners.forEach(cleanup => cleanup());
  };
}, [networkService, roomId, navigate]);
```

**Import clearSession**:
```javascript
// Add to imports at top of file
import { clearSession } from '../utils/sessionStorage';
```

#### 3. File: `frontend/src/components/game/WaitingUI.jsx` (Optional Enhancement)

**Add timeout detection** as a fallback:
```javascript
// Add a timeout to detect stuck state
useEffect(() => {
  const timeout = setTimeout(() => {
    // If still waiting after 30 seconds, show helpful message
    if (gameState.phase === 'waiting' && !gameState.players?.length) {
      console.warn('⏱️ Game data not received after 30 seconds');
      // Could show a "Having trouble?" message with refresh option
    }
  }, 30000);

  return () => clearTimeout(timeout);
}, [gameState.phase, gameState.players]);
```

### Event Flow Diagram

```
User with stored session (room: ABC123)
    |
    v
App loads, finds session
    |
    v
Redirects to /game/ABC123
    |
    v
WebSocket connects to /ws/ABC123
    |
    v
Backend: Room ABC123 doesn't exist
    |
    v
Backend sends room_not_found event
    |
    v
Frontend receives event
    |
    v
Shows error toast to user
    |
    v
Clears invalid session
    |
    v
Redirects to start page
```

## Testing Plan

### Test Scenarios

1. **Non-existent room with stored session**
   - Store a session with fake room_id
   - Restart server
   - Load app
   - Verify: room_not_found event received, session cleared, redirected to start

2. **Valid reconnection still works**
   - Join a real game
   - Disconnect (close browser)
   - Reconnect within session timeout
   - Verify: Reconnection successful, game state restored

3. **Edge case: Room created after initial check**
   - Connect to non-existent room
   - Create that room via another client
   - Verify: System handles gracefully

### Manual Testing Steps

1. **Setup**:
   ```bash
   # Start the server
   ./start.sh
   
   # Create and join a room
   # Note the room ID (e.g., ABC123)
   ```

2. **Create invalid session**:
   ```javascript
   // In browser console
   localStorage.setItem('liap_tui_session', JSON.stringify({
     roomId: 'INVALID999',
     playerName: 'TestUser',
     sessionId: 'test-session',
     createdAt: Date.now(),
     lastActivity: Date.now(),
     gamePhase: null
   }));
   ```

3. **Test the fix**:
   - Refresh the page
   - Should see error message
   - Should redirect to start page
   - Check localStorage - session should be cleared

### Monitoring

After deployment, monitor for:
- `room_not_found` events in logs
- User reports of connection issues
- Reconnection success rates

## Rollback Plan

If issues arise:

1. **Quick disable**: Comment out the room validation check in `ws.py`
2. **Frontend revert**: Remove the `room_not_found` event listener
3. **Git revert**: `git revert <commit-hash>` if needed

### What to monitor:
- WebSocket connection stability
- Reconnection success rates  
- User complaints about being unable to rejoin games
- Server logs for unexpected errors

## Success Criteria

- ✅ Users with invalid sessions see clear error message
- ✅ Invalid sessions are automatically cleared
- ✅ Users are redirected to start page
- ✅ Valid reconnections continue to work
- ✅ No increase in connection errors
- ✅ Better user experience after server restarts

## Implementation Notes

- The backend continues to run after sending `room_not_found` to maintain connection stability
- The frontend handles all cleanup and navigation
- The 3-second delay before redirect gives users time to read the message
- Session clearing happens immediately to prevent redirect loops
- Toast notifications provide clear feedback to users

## Future Enhancements

1. **Room recovery**: Implement server-side room state persistence
2. **Rejoin prompt**: Ask users if they want to create a new room with same players
3. **Session migration**: Transfer stats/preferences to new session
4. **Lobby return**: Option to return to lobby instead of start page