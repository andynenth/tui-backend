# Page Refresh Debug Guide

## Bug Description
When a player refreshes the browser page during an active game, the game state is lost and the player returns to the lobby instead of reconnecting to the active game.

## Testing Sequence

### Prerequisites
1. Two browser windows (one for testing, one for observing)
2. Playwright MCP server active
3. Backend and frontend running

### Test Steps
1. **Enter Lobby**
   - Navigate to http://localhost:5173
   - Enter player name (e.g., "TestPlayer")

2. **Create Room**
   - Click "Create Room"
   - Note the room ID

3. **Start Game**
   - Add 3 bots
   - Click "Start Game"
   - Wait for preparation phase

4. **Select Number (Declaration Phase)**
   - When prompted, select a number (0-8)
   - Click confirm

5. **Play Pieces (Turn Phase)**
   - When it's your turn, select pieces
   - Click play

6. **Refresh Browser**
   - Press F5 or Cmd+R
   - Observe behavior

### Expected vs Actual Behavior
- **Expected**: Player reconnects to active game with current state
- **Actual**: Player returns to lobby, loses game connection

## Root Cause Analysis

### Key Components

1. **Frontend Session Storage** (`frontend/src/utils/sessionStorage.js`)
   - Stores: roomId, playerName, sessionId, gamePhase
   - Used for reconnection after refresh
   - 24-hour expiry

2. **GameService** (`frontend/src/services/GameService.ts`)
   - Handles phase_change events
   - Manages game state
   - Updates session storage on phase changes

3. **NetworkService** (`frontend/src/services/NetworkService.ts`)
   - WebSocket connection management
   - Sends `client_ready` with `is_reconnection` flag
   - Handles reconnection logic

4. **Backend Connection Manager** (`backend/api/websocket/connection_manager.py`)
   - Tracks player connections
   - Allows unlimited reconnection time
   - Maintains player state during disconnection

### Potential Issues

1. **Session Storage Not Being Read on Refresh**
   - App.tsx may not check for existing session
   - Navigation logic might bypass reconnection

2. **WebSocket Reconnection Sequence**
   - `client_ready` event might not trigger full state restore
   - Backend might not send complete phase_change on reconnection

3. **React Router Navigation**
   - Route guards might redirect to lobby before reconnection
   - Missing reconnection logic in routing

## Solution Options

### Option 1: App-Level Session Check
**Location**: `frontend/src/App.tsx` or main entry point

```javascript
// On app mount, check for existing session
useEffect(() => {
  const session = getSession();
  if (session && session.roomId && session.playerName) {
    // Attempt to reconnect
    gameService.joinRoom(session.roomId, session.playerName)
      .then(() => {
        navigate(`/game/${session.roomId}`);
      })
      .catch(() => {
        clearSession();
        navigate('/');
      });
  }
}, []);
```

**Debug Logs to Add**:
```javascript
console.log('[REFRESH_DEBUG] App mount - checking session:', session);
console.log('[REFRESH_DEBUG] Attempting reconnection to:', session?.roomId);
```

### Option 2: Enhanced Backend State Restoration
**Location**: `backend/api/routes/ws.py` - handle client_ready

```python
# When client_ready with is_reconnection=True
if data.get("is_reconnection") and data.get("request_full_state"):
    # Force send complete phase_change event
    if room and room.game and room.game.state_machine:
        await room.game.state_machine.force_broadcast_current_state()
```

**Debug Logs to Add**:
```python
logger.info(f"[REFRESH_DEBUG] client_ready received: is_reconnection={data.get('is_reconnection')}, room={room_id}, has_game={bool(room and room.game)}")
```

### Option 3: Router-Level Protection
**Location**: `frontend/src/pages/GamePage.tsx` or route component

```javascript
// Check session before rendering
useEffect(() => {
  if (!gameState.roomId) {
    const session = getSession();
    if (session && session.roomId === roomId) {
      // Reconnect using session data
      handleReconnection(session);
    } else {
      // No valid session, redirect to lobby
      navigate('/');
    }
  }
}, [gameState.roomId, roomId]);
```

**Debug Logs to Add**:
```javascript
console.log('[REFRESH_DEBUG] GamePage mount - gameState:', gameState);
console.log('[REFRESH_DEBUG] Session check:', getSession());
```

## Testing Process

### 1. Add Debug Logging
First, add comprehensive logging to trace the refresh flow:

```javascript
// NetworkService.ts - processGameEvent
if (eventType === 'phase_change') {
  console.log('🔍 [REFRESH_DEBUG] Phase change received:', {
    newPhase: data.phase,
    currentPhase: this.state.phase,
    hasPlayers: !!data.players,
    hasPhaseData: !!data.phase_data,
    playerName: this.state.playerName,
    roomId: this.state.roomId,
    timestamp: new Date().toISOString()
  });
}

// NetworkService.ts - connectToRoom
console.log('🔍 [REFRESH_DEBUG] Sending client_ready:', {
  room_id: roomId,
  player_name: connectionData?.playerName,
  is_reconnection: isReconnection,
  request_full_state: isReconnection,
  timestamp: new Date().toISOString()
});
```

```python
# backend/api/routes/ws.py
async def handle_client_ready(websocket, room_id, data):
    logger.info(f"🔍 [REFRESH_DEBUG] client_ready: room={room_id}, reconnection={data.get('is_reconnection')}, player={data.get('player_name')}")
    
    # Log current game state
    room = await room_manager.get_room(room_id)
    if room and room.game:
        logger.info(f"🔍 [REFRESH_DEBUG] Game state: phase={room.game.phase}, round={room.game.round_number}, players={len(room.game.players)}")
```

### 2. Test Each Solution

#### Testing Option 1 (App-Level)
1. Add session check in App.tsx
2. Add debug logs
3. Run test sequence
4. Check console for:
   - Session detection on mount
   - Reconnection attempt
   - Navigation decisions

#### Testing Option 2 (Backend)
1. Modify client_ready handler
2. Add state broadcast logic
3. Run test sequence
4. Check logs for:
   - client_ready reception
   - State broadcast trigger
   - phase_change event sent

#### Testing Option 3 (Router)
1. Add route protection
2. Add session validation
3. Run test sequence
4. Check for:
   - Route component lifecycle
   - Session validation
   - Reconnection trigger

### 3. Validation Steps

After implementing a solution:

1. **Basic Test**
   - Complete test sequence
   - Verify reconnection works
   - Check state is preserved

2. **Edge Cases**
   - Refresh during different phases
   - Refresh multiple times
   - Refresh with network delay

3. **Multi-Player Test**
   - Ensure other players see correct state
   - Verify no duplicate players
   - Check turn order preservation

## Success Criteria

The fix is successful when:
1. Player refreshes browser → returns to same game state
2. Player name, hand, and position preserved
3. Current phase and turn order maintained
4. No disruption to other players
5. Works across all game phases

## Rollback Plan

If a solution causes issues:
1. Revert the specific changes
2. Keep debug logs for analysis
3. Try next solution option
4. Document what didn't work and why