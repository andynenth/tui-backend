# Disconnect Handling Plan for Liap Tui

## Overview
This document outlines all possible player disconnection scenarios in Liap Tui and provides a comprehensive plan for handling each case to ensure a smooth gaming experience.

**Important Note:** Liap Tui already has a complete AI system (`backend/engine/ai.py`) and bot management system (`backend/engine/bot_manager.py`). This plan leverages the existing AI infrastructure rather than creating new AI components.

**Last Updated:** 2025-07-18 - Updated to reflect that backend now properly sends `is_bot` data to frontend

## Current State Analysis

### What Currently Works
- WebSocket disconnection detection via `WebSocketDisconnect` exception
- Basic cleanup via `unregister()` function
- Frontend auto-reconnection with exponential backoff
- Connection status indicators in UI
- **Complete AI system** with decision logic for all game phases
- **BotManager** that handles all bot actions through state machine
- **Player model** with `is_bot` flag for AI control
- **Backend properly sends `is_bot` data to frontend** (as of 2025-07-18)
- **Frontend PlayerAvatar component** displays bot-specific styling and icons
- **Bot thinking animations** with inner border spinner effect

### What's Missing
- In-game disconnect handling that converts players to bots
- Connection tracking to manage reconnection windows
- Integration between disconnect detection and bot activation
- State preservation for reconnecting players
- Disconnection grace period UI indicators

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
- If during weak hand vote: Bot takes over immediately
- Give 30-second reconnection window
- If no reconnect: Player remains bot-controlled

**Implementation:**
```python
# In PreparationState
async def handle_player_disconnect(self, player_name: str):
    player = self.game.get_player(player_name)
    
    # Store connection info for potential reconnection
    self.disconnected_players[player_name] = {
        'time': datetime.now(),
        'original_is_bot': player.is_bot,  # Store original state
        'reconnect_deadline': datetime.now() + timedelta(seconds=30)
    }
    
    # Convert to bot - existing BotManager will handle decisions
    player.is_bot = True
    
    # BotManager automatically handles weak hand decisions via phase_change events
    await self.broadcast_custom_event("player_disconnected", {
        "player_name": player_name,
        "ai_activated": True,
        "reconnect_deadline": self.disconnected_players[player_name]['reconnect_deadline']
    })
```

#### 2.2 Disconnect During DECLARATION Phase
**Scenario:** Player disconnects while making pile count declaration

**Current Behavior:**
- No handling - declaration phase hangs

**Proposed Behavior:**
- Bot takes over immediately using existing AI logic
- 30-second reconnection window
- Broadcast player status to others

**Implementation:**
```python
# In DeclarationState
async def handle_player_disconnect(self, player_name: str):
    player = self.game.get_player(player_name)
    
    # Convert to bot - BotManager will handle declaration automatically
    player.is_bot = True
    
    # Store disconnection info
    self.disconnected_players[player_name] = {
        'time': datetime.now(),
        'original_is_bot': False,
        'reconnect_deadline': datetime.now() + timedelta(seconds=30)
    }
    
    # BotManager will receive phase_change event and handle declaration
    # No additional code needed - enterprise architecture handles it!
```

#### 2.3 Disconnect During TURN Phase
**Current Behavior:**
- No handling - game freezes if it's the disconnected player's turn

**Proposed Behavior:**
- Bot takes over immediately (no delay needed)
- Existing BotManager handles turn logic with 0.5-1.5s realistic delays
- 30-second reconnection window throughout

**Implementation:**
```python
# In TurnState
async def handle_player_disconnect(self, player_name: str):
    player = self.game.get_player(player_name)
    
    # Convert to bot - BotManager handles turns automatically
    player.is_bot = True
    
    # Store disconnection info
    self.disconnected_players[player_name] = {
        'time': datetime.now(),
        'original_is_bot': False,
        'reconnect_deadline': datetime.now() + timedelta(seconds=30)
    }
    
    # If it's their turn, BotManager will play within 0.5-1.5 seconds
    # via existing enterprise architecture phase_change events
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

## Key Implementation Strategy

### Leveraging Existing AI System
The game already has a complete AI system that handles bot players:
- **`backend/engine/ai.py`**: Contains all AI decision logic
- **`backend/engine/bot_manager.py`**: Manages bot actions through state machine
- **`Player.is_bot`**: Flag that determines if a player is AI-controlled

**Simple Solution**: When a player disconnects, we just set `player.is_bot = True` and the existing bot system takes over automatically!

### Visual Design Approach
**UPDATE: Bot avatar display is already implemented!** The frontend PlayerAvatar component already handles bot vs human display based on the `isBot` prop, which is now properly sent from the backend.

**Current Implementation:**
1. **Human Players (Connected)**:
   - Letter avatar showing first letter of name
   - Full opacity, normal colors
   - No special indicators

2. **Bot Players (Including Disconnected)**:
   - ✅ **IMPLEMENTED**: Robot SVG icon instead of letter
   - ✅ **IMPLEMENTED**: "Thinking" animation (inner border spinner) when `isThinking={true}`
   - ✅ **IMPLEMENTED**: Distinct gray color scheme
   - Player name displayed in UI components

**Still Needed:**
3. **Disconnected Humans (Within Grace Period)**:
   - Grayed out letter avatar
   - Countdown timer overlay
   - "Reconnecting..." tooltip

This provides clear visual feedback without changing player names or disrupting game flow.

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

#### 1.3 Existing AI System Integration
```python
# The game already has a comprehensive AI system!
# backend/engine/ai.py - AI decision logic
# backend/engine/bot_manager.py - Bot management system

# When player disconnects, we simply:
# 1. Set player.is_bot = True
# 2. Let existing BotManager handle all AI decisions

async def activate_ai_for_disconnected_player(player: Player):
    """Convert disconnected player to AI control"""
    player.is_bot = True
    # BotManager will automatically handle this player
    # via existing enterprise architecture events

async def handle_player_reconnection(player_name: str, websocket: WebSocket):
    """Handle player reconnection within grace period"""
    player = game.get_player(player_name)
    
    # Check if within reconnection window
    if player_name in disconnected_players:
        deadline = disconnected_players[player_name]['reconnect_deadline']
        if datetime.now() < deadline:
            # Restore human control
            player.is_bot = disconnected_players[player_name]['original_is_bot']
            del disconnected_players[player_name]
            
            # Send full state sync
            await send_game_state(websocket, game)
            
            # Notify others
            await broadcast_custom_event("player_reconnected", {
                "player_name": player_name,
                "resumed_control": True
            })
        else:
            # Too late - player becomes spectator
            await send_spectator_view(websocket, game)
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

#### 2.2 Avatar-Based Bot Indicators
**UPDATE: Already implemented in PlayerAvatar.jsx!**

The current implementation already handles bot vs human display:
```jsx
// Current implementation in PlayerAvatar.jsx
export function PlayerAvatar({ name, isBot, isThinking, size = 'medium', theme = 'default' }) {
  // Bot players show robot icon
  if (isBot) {
    return (
      <div className={`player-avatar player-avatar--bot player-avatar--${size} ${theme === 'yellow' ? 'player-avatar--yellow' : ''} ${isThinking ? 'thinking' : ''}`}>
        {/* BotIcon SVG */}
      </div>
    );
  }
  
  // Human players show letter avatar
  return (
    <div className={`player-avatar player-avatar--${size} ${theme === 'yellow' ? 'player-avatar--yellow' : ''}`}>
      {name[0].toUpperCase()}
    </div>
  );
}
```

**Still needed**: Add disconnection grace period indicators (countdown timer, grayed out state)

#### 2.3 Disconnect Notifications
```jsx
const DisconnectNotification = ({ playerName, reconnectDeadline }) => {
  return (
    <Toast type="warning" duration={5000}>
      {playerName} disconnected - AI taking over
      <CountdownBar deadline={reconnectDeadline} />
    </Toast>
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

## Current Implementation Status (as of 2025-07-18)

### ✅ Completed
1. **Backend sends `is_bot` data**: Player objects now include `is_bot` flag in all WebSocket messages
2. **Bot avatar display**: PlayerAvatar component shows robot icon for bots, letter for humans
3. **Bot thinking animation**: Inner border spinner animation when bot is making decisions
4. **Bot styling**: Distinct gray color scheme for bot players
5. **AI system integration**: BotManager and AI decision logic fully operational

### ⏳ In Progress
1. **Disconnect detection**: Need to set `player.is_bot = True` when player disconnects
2. **Reconnection windows**: Track 30-second grace period for reconnection
3. **WebSocket events**: Add player_disconnected and player_reconnected events

### ❌ Not Started
1. **Grace period UI**: Countdown timers and "reconnecting" indicators
2. **Host migration**: Transfer host role when host disconnects
3. **Spectator mode**: Allow late reconnects to watch the game

## Implementation Roadmap

### Phase 1: Connection Tracking (Week 1)
1. Implement player connection tracking with reconnection windows
2. Add disconnect detection that sets `player.is_bot = True`
3. Create reconnection handler that restores `player.is_bot = False`

### Phase 2: Integration with Existing Bot System (Week 2)
1. ✅ **DONE**: BotManager already handles bot players
2. Add disconnect/reconnect WebSocket events
3. Test AI takeover in all game phases

### Phase 3: UI Updates (Week 3)
1. ✅ **DONE**: AI status indicators (robot avatars)
2. ✅ **DONE**: Bot thinking animations
3. ❌ **TODO**: Reconnection countdown timers
4. ❌ **TODO**: Disconnect notifications

### Phase 4: Host Migration (Week 4)
1. Implement host migration logic
2. Add host change notifications
3. Test edge cases

### Phase 5: Polish & Testing (Week 5)
1. Add spectator mode for late reconnects
2. Comprehensive testing of all scenarios
3. Performance optimization

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