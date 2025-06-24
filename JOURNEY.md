The Issue: The "Create Room" button appeared to do nothing when clicked.

  Root Causes:
  1. Frontend Modal State Bug: Debug console.log statements in the Modal component were causing continuous
  re-rendering loops, making the modal flicker between open/closed states
  2. Backend-Frontend Mismatch: The frontend was sending WebSocket events (create_room, get_rooms) but the
  backend only had REST API endpoints - missing WebSocket event handlers

  How I Fixed It

  Phase 1: Frontend Modal Issues

  1. Identified re-rendering loop caused by debug logs in Modal.jsx lines 69 and 73
  2. Removed debug console.log statements that were triggering continuous component re-renders
  3. Applied useMemo optimization to useSocket hook to prevent unnecessary object recreation

  Phase 2: Simplified UX

  1. Removed modal complexity - you suggested directly creating rooms instead of showing a modal
  2. Streamlined button behavior: Click → Create room → Navigate (no modal popup)
  3. Added loading state: Button shows "Creating..." while processing

  Phase 3: Backend WebSocket Handlers

  1. Discovered missing handlers: Backend had REST API (POST /create-room) but no WebSocket event handlers
  2. Added WebSocket event handlers in /backend/api/routes/ws.py:
    - create_room: Creates room and responds with room_created event
    - get_rooms: Returns current room list as room_list event
  3. Integrated with existing room creation logic and lobby notifications

  Key Insight

  The problem wasn't the button itself - it was a communication protocol mismatch. Frontend expected WebSocket
   bidirectional communication, but backend only provided REST API endpoints. Adding the missing WebSocket
  handlers bridged this gap.

---

  The Issue: The "Create Room" button appeared to do nothing - rooms were created on the backend but the frontend
  couldn't display them properly.

  Root Cause Analysis

  There were actually 3 cascading issues:

  1. Missing WebSocket Handlers: Frontend sent create_room and get_room_state WebSocket events, but backend
  only had REST API endpoints
  2. Navigation Logic Bug: Two room_created events (direct response + lobby broadcast) caused navigation to
  wrong room ID
  3. Missing Host Information: Backend didn't include is_host field in player data, so frontend couldn't
  detect host status

  The Fix

  Phase 1: Added Missing WebSocket Handlers
  # backend/api/routes/ws.py
  elif event_name == "create_room":
      room_id = room_manager.create_room(player_name)
      await registered_ws.send_json({
          "event": "room_created",
          "data": {"room_id": room_id, "success": true}
      })

  elif event_name == "get_room_state":
      room = room_manager.get_room(room_id)
      await registered_ws.send_json({
          "event": "room_update",
          "data": room.summary()
      })

  Phase 2: Fixed Navigation Logic
  // frontend/src/pages/LobbyPage.jsx
  const unsubRoomCreated = socket.on('room_created', (data) => {
    // Only navigate if this is direct response, not lobby broadcast
    if (data.success === true) {
      navigate(`/room/${data.room_id}`);
    }
  });

  Phase 3: Added Host Information
  # backend/engine/room.py
  def slot_info(player, slot_index):
      return {
          "name": player.name,
          "is_bot": player.is_bot,
          "is_host": slot_index == 0  # Host is always in slot P1
      }

  Result

  ✅ Before: Button click → Nothing visible happens✅ After: Button click → Room created → Navigate to room →
  Display host in P1 + bots in P2-P4 → Start Game button enabled

  The key insight was that frontend and backend were using different communication protocols (WebSocket vs
  REST), which required bridging the gap with proper event handlers.
  ---
  ⏺ Summary of Room Management Bugs and Fixes

  1. JavaScript WebSocket Connection Error

  Bug: Cannot read properties of null (reading 'close') error in SocketConnection.js:31
  Root Cause: Timeout handler tried to call this.socket.close() when this.socket was null
  Fix: Added null check before calling close method
  // Before
  this.socket.close();

  // After  
  if (this.socket) {
      this.socket.close();
  }

  2. Missing "Remove Bot" Backend Handler

  Bug: Remove bot button did nothing - no backend response
  Root Cause: Backend WebSocket handler missing remove_player event processor
  Fix: Added complete remove_player event handler in backend/api/routes/ws.py
  elif event_name == "remove_player":
      slot_id = event_data.get("slot_id")
      # Convert frontend slot IDs (1-4) to backend indices (0-3)
      slot_index = int(slot_id) - 1
      result = await room.assign_slot_safe(slot_index, None)
      # Broadcast room update to all clients

  3. Missing "Add Bot" Backend Handler

  Bug: Add bot button didn't work - same issue as remove bot
  Root Cause: Backend missing add_bot event processorFix: Added add_bot event handler that generates bot names
   and assigns to slots
  elif event_name == "add_bot":
      slot_id = event_data.get("slot_id")
      bot_name = f"Bot {slot_id}"
      result = await room.assign_slot_safe(slot_index, bot_name)
      # Broadcast room update to all clients

  4. Wrong Broadcast Function Call

  Bug: name 'broadcast_to_room' is not defined error when removing players
  Root Cause: Used non-existent function name instead of the actual broadcast function
  Fix: Changed broadcast_to_room() calls to use existing broadcast() function
  # Before
  await broadcast_to_room(room_id, {...})

  # After
  await broadcast(room_id, "room_update", {...})

  5. Missing "Leave Room" Backend Handler

  Bug: Leave room button did nothing - no backend processing
  Root Cause: Backend missing leave_room event processor
  Fix: Added comprehensive leave room handler that:
  - Distinguishes between host leaving (closes room) vs regular player leaving
  - Broadcasts appropriate events (room_closed or room_update)
  - Updates lobby room list when rooms are closed
  - Handles both scenarios correctly

  6. Frontend Leave Room Data Missing

  Bug: Backend expected player_name in leave room event but frontend didn't send it
  Root Cause: Frontend called socket.send('leave_room') without player data
  Fix: Updated frontend to include player name
  // Before
  socket.send('leave_room');

  // After  
  socket.send('leave_room', { player_name: app.playerName });

  Key Patterns in the Fixes

  1. Consistent Event Handling: All WebSocket events now follow the same pattern:
    - Validate input data
    - Use assign_slot_safe() for thread-safe operations
    - Broadcast updates to all room clients
    - Handle errors gracefully
  2. Frontend-Backend Data Sync: Fixed slot numbering mismatches (frontend 1-4 → backend 0-3)
  3. Real-time Updates: All operations now broadcast room state changes immediately to connected clients
  4. Error Prevention: Added null checks and proper error handling throughout

  The end result is a fully functional room management system where all buttons work correctly with real-time
  UI updates and proper WebSocket communication.

---

## Recent Fixes (Session 4) - Room Management Polish

### 7. Host Leaving Room Not Deleting Room ✅
**Bug**: When host left room, room remained visible in lobby
**Root Cause**: Code called non-existent `room_manager.remove_room()` instead of `delete_room()`
**Fix**: Updated method call in `backend/api/routes/ws.py:262`
```python
# Before
room_manager.remove_room(room_id)

# After  
room_manager.delete_room(room_id)
```

### 8. Room ID Not Showing in Lobby ✅
**Bug**: Lobby showed "Room undefined" instead of actual room IDs
**Root Cause**: Frontend used `room.id` but backend returns `room.room_id` in summary
**Fix**: Updated lobby to use fallback pattern in `frontend/src/pages/LobbyPage.jsx`
```javascript
// Before
Room {room.id}

// After
Room {room.room_id || room.id}
```

### 9. Leave Room Modal Not Appearing ✅
**Bug**: Leave Room button clicked but no modal appeared
**Root Cause**: Tailwind CSS classes `bg-opacity-50` and `backdrop-blur-sm` not working properly
**Fix**: Replaced problematic CSS with explicit inline styles in `frontend/src/components/Modal.jsx`
```javascript
// Before
className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm"

// After
className="fixed inset-0 z-50 flex items-center justify-center bg-black"
style={{ 
  zIndex: 9999, 
  backgroundColor: 'rgba(0, 0, 0, 0.5)',
  position: 'fixed',
  top: 0, left: 0, right: 0, bottom: 0
}}
```

### 10. Host Leave Room Confirmation Missing ✅
**Bug**: Host leaving room closed room but didn't get navigation confirmation
**Root Cause**: Backend sent room closure broadcast but no direct response to leaving host
**Fix**: Added confirmation response in `backend/api/routes/ws.py`
```python
# Added after room deletion
await registered_ws.send_json({
    "event": "player_left",
    "data": {"player_name": player_name, "success": True, "room_closed": True}
})
```

## 🔧 Common Bug Patterns & Solutions

### WebSocket Event Handler Pattern
**Problem**: Frontend sends events but backend doesn't handle them
**Solution**: Always add backend handlers following this pattern:
```python
elif event_name == "your_event":
    # 1. Validate input data
    data = event_data.get("required_field")
    if not data:
        await registered_ws.send_json({"event": "error", "data": {"message": "Missing field"}})
        continue
    
    # 2. Process with thread-safe operations
    result = await room.some_safe_operation(data)
    
    # 3. Broadcast updates
    if result["success"]:
        updated_summary = room.summary()
        await broadcast(room_id, "room_update", updated_summary)
    
    # 4. Send confirmation to sender
    await registered_ws.send_json({"event": "operation_result", "data": result})
```

### CSS/Tailwind Issues Pattern
**Problem**: Tailwind classes not working as expected
**Debugging**: Add explicit inline styles to test if CSS is the issue
**Solution**: Either fix Tailwind config or use inline styles for critical UI elements

### Modal Rendering Issues
**Problem**: Modal state updates but doesn't appear
**Debugging Steps**:
1. Add `console.log` to track state changes
2. Add `console.log` in modal render function
3. Test with simplified CSS (remove complex classes)
4. Use explicit positioning and z-index

### Frontend-Backend Data Structure Mismatch
**Problem**: Frontend expects different data format than backend provides
**Solution**: Use fallback patterns: `room.room_id || room.id`
**Best Practice**: Always check backend API responses and align frontend expectations

## 📋 Testing Checklist for Room Management

When adding new room features, test these scenarios:
- [ ] Create room as host
- [ ] Add/remove bots in all slots  
- [ ] Join room as regular player
- [ ] Leave room as regular player (should remove from slot)
- [ ] Leave room as host (should close entire room)
- [ ] Check lobby updates after room changes
- [ ] Verify room IDs display correctly
- [ ] Test modals appear and function properly
- [ ] Check WebSocket error handling

### 11. Lobby Not Updating When Room Availability Changes ✅
**Bug**: When removing bots from rooms, lobby doesn't show room as available again
**Root Cause**: Three cascading issues:
1. **Event Name Mismatch**: Frontend listened for `room_list` but backend sent `room_list_update`
2. **WebSocket Handler Mismatch**: Frontend sent `get_rooms` but backend only handled `request_room_list`

---

## 🎯 Bot Declaration Phase Integration (Week 3 - Current Issue)

### 12. Declaration Phase Stopping Issue 🔄 IN PROGRESS
**Problem**: Game reaches Declaration phase but bots don't make declarations, causing game to stop waiting for player input

#### Root Cause Analysis (Completed):
1. ✅ **RED_GENERAL Starter Detection Failed**: Bot 2 has RED_GENERAL but Andy was being chosen as starter
   - **Fixed**: `preparation_state.py:351` - Changed `getattr(piece, 'name', str(piece))` to `str(piece)` for piece detection
   
2. ✅ **Bot Manager Not Triggered**: State machine didn't notify bot manager when transitioning to Declaration phase  
   - **Fixed**: Added `_notify_bot_manager()` method in `game_state_machine.py:161` to trigger bot actions on phase changes

3. ✅ **Declaration Order Mismatch**: Bot manager looked for `game.current_order` but state machine stored order in `phase_data['declaration_order']`
   - **Fixed**: Updated `bot_manager.py:443` `_get_declaration_order()` to read from state machine phase data

4. ✅ **String vs Player Object Type Error**: Declaration order contained strings but bot manager expected Player objects
   - **Fixed**: Updated `bot_manager.py:456` `_get_player_index()` to handle both strings and Player objects
   - **Fixed**: Updated `bot_manager.py:102` `_handle_declaration_phase()` to find Player objects from strings

5. ✅ **Missing Game Attribute**: Declaration state tried to access `game.player_declarations` which didn't exist
   - **Fixed**: Added `player_declarations = {}` to `game.py:36` in Game `__init__` method

6. ✅ **Declaration Validation Error**: `_get_current_declarer()` returned Player objects but validation expected strings
   - **Fixed**: Updated `declaration_state.py:103` to return player names as strings

#### Current Status:
- ✅ Bot 2 correctly identified as starter (has RED_GENERAL)
- ✅ Bot manager receives "round_started" event 
- ✅ Declaration order properly retrieved: ['Bot 2', 'Bot 3', 'Bot 4', 'Andy']
- ✅ Bots successfully make declarations: Bot 2→3, Bot 3→1, Bot 4→1
- ❌ **INFINITE LOOP**: Bots keep re-declaring because `declared` value remains 0

#### Current Issue - Bot Infinite Declaration Loop:
**Symptom**: Bots continuously re-declare because they think their previous declarations weren't processed
**Evidence**: 
```
🔍 DECL_PHASE_DEBUG: Player Bot 4 declared value: 0  (should be 1 after declaration)
✅ Bot Bot 4 declared 1  (bot successfully declares)
Wrong player turn: Bot 4, expected: Andy  (validation error - should be expecting Andy)
```

**Root Cause**: Two interlinked issues:
1. **Declaration Not Persisted**: Player objects' `declared` attribute not being updated when declarations are processed
2. **State Machine Validation Out of Sync**: Current declarer index advances but Player objects don't reflect successful declarations

#### Next Steps:
1. **Fix Declaration Persistence**: Ensure `player.declared` attribute is updated when declarations are processed in `declaration_state.py:_handle_declaration()`
2. **Debug State Machine Validation**: The validation shows "expected: Andy" after bots declare, but then rejects declarations from bots - need to debug the `current_declarer_index` logic
3. **Test End-to-End Flow**: Verify that once all bots declare, the game properly waits for human player Andy to declare
4. **Fix Frontend Integration**: Address frontend errors about null `updateDeclaration` method

#### Implementation Strategy:
- **Priority 1**: Fix the bot loop (declaration persistence + validation sync) 
- **Priority 2**: Test human player declaration integration
- **Priority 3**: Phase transition to Turn phase after all declarations complete
- **Priority 4**: Frontend declaration UI fixes
3. **Data Structure Mismatch**: Frontend used `room.players?.length` but backend sent `room.occupied_slots`

**Fix**: Updated frontend-backend communication in multiple files:
```javascript
// frontend/src/pages/LobbyPage.jsx - Fixed event listener
socket.on('room_list_update', (data) => { // was: 'room_list'

// Fixed data structure usage
const playerCount = room.occupied_slots || 0; // was: room.players?.length || 0
const canJoin = (room.occupied_slots || 0) < (room.total_slots || 4); // was: room.players?.length
```

```python
# backend/api/routes/ws.py - Fixed event handler
if event_name == "request_room_list" or event_name == "get_rooms": # was: only "request_room_list"
```

**Result**: Lobby now correctly shows real-time availability: "🔒 Full (4/4)" → "⏳ Waiting (3/4)" when bots are removed

### 12. Join Button in Lobby Not Working ✅
**Bug**: Clicking "Join" button on rooms in lobby did nothing - no error, no navigation
**Root Cause**: Missing WebSocket event handler for `join_room` events from lobby
**Investigation**: 
- Frontend correctly sends `join_room` WebSocket message with `room_id` and `player_name`
- Backend lobby handler only supported `create_room`, `get_rooms`, but not `join_room`
- Missing handler meant messages were ignored silently

**Fix**: Added complete `join_room` handler in `backend/api/routes/ws.py` lobby section:
```python
elif event_name == "join_room":
    room_id_to_join = event_data.get("room_id")
    player_name = event_data.get("player_name", "Unknown Player")
    
    # Validate room exists, not full, not started
    room = room_manager.get_room(room_id_to_join)
    if not room or room.is_full() or room.started:
        await registered_ws.send_json({"event": "error", "data": {...}})
        continue
    
    # Try to join
    result = await room.join_room_safe(player_name)
    if result["success"]:
        await registered_ws.send_json({"event": "room_joined", "data": {...}})
```

### 13. Host Not Seeing Player Join Real-Time ✅  
**Bug**: When player joins room from lobby, host doesn't see slot update immediately
**Root Cause**: Event name inconsistency in room broadcasting
**Investigation**:
- Player joins successfully and gets navigated to room
- But existing room clients (host) don't get real-time updates
- Join events work but leave events show updates immediately

**Fix**: Two-part fix in `backend/api/routes/ws.py`:

**Part 1 - Missing Room Broadcast**: Added broadcast to room clients after successful join:
```python
# After successful join, notify ALL clients in the room
await broadcast(room_id_to_join, "room_update", {
    "players": room_summary["slots"],
    "host_name": room_summary["host_name"],
    "room_id": room_id_to_join,
    "started": room_summary.get("started", False)
})
```

**Part 2 - Event Name Mismatch**: 
- ❌ Join events used: `room_state_update` with `slots` field
- ✅ Other events used: `room_update` with `players` field  
- ❌ Frontend expects: `room_update` events only

**Fix**: Changed join broadcast to match other room operations:
```python
# Before (inconsistent)
await broadcast(room_id, "room_state_update", {"slots": ...})

# After (consistent)  
await broadcast(room_id, "room_update", {"players": ...})
```

**Result**: Host now sees new players join instantly with real-time slot updates

## 🔧 WebSocket Event Consistency Pattern

**Key Learning**: All room events must use identical event names and data structures:

```python
# ✅ CONSISTENT PATTERN - All room operations use this
await broadcast(room_id, "room_update", {
    "players": room_summary["slots"],    # Always "players", never "slots" 
    "host_name": room_summary["host_name"],
    "room_id": room_id,
    "started": room_summary.get("started", False)
})
```

**Events that follow this pattern**:
- `add_bot` ✅
- `remove_player` ✅  
- `leave_room` ✅
- `join_room` ✅ (now fixed)

## 🚨 Quick Debug Commands

```javascript
// In browser console - check modal state
console.log('Modal state:', document.querySelector('[role="dialog"]'));

// Check WebSocket events  
// Add to useSocket hook temporarily:
socket.onmessage = (event) => console.log('WS received:', JSON.parse(event.data));

// Check room data structure
console.log('Room data:', roomData);
```

---

## Recent Fixes (Session 5) - Game Hanging Issues

### 14. Game Hanging at "Waiting for game phase: waiting" ✅
**Bug**: After clicking "Start Game" with 3 bots, game would hang indefinitely at "Waiting for game phase: waiting"
**Root Cause**: Two separate cascading issues:

#### **Backend Issue**: Bot Redeal Decision Automation Not Working
**Problem**: Game state machine reached PREPARATION phase but bots weren't making redeal decisions automatically
**Investigation**:
- Backend logs showed weak hands detected: `🃏 PREP_STATE_DEBUG: Found weak players: {'Bot 3'}`
- But current_weak_player was `None`, so bot manager wasn't triggered
- Game waited forever for redeal decisions that never came

**Fix**: Multi-part backend fix in `backend/engine/`:

1. **Added Missing Game Attributes** (`game.py:34-35`):
```python
# Player tracking for state machine
self.current_player = None         # Current player (for round start/declarations)
self.round_starter = None          # Player who starts the round
```

2. **Added Bot Redeal Event Handlers** (`bot_manager.py:61-64,421-506`):
```python
elif event_name == "weak_hands_found":
    await self._handle_weak_hands(data)
elif event_name == "redeal_decision_needed":
    await self._handle_redeal_decision(data)

async def _bot_redeal_decision(self, bot: Player):
    # Simple strategy: decline redeal 70% of the time to avoid infinite loops
    decline_probability = 0.7
    should_decline = random.random() < decline_probability
```

3. **Added Bot Manager Triggering** (`preparation_state.py:145-151`):
```python
# Trigger bot manager to handle bot decisions
await self._trigger_bot_redeal_decisions()

# Fallback: If no current weak player but we have weak players, trigger for all
if not self.current_weak_player and self.weak_players:
    for weak_player in self.weak_players:
        await self._trigger_bot_redeal_for_player(weak_player)
```

#### **Frontend Issue**: Phase Change Events Not Reaching Frontend
**Problem**: Backend successfully transitioned to DECLARATION phase, but frontend never received the `phase_change` events
**Investigation**:
- Backend logs: `DEBUG_WS: Successfully sent 'phase_change' to a client`
- Frontend logs: No `🎯 GAME_CONTEXT: Received phase_change event` messages
- Timing issue: Frontend connected **after** phase transitions completed

**Fix**: Added current phase sync when client connects (`backend/api/routes/ws.py:228-243`):
```python
# Send current game phase if game is running
if room.started and room.game_state_machine:
    current_phase = room.game_state_machine.get_current_phase()
    if current_phase:
        await registered_ws.send_json({
            "event": "phase_change",
            "data": {
                "phase": current_phase.value,
                "allowed_actions": allowed_actions,
                "phase_data": phase_data
            }
        })
```

### 15. Frontend WebSocket Connection Instability ✅
**Bug**: Frontend repeatedly connecting/disconnecting, causing infinite GamePhaseManager creation loops
**Root Cause**: React re-rendering issues causing multiple socket manager recreations

**Investigation**:
```javascript
// Console showed infinite loop:
GamePhaseManager.js:44 ✅ Initialized phases: Array(5)
GamePhaseManager.js:28 GamePhaseManager initialized  
GamePhaseManager.js:250 🧹 Destroying GamePhaseManager
useSocket.js:51 React hook: Disconnected {intentional: true}
```

**Fix**: Multi-part frontend stability fix:

1. **Prevented Multiple Socket Connections** (`GameContext.jsx:47-48`):
```javascript
// Wait for socket connection (useSocket handles this automatically)
// Removed manual socket.connect() call that conflicted with automatic connection
```

2. **Fixed React Re-rendering Loops** (`GameContext.jsx:42,65`):
```javascript
if (isInitialized) return; // Prevent re-initialization
}, [roomId, playerName, socket.isConnected]); // Wait for socket connection
```

3. **Stabilized Manager References** (`GameContext.jsx:35-37`):
```javascript
// Memoize phaseManager to prevent constant recreation  
const stableGameStateManager = useMemo(() => gameState.manager, [gameState.manager]);
const stableSocketManager = useMemo(() => socket.manager, [socket.manager]);
```

4. **Fixed Phase Manager Recreation** (`usePhaseManager.js:23-31`):
```javascript
// If we already have a manager with the same instances, don't recreate
if (phaseManagerRef.current && 
    currentStateManager === stateManager && 
    currentSocketManager === socketManager) {
  return;
}
```

### 16. DeclarationPhase UI Renderer Null Error ✅
**Bug**: `TypeError: Cannot read properties of null (reading 'showDeclarationPhase')`
**Root Cause**: DeclarationPhase trying to call UI methods on null renderer

**Fix**: Added null check in `DeclarationPhase.js:42-44`:
```javascript
// Initialize phase UI (optional)
if (this.uiRenderer) {
  this.uiRenderer.showDeclarationPhase();
}
```

## 🔧 Game State Machine Debug Pattern

When debugging game hanging issues, check this sequence:

### Backend State Machine Flow:
1. **Game Start**: `🔒 [Room XXX] Starting game`
2. **Phase Transition**: `🔄 STATE_MACHINE_DEBUG: Attempting transition from None to GamePhase.PREPARATION`
3. **Card Dealing**: `🎴 PREP_STATE_DEBUG: Using guaranteed no redeal dealing`
4. **Weak Hand Check**: `🔍 PREP_STATE_DEBUG: Checking transition conditions`
5. **Phase Broadcast**: `DEBUG_WS: Broadcasting event 'phase_change'`

### Frontend Reception Flow:
1. **Socket Connection**: `useSocket.js:41 React hook: Connected to room XXX`
2. **Context Initialization**: `🚀 GAME_CONTEXT: Socket connected, initializing game context`
3. **Phase Event**: `🎯 GAME_CONTEXT: Received phase_change event`
4. **Phase Transition**: `🔄 Phase transition requested: null → declaration`

### Common Failure Points:
- **Backend**: Bot automation not triggering → Game hangs waiting for decisions
- **WebSocket**: Events sent but not received → Frontend stuck on "waiting"
- **Frontend**: React re-rendering → Multiple managers created/destroyed
- **UI**: Null renderer → Phase transition crashes

## 🚨 Quick Debug Commands for Game State

```javascript
// Check current game phase
console.log('Current phase:', window.gamePhaseManager?.currentPhaseName);

// Check socket connection state  
console.log('Socket connected:', socket.isConnected);

// Check if phase events are being received
socket.on('phase_change', (data) => console.log('Phase change received:', data));
```

```python
# Backend - Check game state machine status
print(f"Current phase: {room.game_state_machine.current_phase}")
print(f"Bot manager games: {list(bot_manager.active_games.keys())}")
```

---

## Recent Fixes (Session 6) - Phase Name and Hand Data Issues

### 17. Game Stopping at "Waiting for game phase: to" ✅
**Bug**: Game successfully transitioned to Declaration phase on backend, but frontend showed "Waiting for game phase: to" instead of "declaration"
**Root Cause**: JavaScript build process (esbuild) was minifying class names:
- `DeclarationPhase` → `toPhase` (or similar minified name)  
- `this.constructor.name.replace('Phase', '').toLowerCase()` → `"to"`

**Investigation**:
```javascript
// Console logs showed the minification issue:
🚪 Entering phase: to
🔸 Entering to
GamePhaseManager.js:85 ✅ Phase transition complete: null → to
```

**Fix**: Explicitly set phase names in each phase constructor to avoid dependency on `constructor.name`:
```javascript
// Before (unreliable)
this.name = this.constructor.name.replace('Phase', '').toLowerCase();

// After (reliable)
export class DeclarationPhase extends BasePhase {
  constructor(stateManager, socketManager, uiRenderer) {
    super(stateManager, socketManager, uiRenderer);
    this.name = 'declaration'; // Explicit phase name
  }
}
```

**Files Updated**:
- `frontend/game/phases/DeclarationPhase.js` - Added `this.name = 'declaration'`
- `frontend/game/phases/RedealPhase.js` - Added `this.name = 'redeal'`
- `frontend/game/phases/TurnPhase.js` - Added `this.name = 'turn'`
- `frontend/game/phases/ScoringPhase.js` - Added `this.name = 'scoring'`
- `frontend/game/phases/BasePhase.js` - Updated all console logs to use reliable name
- `frontend/game/GamePhaseManager.js` - Updated all phase name references

### 18. Frontend Not Receiving Player Hand Data ✅
**Bug**: Declaration phase showed "Your hand: 0 pieces" instead of actual dealt cards
**Root Cause**: Phase change events didn't include player hand data, only phase metadata

**Investigation**:
```javascript
// Frontend showed empty hand
GameStateManager initialized with: {roomId: '00EAC0', playerName: 'Andy', round: 1, players: 0, hand: 0}

// But backend logs showed proper dealing:
Andy: ['HORSE_BLACK(5)', 'ELEPHANT_BLACK(9)', 'ADVISOR_BLACK(11)', ...]
```

**Fix**: Modified phase_change events to include all player hands:

**Backend Changes**:
```python
# backend/engine/state_machine/game_state_machine.py
async def _broadcast_phase_change_with_hands(self, phase: GamePhase):
    base_data = {
        "phase": phase.value,
        "allowed_actions": [action.value for action in self.get_allowed_actions()],
        "phase_data": self.get_phase_data()
    }
    
    # Add player hands to the data
    if hasattr(self, 'game') and self.game and hasattr(self.game, 'players'):
        players_data = {}
        for player in self.game.players:
            player_name = getattr(player, 'name', str(player))
            player_hand = [str(piece) for piece in player.hand] if hasattr(player, 'hand') and player.hand else []
            
            players_data[player_name] = {
                'hand': player_hand,
                'hand_size': len(player_hand)
            }
        
        base_data['players'] = players_data
    
    await self.broadcast_event("phase_change", base_data)
```

**Frontend Changes**:
```javascript
// frontend/src/contexts/GameContext.jsx
const unsubPhaseChange = socket.on('phase_change', async (data) => {
  console.log('🎯 GAME_CONTEXT: Received phase_change event:', data);
  
  // Update game state with player data if available
  if (data.players && gameState.manager) {
    const playerData = data.players[playerName];
    if (playerData && playerData.hand) {
      console.log('🃏 GAME_CONTEXT: Updating hand data:', playerData.hand);
      gameState.manager.updateHand(playerData.hand);
    }
  }
  
  // Continue with phase transition...
});
```

**Files Updated**:
- `backend/engine/state_machine/game_state_machine.py` - Added `_broadcast_phase_change_with_hands()`
- `backend/api/routes/ws.py` - Added hand data to client_ready phase_change events  
- `frontend/src/contexts/GameContext.jsx` - Added hand extraction and update logic

## 🔧 Build Process Debug Pattern

**Key Learning**: JavaScript minification can break code that relies on `constructor.name`:

### Problem Identification:
1. **Symptoms**: Phase names showing as meaningless strings ("to" instead of "declaration")
2. **Debug Method**: Add explicit logging of `constructor.name` values
3. **Root Cause**: Build tools minify class names for optimization

### Solution Strategy:
1. **Avoid Dynamic Names**: Don't rely on `constructor.name` in production code
2. **Explicit Constants**: Set phase names explicitly in constructors
3. **Fallback Patterns**: Use `this.name || this.constructor.name` for backward compatibility

### Prevention:
```javascript
// ❌ Fragile - breaks with minification
this.name = this.constructor.name.replace('Phase', '').toLowerCase();

// ✅ Reliable - explicit phase names
export class DeclarationPhase extends BasePhase {
  constructor(...args) {
    super(...args);
    this.name = 'declaration'; // Explicit and minification-safe
  }
}
```

## 🎮 Game State Synchronization Pattern

**Key Learning**: Frontend and backend must stay synchronized on game state:

### Data Flow Design:
1. **Backend Authority**: Backend holds authoritative game state (hands, phases, etc.)
2. **Event Broadcasting**: State changes broadcast to all clients via WebSocket
3. **Frontend Updates**: Clients extract relevant data and update local state
4. **Player Privacy**: Include all player data but let frontend filter what to display

### WebSocket Event Structure:
```javascript
// Comprehensive phase_change event structure
{
  "event": "phase_change",
  "data": {
    "phase": "declaration",
    "allowed_actions": ["DECLARE", "PLAYER_DISCONNECT"],
    "phase_data": { /* phase-specific metadata */ },
    "players": {
      "Andy": { "hand": ["HORSE_BLACK(5)", ...], "hand_size": 8 },
      "Bot 2": { "hand": ["CHARIOT_RED(8)", ...], "hand_size": 8 }
    }
  }
}
```

**Result**: 
- ✅ **Hand Count Fixed**: Game now shows "Your hand: 8 pieces" instead of "Your hand: 0 pieces"
- ✅ **Data Flow Working**: Console shows hand data being received: `🃏 GAME_CONTEXT: Updating hand data: (8) ['ADVISOR_BLACK(11)', 'HORSE_RED(6)', ...]`
- ❌ **Remaining Issues**: Cards still not visible in UI, declaration cannot proceed

### 19. Declaration Phase UI Not Showing Cards ✅ **COMPLETED**
**Bug**: Hand count is correct (8 pieces) but individual cards are not displayed in the UI
**Status**: **FIXED** - Individual cards now display correctly using GamePiece components

**Solution Applied**:
1. **Added GamePiece Import**: Updated `DeclarationPhase.jsx` to import `GamePiece` component
2. **Created renderHand() Function**: Added function following TurnPhase pattern to display individual cards
3. **Replaced Static Text**: Changed "Your hand: 8 pieces" to visual card grid with individual pieces
4. **Made Cards Non-Interactive**: Cards display for reference only (no selection during declaration)

**Files Modified**:
- `frontend/src/phases/DeclarationPhase.jsx` - Added card rendering functionality

**Result**: 
- ✅ **Individual Cards Displayed**: Players now see visual representations of their 8 pieces
- ✅ **Proper Grid Layout**: Cards arranged in 4-column grid with GamePiece styling
- ✅ **Hand Data Integration**: Successfully uses hand data received from backend via WebSocket
- ✅ **Declaration Input Working**: Bots successfully make declarations and UI updates

**Before Fix**:
```
Your hand: 8 pieces
Declaration Progress (0/0)
```

**After Fix**:
```
Your hand:
[🎴ELEPHANT_BLACK(9)] [🎴GENERAL_BLACK(13)] [🎴SOLDIER_BLACK(1)] [🎴CHARIOT_BLACK(7)]
[🎴CANNON_BLACK(3)]   [🎴HORSE_RED(6)]     [🎴CHARIOT_RED(8)]   [🎴ELEPHANT_RED(10)]
8 pieces total

Declaration Progress (3/4)
Bot 2: 3 piles | Bot 3: 1 piles | Bot 4: 1 piles
```

---

## Recent Issues (Session 7) - Bot Declaration Infinite Loop

### 20. Bot Infinite Declaration Loop ✅ **COMPLETED**
**Bug**: Bots continuously re-declare instead of stopping after successful declarations
**Status**: **FIXED** - Recursive call removed, single-pass declaration system working

**Root Cause Identified**:
1. **Recursive Call Issue**: After each bot declaration, `_bot_declare()` called `await self._handle_declaration_phase(bot.name)` recursively
2. **Loop Restart**: This restarted the entire declaration sequence, causing bots to declare multiple times
3. **Timing Race Condition**: State machine actions were queued (`{'success': True, 'queued': True}`) but bot manager immediately checked phase data before processing

**Solution Applied**:
1. **Removed Recursive Call**: Eliminated `await self._handle_declaration_phase(bot.name)` from `_bot_declare()` method
2. **Single-Pass Logic**: Let the natural for-loop in `_handle_declaration_phase()` process all bots sequentially in one pass
3. **Added Debug Logging**: Added `🔧 BOT_DECLARE_DEBUG: State machine result:` to track action processing
4. **Improved Phase Data Checking**: Enhanced logging with `All phase declarations: {}` for better debugging

**Files Modified**:
- `backend/engine/bot_manager.py` - Removed recursive call on line ~199, added debugging

**Result**: 
- ✅ **Single Bot Declarations**: Each bot declares exactly once: Bot 2→2 piles, Bot 3→1 pile, Bot 4→1 pile
- ✅ **Clean Termination**: "Player Andy is human, stopping bot declarations" - no infinite loops
- ✅ **No Validation Errors**: Eliminated "Wrong player turn" and "Invalid action" errors
- ✅ **Proper State Flow**: Declaration order ['Bot 2', 'Bot 3', 'Bot 4', 'Andy'] processes correctly

**Before Fix**:
```
✅ Bot Bot 2 declared 3
✅ Bot Bot 3 declared 1  
✅ Bot Bot 4 declared 1
[INFINITE LOOP - bots keep re-declaring]
Wrong player turn: Bot 4, expected: Andy
```

**After Fix**:
```
✅ Bot Bot 2 declared 2
✅ Bot Bot 3 declared 1  
✅ Bot Bot 4 declared 1
🔍 DECL_PHASE_DEBUG: Player Andy is human, stopping bot declarations
[CLEAN STOP - waiting for Andy's input]
```

### 21. Frontend Declaration Handler Null Error ⏳ **IN PROGRESS**
**Bug**: Frontend throws null pointer error when handling bot declarations, preventing Andy's declaration input
**Status**: **CRITICAL FRONTEND ISSUE** - Blocks human player interaction

**Symptoms**:
```
DeclarationPhase.js:291 🤖 Bot 2 declares 2 piles.
TypeError: Cannot read properties of null (reading 'updateDeclaration')
    at to.handleDeclare (DeclarationPhase.js:97:21)
```

**Impact**:
- ✅ **Bot declarations work**: Backend successfully processes Bot 2→2, Bot 3→1, Bot 4→1
- ✅ **Individual cards display**: Andy can see his 8 cards in the Declaration UI
- ❌ **Andy's declaration input missing**: No buttons/interface for Andy to make his declaration
- ❌ **Declaration progress broken**: Bot declarations trigger null errors in frontend

**Root Cause**: 
- `DeclarationPhase.js:97` calls `updateDeclaration` on a null object when processing bot declaration events
- This prevents the declaration state from updating properly, which blocks Andy's input interface

**Investigation Strategy**:
1. Examine `DeclarationPhase.js:97` to identify the null object
2. Check if `this.stateManager` or `this.uiRenderer` is null during bot declaration handling
3. Verify declaration event flow: WebSocket → Phase → State Manager → UI update
4. Add null guards and proper initialization order

**Backend Status**: ✅ Working perfectly - bots declare and stop, waiting for Andy
**Frontend Status**: ❌ Broken - can't process declarations or show Andy's input

**Priority**: High (blocks game progression after bot declarations complete)