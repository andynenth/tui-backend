# Disconnect Handling Plan for Liap Tui

## Overview
This document outlines all possible player disconnection scenarios in Liap Tui and provides a comprehensive plan for handling each case to ensure a smooth gaming experience.

## Current State Analysis

### What Currently Works
- WebSocket disconnection detection via `WebSocketDisconnect` exception
- Basic cleanup via `unregister()` function
- Frontend auto-reconnection with exponential backoff
- Connection status indicators in UI

### What's Missing
- In-game disconnect handling
- Player replacement mechanisms
- Game state preservation
- Reconnection grace periods
- Turn timeouts for disconnected players

## Disconnection Scenarios

### 1. Pre-Game Disconnections (Lobby/Room)

#### 1.1 Host Disconnects in Lobby
**Current Behavior:**
- Room is closed immediately
- All players receive `room_closed` event
- Everyone returns to lobby

**Proposed Behavior:**
- Same as current (room should close if host leaves before game starts)

**Implementation:** No change needed

#### 1.2 Regular Player Disconnects in Lobby
**Current Behavior:**
- Player is removed from room
- Others receive `player_left` event
- Room continues to exist

**Proposed Behavior:**
- Same as current

**Implementation:** No change needed

### 2. In-Game Disconnections

#### 2.1 Disconnect During PREPARATION Phase
**Scenario:** Player disconnects while cards are being dealt or during weak hand voting

**Current Behavior:**
- No handling - game likely gets stuck

**Proposed Behavior:**
- If during deal: Continue dealing, mark player as "disconnected"
- If during weak hand vote: Auto-vote "no" after timeout
- Give 30-second reconnection window
- If no reconnect: Replace with AI player

**Implementation:**
```python
# In PreparationState
async def handle_player_disconnect(self, player_name: str):
    self.disconnected_players[player_name] = {
        'time': datetime.now(),
        'phase_data': self.get_player_state(player_name)
    }
    
    # Set reconnection timer
    asyncio.create_task(self.start_reconnection_timer(player_name))
    
    # If voting, auto-vote after timeout
    if self.waiting_for_weak_hand_decision(player_name):
        asyncio.create_task(self.auto_vote_weak_hand(player_name))
```

#### 2.2 Disconnect During DECLARATION Phase
**Scenario:** Player disconnects while making pile count declaration

**Current Behavior:**
- No handling - declaration phase hangs

**Proposed Behavior:**
- 30-second reconnection window
- If no reconnect: AI declares based on hand strength
- Broadcast player status to others

**Implementation:**
```python
# In DeclarationState
async def handle_player_disconnect(self, player_name: str):
    if player_name in self.pending_declarations:
        # Start timeout timer
        asyncio.create_task(
            self.declaration_timeout(player_name, timeout=30)
        )
```

#### 2.3 Disconnect During TURN Phase
**Current Behavior:**
- No handling - game freezes if it's the disconnected player's turn

**Proposed Behavior:**
- If it's their turn: 15-second timeout, then AI plays
- If not their turn: Mark as disconnected, continue game
- 30-second reconnection window throughout

**Implementation:**
```python
# In TurnState
async def handle_player_disconnect(self, player_name: str):
    is_current_player = self.current_player == player_name
    
    if is_current_player:
        # Start turn timer
        await self.start_turn_timer(player_name, timeout=15)
    
    # Mark as disconnected
    await self.mark_player_disconnected(player_name)
```

#### 2.4 Disconnect During SCORING Phase
**Scenario:** Player disconnects while scores are being calculated

**Current Behavior:**
- No handling

**Proposed Behavior:**
- Continue scoring normally
- Mark player as disconnected
- Allow reconnection to see results

#### 2.5 Host Disconnects During Game
**Current Behavior:**
- No special handling

**Proposed Behavior:**
- Migrate host privileges to next player
- Continue game normally
- Notify all players of host change

**Implementation:**
```python
async def migrate_host(self, old_host: str):
    # Find next available player
    new_host = self.get_next_active_player(old_host)
    
    # Update room host
    self.room.host_name = new_host
    
    # Broadcast host change
    await self.broadcast_event("host_changed", {
        "old_host": old_host,
        "new_host": new_host
    })
```

### 3. Network-Specific Scenarios

#### 3.1 Temporary Network Blip (<5 seconds)
**Proposed Behavior:**
- Frontend reconnects automatically
- No game interruption
- Message queue ensures no lost actions

#### 3.2 Short Disconnection (5-30 seconds)
**Proposed Behavior:**
- Show "reconnecting" status to other players
- Pause turn timer if applicable
- Full state sync on reconnection

#### 3.3 Extended Disconnection (>30 seconds)
**Proposed Behavior:**
- Replace with AI player
- Allow player to spectate if they reconnect later
- Option to replace AI if player returns

## Technical Implementation

### 1. Backend Changes

#### 1.1 Enhanced Disconnect Detection
```python
# ws.py
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    try:
        # ... existing code ...
    except WebSocketDisconnect:
        await handle_disconnect(room_id, websocket)
    finally:
        await cleanup_connection(room_id, websocket)

async def handle_disconnect(room_id: str, websocket: WebSocket):
    player_info = get_player_from_websocket(websocket)
    
    if room_id == "lobby":
        await handle_lobby_disconnect(player_info)
    else:
        room = room_manager.get_room(room_id)
        if room and room.game_started:
            await handle_game_disconnect(room, player_info)
        else:
            await handle_room_disconnect(room, player_info)
```

#### 1.2 Player State Management
```python
class PlayerConnection:
    def __init__(self, player_name: str):
        self.player_name = player_name
        self.connection_status = "connected"
        self.disconnect_time = None
        self.reconnect_deadline = None
        self.is_ai_controlled = False
        self.websocket = None
```

#### 1.3 AI Player Integration
```python
class AIPlayer:
    def __init__(self, player_name: str, game_state: dict):
        self.player_name = player_name
        self.hand = game_state.get('hand', [])
        self.difficulty = "medium"
    
    async def make_declaration(self, game_context: dict) -> int:
        # AI logic for declaration
        pass
    
    async def make_turn(self, game_context: dict) -> list:
        # AI logic for playing pieces
        pass
```

### 2. Frontend Changes

#### 2.1 Enhanced Connection Status
```typescript
interface PlayerStatus {
  name: string;
  connected: boolean;
  isAI: boolean;
  lastSeen?: Date;
  reconnectDeadline?: Date;
}
```

#### 2.2 Disconnect UI Components
```jsx
const DisconnectBanner = ({ disconnectedPlayers, reconnectDeadlines }) => {
  return (
    <div className="disconnect-banner">
      {disconnectedPlayers.map(player => (
        <div key={player.name} className="disconnect-notice">
          {player.name} disconnected - AI playing 
          <Timer deadline={reconnectDeadlines[player.name]} />
        </div>
      ))}
    </div>
  );
};
```

### 3. Message Protocol Updates

#### 3.1 New WebSocket Events
```typescript
// Server -> Client
interface PlayerDisconnectedEvent {
  event: "player_disconnected";
  data: {
    player_name: string;
    reconnect_deadline: number; // timestamp
    ai_activated: boolean;
  };
}

interface PlayerReconnectedEvent {
  event: "player_reconnected";
  data: {
    player_name: string;
    resumed_control: boolean; // true if took back from AI
  };
}

interface HostMigratedEvent {
  event: "host_migrated";
  data: {
    old_host: string;
    new_host: string;
    reason: "disconnect" | "left_game";
  };
}
```

## Implementation Roadmap

### Phase 1: Foundation (Week 1)
1. Implement player connection tracking
2. Add disconnect/reconnect events
3. Create AI player framework

### Phase 2: Turn Management (Week 2)
1. Implement turn timeouts
2. Add AI decision making for turns
3. Handle turn handover to AI

### Phase 3: Phase-Specific Handling (Week 3)
1. Preparation phase disconnect handling
2. Declaration phase auto-declaration
3. Scoring phase continuity

### Phase 4: Host Migration (Week 4)
1. Implement host migration logic
2. Add host change notifications
3. Test edge cases

### Phase 5: UI/UX Polish (Week 5)
1. Add disconnect notifications
2. Implement reconnection timers
3. Create spectator mode for late reconnects

## Testing Strategy

### 1. Unit Tests
- Test each disconnect scenario
- Verify AI decision logic
- Test reconnection windows

### 2. Integration Tests
- Simulate network disconnections
- Test state synchronization
- Verify message queuing

### 3. Manual Testing Scenarios
1. Pull network cable during each phase
2. Close browser during gameplay
3. Simulate poor network conditions
4. Test mobile network switching

## Success Metrics
1. Game never gets stuck due to disconnection
2. Reconnection success rate >95% within 30 seconds
3. AI decisions are reasonable and timely
4. Clear communication to all players about connection status
5. Smooth host migration without game interruption

## Future Enhancements
1. Configurable disconnect timeouts per room
2. Different AI difficulty levels
3. Pause game feature for all players
4. Save/resume game functionality
5. Disconnect statistics and analytics