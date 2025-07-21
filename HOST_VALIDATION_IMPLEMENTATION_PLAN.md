# Host Validation Implementation Plan

## Overview

This document provides a comprehensive plan to restrict room management actions (add_bot and remove_player) to only the host player, implementing both frontend UI changes and backend validation for security.

## Current State Analysis

### Frontend (`frontend/src/pages/RoomPage.jsx`)
- **Lines 233-240**: "Add Bot" button is shown for ALL connected players on empty slots
- **Lines 242-252**: "Remove" button is shown for ALL connected players (except host cannot be removed)
- **Line 27-30**: Host check is already implemented using `isCurrentPlayerHost`

### Backend (`backend/api/routes/ws.py`)
- **Lines 825-885**: `add_bot` event handler - NO host validation
- **Lines 760-819**: `remove_player` event handler - NO host validation
- **Line 256**: WebSocket ID is generated and stored as `websocket._ws_id`
- **Lines 603-608**: Connection manager tracks player-to-websocket mapping

### Connection Tracking (`backend/api/websocket/connection_manager.py`)
- **Line 47-49**: Maps WebSocket ID to (room_id, player_name) tuple
- **Lines 53-81**: `register_player()` associates WebSocket with player
- **Lines 83-112**: `handle_disconnect()` uses mapping to identify disconnecting player

## Implementation Strategy

### Phase 1: Frontend - Hide Controls for Non-Host Players

**Goal**: Prevent non-host players from seeing add/remove buttons

**File**: `frontend/src/pages/RoomPage.jsx`

**Changes**:
1. Wrap "Add Bot" button with host check (line 233)
2. Wrap "Remove" button with host check (line 244)

### Phase 2: Backend - Add Host Validation

**Goal**: Enforce host-only actions on the server side for security

**File**: `backend/api/routes/ws.py`

**Changes**:
1. Create helper function to get current player from WebSocket
2. Add host validation to `add_bot` handler
3. Add host validation to `remove_player` handler

## Detailed Implementation

### Phase 1: Frontend Changes

```jsx
// In RoomPage.jsx, modify the "Add Bot" button section (around line 233)
// REPLACE:
{isEmpty ? (
  <div className="rp-playerAction">
    <button
      className="rp-actionBtn rp-addBotBtn"
      onClick={() => addBot(position)}
      disabled={!isConnected}
    >
      Add Bot
    </button>
  </div>
) : (

// WITH:
{isEmpty && isCurrentPlayerHost ? (
  <div className="rp-playerAction">
    <button
      className="rp-actionBtn rp-addBotBtn"
      onClick={() => addBot(position)}
      disabled={!isConnected}
    >
      Add Bot
    </button>
  </div>
) : (

// AND modify the "Remove" button section (around line 242)
// REPLACE:
!isHost && (
  <div className="rp-playerAction">
    <button
      className="rp-actionBtn rp-removeBtn"
      onClick={() => removePlayer(position)}
      disabled={!isConnected}
    >
      Remove
    </button>
  </div>
)

// WITH:
!isHost && isCurrentPlayerHost && (
  <div className="rp-playerAction">
    <button
      className="rp-actionBtn rp-removeBtn"
      onClick={() => removePlayer(position)}
      disabled={!isConnected}
    >
      Remove
    </button>
  </div>
)
```

### Phase 2: Backend Changes

```python
# In backend/api/routes/ws.py

# Step 1: Add helper function after imports (around line 30)
async def get_current_player_name(websocket_id: str) -> Optional[str]:
    """Get the player name associated with a WebSocket ID"""
    if websocket_id in connection_manager.websocket_to_player:
        _, player_name = connection_manager.websocket_to_player[websocket_id]
        return player_name
    return None

# Step 2: Modify add_bot handler (starting at line 825)
elif event_name == "add_bot":
    # Already validated - slot_id is guaranteed to be present and valid
    slot_id = event_data.get("slot_id")
    
    # Get current player from WebSocket
    websocket_id = getattr(registered_ws, '_ws_id', None)
    current_player = await get_current_player_name(websocket_id) if websocket_id else None
    
    room = room_manager.get_room(room_id)
    if room:
        # Check if current player is the host
        if current_player != room.host_name:
            await registered_ws.send_json(
                {
                    "event": "error",
                    "data": {
                        "message": "Only the host can add bots",
                        "type": "permission_denied"
                    },
                }
            )
            continue
            
        try:
            # ... rest of existing add_bot logic ...

# Step 3: Modify remove_player handler (starting at line 760)
elif event_name == "remove_player":
    # Already validated - slot_id is guaranteed to be present and valid
    slot_id = event_data.get("slot_id")
    
    # Get current player from WebSocket
    websocket_id = getattr(registered_ws, '_ws_id', None)
    current_player = await get_current_player_name(websocket_id) if websocket_id else None
    
    room = room_manager.get_room(room_id)
    if room:
        # Check if current player is the host
        if current_player != room.host_name:
            await registered_ws.send_json(
                {
                    "event": "error",
                    "data": {
                        "message": "Only the host can remove players",
                        "type": "permission_denied"
                    },
                }
            )
            continue
            
        try:
            # ... rest of existing remove_player logic ...
```

## Testing Plan

### Test Cases

1. **Frontend Visibility Tests**:
   - [ ] Host sees "Add Bot" buttons on empty slots
   - [ ] Non-host players do NOT see "Add Bot" buttons
   - [ ] Host sees "Remove" buttons on non-host players
   - [ ] Non-host players do NOT see "Remove" buttons

2. **Backend Security Tests**:
   - [ ] Host can successfully add bots
   - [ ] Non-host players receive error when attempting to add bots
   - [ ] Host can successfully remove players
   - [ ] Non-host players receive error when attempting to remove players

3. **Edge Cases**:
   - [ ] Host migration: New host gains add/remove abilities
   - [ ] WebSocket reconnection: Permissions maintained after reconnect
   - [ ] Multiple rooms: Host in one room cannot affect another room

### Manual Testing Steps

1. **Setup**:
   ```bash
   ./start.sh
   ```

2. **Test Non-Host Restrictions**:
   - Player A creates room (becomes host)
   - Player B joins room
   - Verify Player B sees no add/remove buttons
   - Use browser DevTools to manually send add_bot/remove_player from Player B
   - Verify backend rejects with permission error

3. **Test Host Capabilities**:
   - Verify Player A (host) sees all buttons
   - Verify Player A can add bots successfully
   - Verify Player A can remove Player B

## Potential Side Effects & Mitigations

### 1. Host Disconnection
**Issue**: If host disconnects, no one can manage the room
**Current Behavior**: Room is immediately deleted (pre-game)
**No Change Needed**: Existing behavior prevents this issue

### 2. WebSocket ID Not Found
**Issue**: Connection manager might not have the mapping
**Mitigation**: Gracefully handle missing player identity by denying permission

### 3. Race Conditions
**Issue**: Player identity might change during request processing
**Mitigation**: Get player identity at the start of handler and use throughout

## Implementation Checklist

- [ ] Phase 1: Update frontend RoomPage.jsx
  - [ ] Add host check to "Add Bot" button
  - [ ] Add host check to "Remove" button
  - [ ] Test UI changes locally
  
- [ ] Phase 2: Update backend ws.py
  - [ ] Add get_current_player_name helper function
  - [ ] Add host validation to add_bot handler
  - [ ] Add host validation to remove_player handler
  - [ ] Handle edge cases (missing WebSocket ID, etc.)
  
- [ ] Testing
  - [ ] Run all manual test cases
  - [ ] Verify no regression in existing functionality
  - [ ] Test with multiple concurrent rooms
  
- [ ] Code Quality
  - [ ] Run frontend linter: `cd frontend && npm run lint`
  - [ ] Run backend formatter: `cd backend && black .`
  - [ ] Run backend linter: `cd backend && pylint api/routes/ws.py`

## Security Considerations

1. **Defense in Depth**: Both frontend and backend validation ensures security even if frontend is bypassed
2. **No Trust in Client**: Backend validates every request regardless of frontend state
3. **Fail Secure**: Default to denying permission if player identity cannot be determined
4. **Audit Trail**: All permission denials are logged for monitoring

## Rollback Plan

If issues arise:
1. Frontend: Remove host checks from button rendering
2. Backend: Remove host validation from event handlers
3. Both changes are independent and can be rolled back separately