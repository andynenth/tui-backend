# Bot Replacement Feature Merge Plan

## Overview
This document outlines the plan to merge the bot replacement feature from commit 2bfaa2f into the current bot-replacement branch (currently at commit 4af45b9).

## Feature Summary
The bot replacement system automatically activates bots when players disconnect and seamlessly returns control when they reconnect. This ensures games can continue smoothly despite network issues.

## Key Components to Merge

### 1. Backend Components

#### A. Connection Management System
**Files to create:**
- `/backend/api/websocket/connection_manager.py`
  - Tracks WebSocket connections and player states
  - Maps WebSocket IDs to player names
  - Manages connection status (CONNECTED, DISCONNECTED, RECONNECTING)
  - No grace period - players can reconnect anytime

- `/backend/api/websocket/message_queue.py`
  - Queues critical game events for disconnected players
  - Maintains message sequence numbers
  - Prioritizes critical events (phase_change, turn_resolved, etc.)
  - Delivers queued messages upon reconnection

#### B. WebSocket Handler Updates
**Files to modify:**
- `/backend/api/routes/ws.py`
  - Add WebSocket UUID tracking (`websocket._ws_id = str(uuid.uuid4())`)
  - Import connection_manager and message_queue_manager
  - Add `broadcast_with_queue()` function for disconnected player handling
  - Add comprehensive `handle_disconnect()` function
  - Update `client_ready` handler to register players in connection_manager
  - Add reconnection detection and message delivery logic
  - Pass original websocket object (not registered_ws) to disconnect handler

#### C. Player Model Updates
**Files to modify:**
- `/backend/engine/player.py`
  - Add connection tracking fields:
    ```python
    self.is_connected = True  # Current connection status
    self.disconnect_time = None  # When player disconnected
    self.original_is_bot = is_bot  # Store original bot state
    ```

#### D. Room Management Updates
**Files to modify:**
- `/backend/engine/room.py`
  - Add `is_host(player_name)` method
  - Add `migrate_host()` method with priority:
    1. First available human player
    2. First available bot if no humans
    3. None if room empty

#### E. Bot Manager Updates
**Files to modify:**
- `/backend/engine/bot_manager.py`
  - Add handler for `player_bot_activated` event
  - Add `_handle_bot_activation()` method
  - Ensure bot takes over when player disconnects mid-turn

### 2. Frontend Components

#### A. Type Definitions
**Files to modify:**
- `/frontend/src/services/types.ts`
  - Add to Player interface:
    ```typescript
    is_connected?: boolean;
    disconnect_time?: string;
    original_is_bot?: boolean;
    ```
  - Add to GameState interface:
    ```typescript
    disconnectedPlayers: string[];
    host: string | null;
    ```
  - Add to ConnectionData interface:
    ```typescript
    playerName?: string;
    ```
  - Add new event types to GameEventType:
    ```typescript
    | 'player_disconnected'
    | 'player_reconnected'
    | 'host_changed'
    | 'queued_messages'
    ```

#### B. GameService Updates
**Files to modify:**
- `/frontend/src/services/GameService.ts`
  - Add disconnected players tracking in state
  - Add event handlers:
    - `handlePlayerDisconnected()`
    - `handlePlayerReconnected()`
    - `handleHostChanged()`
    - `handleQueuedMessages()`
  - Update player state preservation in phase changes
  - Add connection status to player data handling

#### C. NetworkService Updates
**Files to modify:**
- `/frontend/src/services/NetworkService.ts`
  - Pass playerName in connection options
  - Update connection tracking

### 3. Implementation Order

1. **Phase 1: Backend Infrastructure**
   - Create connection_manager.py
   - Create message_queue.py
   - Update player.py with connection fields
   - Update room.py with host migration

2. **Phase 2: WebSocket Integration**
   - Update ws.py with UUID tracking
   - Add disconnect handling
   - Add player registration
   - Add reconnection logic

3. **Phase 3: Bot Activation**
   - Update bot_manager.py with activation handler
   - Test bot takeover on disconnect

4. **Phase 4: Frontend Integration**
   - Update type definitions
   - Update GameService with event handlers
   - Add UI indicators for disconnected players

5. **Phase 5: Testing & Refinement**
   - Test disconnect/reconnect flow
   - Test host migration
   - Test message queueing
   - Fix any edge cases

## Key Implementation Details

### WebSocket ID Tracking
- Each WebSocket gets a UUID on connection: `websocket._ws_id = str(uuid.uuid4())`
- This ID is used to track which player disconnected
- Must use original websocket object, not registered wrapper

### Player Registration
- Players must be registered when `client_ready` event is received
- Registration includes: room_id, player_name, websocket_id
- Both lobby and game room connections need registration

### Bot Activation Flow
1. WebSocket disconnects
2. ConnectionManager marks player as disconnected
3. Player object updated: `is_bot = True`, `is_connected = False`
4. Message queue created for the player
5. Bot manager notified if it's the player's turn
6. Host migration triggered if needed

### Reconnection Flow
1. Player connects with same name
2. System detects previous disconnect state
3. Player restored: `is_bot = False`, `is_connected = True`
4. Queued messages delivered
5. Message queue cleared

### Critical Events to Queue
- phase_change
- turn_resolved
- round_complete
- game_ended
- score_update
- host_changed

## Testing Strategy

1. **Unit Tests**
   - Connection manager state tracking
   - Message queue operations
   - Host migration logic

2. **Integration Tests**
   - Full disconnect/reconnect flow
   - Bot activation during different phases
   - Message delivery on reconnection

3. **Manual Testing**
   - Browser close during game
   - Network interruption simulation
   - Multiple disconnects/reconnects
   - Host disconnection

## Migration Notes

### From Current State
The current branch has basic ws.py without connection tracking. We need to:
1. Add the connection management infrastructure
2. Update existing WebSocket handling
3. Ensure backward compatibility

### Breaking Changes
None expected - the feature is additive and doesn't change existing APIs.

### Configuration
No new configuration required. The system works automatically.

## Success Criteria

1. Players can disconnect at any time without breaking the game
2. Bots take over immediately and play conservatively
3. Players can reconnect and resume control
4. No game events are lost during disconnection
5. Host migration works smoothly
6. UI clearly shows disconnected players

## Rollback Plan

If issues arise:
1. Remove connection_manager and message_queue imports
2. Remove disconnect handling from ws.py
3. Remove connection fields from Player
4. Revert to simple disconnect behavior

The feature is designed to be modular and can be disabled without affecting core game functionality.

## Implementation Checklist

### Phase 1: Backend Infrastructure

#### Connection Manager
- [x] Create `/backend/api/websocket/connection_manager.py` with the following:
  - [x] Define `PlayerConnection` dataclass with fields: `player_name`, `room_id`, `websocket_id`, `status`, `disconnect_time`, `is_host`
  - [x] Implement `ConnectionManager` class with empty `__init__` method
  - [x] Add `async def register_player(self, room_id: str, player_name: str, websocket_id: str) -> None` method
  - [x] Add `async def handle_disconnect(self, websocket_id: str) -> Optional[PlayerConnection]` method
  - [x] Add `async def check_reconnection(self, room_id: str, player_name: str) -> bool` method
  - [x] Add `async def get_player_by_websocket(self, websocket_id: str) -> Optional[PlayerConnection]` method
  - [x] Add `async def cleanup_room(self, room_id: str) -> None` method
  - [x] Initialize singleton instance: `connection_manager = ConnectionManager()`

#### Message Queue Manager
- [x] Create `/backend/api/websocket/message_queue.py` with the following:
  - [x] Define `QueuedMessage` dataclass with fields: `event`, `data`, `sequence_number`, `timestamp`
  - [x] Implement `MessageQueueManager` class with empty `__init__` method
  - [x] Add `async def queue_message(self, room_id: str, player_name: str, event: str, data: Any) -> bool` method
  - [x] Add `async def get_queued_messages(self, room_id: str, player_name: str) -> List[Dict[str, Any]]` method
  - [x] Add `async def clear_queue(self, room_id: str, player_name: str) -> None` method
  - [x] Add `_should_queue_event(self, event: str) -> bool` method that returns True for critical events
  - [x] Initialize singleton instance: `message_queue_manager = MessageQueueManager()`

#### Player Model Updates
- [x] Open `/backend/engine/player.py` and add the following fields to `__init__` method after line 19:
  ```python
  self.is_connected = True  # Whether player is currently connected
  self.disconnect_time = None  # When player disconnected
  self.original_is_bot = is_bot  # Store original bot state for reconnection
  ```

#### Room Management Updates
- [x] Open `/backend/engine/room.py` and add after line 520:
  - [x] Add `def is_host(self, player_name: str) -> bool:` method that returns `player_name == self.host_name`
  - [x] Add `def migrate_host(self) -> Optional[str]:` method with logic:
    - [x] Loop through players to find first connected human player
    - [x] If no humans, find first bot
    - [x] Update `self.host_name` to new host
    - [x] Return new host name or None

### Phase 2: WebSocket Integration

#### WebSocket Handler Base Updates
- [x] Open `/backend/api/routes/ws.py` and add imports after line 5:
  ```python
  import uuid
  from backend.api.websocket.connection_manager import connection_manager
  from backend.api.websocket.message_queue import message_queue_manager
  from backend.engine.player import Player
  from typing import Optional
  ```

#### WebSocket UUID Tracking
- [x] In `/backend/api/routes/ws.py`, modify `websocket_endpoint` function (line 24):
  - [x] Add after line 28 (after await register): `websocket._ws_id = str(uuid.uuid4())`
  - [x] Add logging: `logger.info(f"WebSocket connected: room={room_id}, ws_id={websocket._ws_id}")`

#### Broadcast with Queue Function
- [x] In `/backend/api/routes/ws.py`, add new function before `websocket_endpoint`:
  ```python
  async def broadcast_with_queue(room_id: str, event: str, data: dict):
      """Broadcast to connected players and queue for disconnected ones"""
      # Implementation here
  ```
  - [x] Get all players from room manager
  - [x] For each player, check if connected via connection_manager
  - [x] If connected, use regular broadcast
  - [x] If disconnected, use message_queue_manager.queue_message

#### Disconnect Handler
- [x] In `/backend/api/routes/ws.py`, add new function after `broadcast_with_queue`:
  ```python
  async def handle_disconnect(room_id: str, websocket: WebSocket):
      """Handle player disconnect with bot activation"""
      # Implementation here
  ```
  - [x] Get websocket ID: `ws_id = getattr(websocket, '_ws_id', None)`
  - [x] Call connection_manager.handle_disconnect(ws_id)
  - [x] If player found, update player object: `player.is_bot = True`, `player.is_connected = False`
  - [x] Broadcast player_disconnected event
  - [x] Check for host migration if needed
  - [x] Notify bot manager with player_bot_activated event

#### Update WebSocket Exception Handler
- [x] In `/backend/api/routes/ws.py`, find the WebSocketDisconnect exception handler (around line 31):
  - [x] Change `except WebSocketDisconnect:` block to:
    ```python
    except WebSocketDisconnect:
        unregister(room_id, websocket)
        await handle_disconnect(room_id, websocket)  # Use original websocket, not registered_ws
    ```

#### Player Registration Handler
- [x] In `/backend/api/routes/ws.py`, find the client_ready event handler:
  - [x] After successful room join, add:
    ```python
    ws_id = getattr(websocket, '_ws_id', None)
    if ws_id and event_data.get("player_name"):
        await connection_manager.register_player(room_id, event_data["player_name"], ws_id)
    ```

#### Reconnection Detection
- [x] In `/backend/api/routes/ws.py`, modify the client_ready handler:
  - [x] Before room join, check reconnection:
    ```python
    if await connection_manager.check_reconnection(room_id, player_name):
        # Handle reconnection logic
    ```
  - [x] If reconnecting, restore player state and deliver queued messages
  - [x] Broadcast player_reconnected event

### Phase 3: Bot Activation

#### Bot Manager Updates
- [x] Open `/backend/engine/bot_manager.py`:
  - [x] Fix import at line 1 by adding `Any` to typing imports: `from typing import Any, Dict, List, Optional, Set`
  - [x] In `__init__` method, add to self._handlers dict:
    ```python
    "player_bot_activated": self._handle_bot_activation,
    ```
  - [x] Add new method after `_handle_turn_start`:
    ```python
    async def _handle_bot_activation(self, event: GameEvent) -> None:
        """Handle when a player disconnects and bot takes over"""
        # Implementation here
    ```
  - [x] Check if it's the bot's turn and trigger immediate action

### Phase 4: Frontend Integration

#### Type Definitions
- [x] Open `/frontend/src/services/types.ts`:
  - [x] Add to Player interface (after line 83):
    ```typescript
    is_connected?: boolean;
    disconnect_time?: string;
    original_is_bot?: boolean;
    ```
  - [x] Add to GameState interface (after line 147):
    ```typescript
    disconnectedPlayers: string[];
    host: string | null;
    ```
  - [x] Add to ConnectionData interface (after line 28):
    ```typescript
    playerName?: string;
    ```
  - [x] Add to GameEventType union (after line 298):
    ```typescript
    | 'player_disconnected'
    | 'player_reconnected'
    | 'host_changed'
    | 'queued_messages'
    ```

#### GameService Event Handlers
- [x] Open `/frontend/src/services/GameService.ts`:
  - [x] Add to state initialization in `getInitialState()` method:
    ```typescript
    disconnectedPlayers: [],
    host: null,
    ```
  - [x] Add new event handlers in `setupNetworkListeners()` method:
    - [x] `handlePlayerDisconnected(data: any)` - Update disconnectedPlayers array
    - [x] `handlePlayerReconnected(data: any)` - Remove from disconnectedPlayers
    - [x] `handleHostChanged(data: any)` - Update host field
    - [x] `handleQueuedMessages(data: any)` - Process array of queued events
  - [x] Update `handlePhaseChange()` to preserve is_connected status when updating players

#### NetworkService Updates
- [x] Open `/frontend/src/services/NetworkService.ts`:
  - [x] Modify `connectToRoom()` method to include playerName in connection options
  - [x] Update ConnectionData structure when establishing connection

#### UI Components (Optional)
- [ ] Add visual indicators for disconnected players in player list components
- [ ] Add "BOT" indicator when player.is_bot && player.original_is_bot === false
- [ ] Add reconnection status messages

### Phase 5: Testing & Verification

#### Unit Tests
- [x] Create `/backend/tests/test_connection_manager.py`:
  - [x] Test player registration
  - [x] Test disconnect handling
  - [x] Test reconnection detection
  - [x] Test room cleanup

- [x] Create `/backend/tests/test_message_queue.py`:
  - [x] Test message queueing
  - [x] Test queue retrieval
  - [x] Test queue clearing
  - [x] Test critical event filtering

#### Integration Tests
- [x] Create `/backend/tests/test_bot_replacement_flow.py`:
  - [x] Test full disconnect → bot activation → reconnect flow
  - [x] Test host migration scenarios
  - [x] Test message delivery on reconnection
  - [x] Test bot behavior during different game phases

#### Manual Testing Scenarios
- [ ] Test browser close during different phases:
  - [ ] During preparation phase
  - [ ] During declaration phase
  - [ ] During player's turn
  - [ ] During other player's turn
  - [ ] During scoring phase

- [ ] Test network interruption:
  - [ ] Use browser dev tools to simulate offline
  - [ ] Verify bot takes over
  - [ ] Go back online and verify reconnection

- [ ] Test host disconnect:
  - [ ] Have host close browser
  - [ ] Verify host migration to next human player
  - [ ] Verify game continues

- [ ] Test multiple disconnects:
  - [ ] Have 2+ players disconnect
  - [ ] Verify all replaced by bots
  - [ ] Verify game continues
  - [ ] Test reconnection of multiple players

#### Verification Steps
- [ ] Run `python test_enterprise_architecture.py` to verify enterprise patterns
- [ ] Run `python test_turn_number_sync.py` to verify no sync bugs
- [ ] Check backend logs for proper disconnect detection
- [ ] Verify no WebSocket errors in browser console
- [ ] Confirm game state consistency after reconnection

### Post-Implementation
- [ ] Update documentation with bot replacement feature details
- [ ] Add feature flag to enable/disable bot replacement (optional)
- [ ] Monitor logs for any edge cases or errors
- [ ] Gather user feedback on reconnection experience