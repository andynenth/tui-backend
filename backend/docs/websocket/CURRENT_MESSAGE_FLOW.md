# Current WebSocket Message Flow

## Date: 2025-01-28
## Status: Pre-Phase 2 Documentation

### Overview

This document maps the current WebSocket message flow in the system after Phase 7 legacy code removal. It identifies which code belongs to infrastructure vs business logic to guide the Phase 2 refactoring.

### Current Architecture

```
WebSocket Client
        ↓
    ws.py (Mixed Layer)
        ↓
    adapter_wrapper
        ↓
    integrated_adapter_system
        ↓
    Clean Architecture
```

## Message Flow Analysis

### 1. Connection Establishment (Infrastructure)

**Location**: `api/routes/ws.py` lines 343-399
**Components**:
- WebSocket acceptance
- Connection ID generation (line 350)
- Connection registration (line 361)
- Room existence check (lines 366-398)

**Infrastructure Code**:
```python
# Lines 349-363: Pure infrastructure
websocket._ws_id = str(uuid.uuid4())
connection_id = await register(room_id, websocket)
websocket._connection_id = connection_id
```

**Business Logic Mixed In**:
```python
# Lines 371-395: Business logic (room validation)
room = await uow.rooms.get_by_id(room_id)
if not room:
    await websocket.send_json({"event": "room_not_found", ...})
```

### 2. Message Reception Loop (Infrastructure)

**Location**: `api/routes/ws.py` lines 400-449
**Components**:
- Message reception (line 402)
- Message validation (lines 405-416)
- Adapter routing (lines 424-432)

**Infrastructure Code**:
```python
# Lines 402-416: Pure infrastructure
message = await websocket.receive_json()
is_valid, error_msg, sanitized_data = validate_websocket_message(message)
```

### 3. Message Routing (Business Logic)

**Location**: Multiple files
**Current Flow**:
1. `ws_adapter_wrapper.try_handle_with_adapter()` (lines 424-426)
2. `integrated_adapter_system.handle_message()` 
3. Individual adapter handlers

**Event Categories**:

#### Connection Events (4 events)
- `ping` → PingAdapter
- `client_ready` → ClientReadyAdapter  
- `ack` → AckAdapter
- `sync_request` → SyncRequestAdapter

#### Room Management Events (6 events)
- `create_room` → room_adapters
- `join_room` → room_adapters
- `leave_room` → room_adapters
- `get_room_state` → room_adapters
- `add_bot` → room_adapters
- `remove_player` → room_adapters

#### Lobby Events (2 events)
- `request_room_list` → lobby_adapters
- `get_rooms` → lobby_adapters

#### Game Events (10 events)
- `start_game` → game_adapters
- `declare` → game_adapters
- `play` → game_adapters
- `play_pieces` → game_adapters
- `request_redeal` → game_adapters
- `accept_redeal` → game_adapters
- `decline_redeal` → game_adapters
- `redeal_decision` → game_adapters
- `player_ready` → game_adapters
- `leave_game` → game_adapters

### 4. Disconnection Handling (Mixed)

**Location**: `api/routes/ws.py` lines 74-209
**Components**:
- WebSocket disconnection detection
- Player state management (business logic)
- Connection cleanup (infrastructure)
- Bot activation logic (business logic)

**Infrastructure Code**:
```python
# Connection tracking and cleanup
connection_id = getattr(websocket, "_connection_id", None)
await unregister(connection_id)
```

**Business Logic**:
```python
# Lines 89-173: All player/room/game state management
if connection and connection.player_name and connection.room_id != "lobby":
    # Complex business logic for handling player disconnection
```

### 5. Helper Functions (Mixed)

**Location**: `api/routes/ws.py` lines 35-72

#### `get_current_player_name()` (Infrastructure)
- Pure connection lookup function

#### `broadcast_with_queue()` (Business Logic)
- Message queuing for disconnected players
- Room state queries

#### `start_cleanup_task()` (Infrastructure)
- Background task management

## Code Classification Summary

### Infrastructure Components
1. WebSocket lifecycle management
2. Connection registration/tracking
3. Message reception and sending
4. Rate limiting checks
5. Basic validation
6. Background task management

### Business Logic Components
1. Room existence validation
2. Player state management
3. Game state handling
4. Message queuing logic
5. Bot activation rules
6. All adapter routing decisions

### Mixed/Coupled Areas
1. `websocket_endpoint()` - Mixes connection handling with room validation
2. `handle_websocket_disconnect()` - Mixes cleanup with game logic
3. `broadcast_with_queue()` - Infrastructure function with business queries

## Refactoring Targets for Phase 2

### To Extract to Infrastructure Layer
- Lines 349-363: Connection establishment
- Lines 402-416: Message reception and validation  
- Lines 74-85, 206-209: Basic disconnect handling
- Connection tracking functions

### To Extract to Application Layer
- Lines 371-395: Room validation logic
- Lines 424-432: Message routing decisions
- Lines 89-173: Disconnect business logic
- Lines 42-63: Message queue business logic

### To Keep in ws.py (Thin Layer)
- Route definition
- Basic orchestration between infrastructure and application

## Message Format

### Incoming Message Structure
```json
{
    "event": "string",  // Event name (legacy format)
    "action": "string", // Action name (adapter format)
    "data": {}          // Event-specific data
}
```

### Outgoing Message Structure
```json
{
    "event": "string",  // Event type
    "data": {},         // Response data
    "error": "string"   // Optional error message
}
```

## Dependencies

### Current Import Structure
```
ws.py imports:
├── infrastructure/websocket/connection_singleton (broadcast, register, unregister)
├── api/validation (validate_websocket_message)
├── api/middleware/websocket_rate_limit (rate limiting)
├── api/websocket/connection_manager (connection tracking)
├── api/websocket/message_queue (queue management)
├── api/routes/ws_adapter_wrapper (adapter integration)
├── infrastructure/dependencies (get_unit_of_work, services)
└── application/services/* (room, lobby services)
```

## Next Steps

This analysis shows clear separation points for Phase 2:
1. Extract infrastructure components to dedicated layer
2. Create message router for business logic
3. Simplify ws.py to thin orchestration layer
4. Maintain backward compatibility during transition