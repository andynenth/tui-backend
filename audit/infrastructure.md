# Infrastructure Audit

## Overview
This document contains detailed analysis of all infrastructure components including room management, bot systems, shared instances, and event storage.

---

## 1. `/backend/engine/room.py`

**Status**: ✅ Checked  
**Purpose**: Manages individual game room state including players, room status, and game lifecycle. Provides thread-safe operations for room management.

**Classes/Functions**:

- `Room` class - Core room management class
- `__init__()` - Initializes room with host and default bots
- `assign_slot_safe()` - Thread-safe slot assignment with operation tracking
- `join_room_safe()` - Thread-safe room joining with duplicate prevention
- `start_game_safe()` - **Key method**: Thread-safe game starting (called by ws.py line 1246)
- `_get_slot_state_snapshot()` - Helper for debugging slot states
- `validate_state()` - Enhanced state validation with detailed reporting
- `get_occupied_slots()`, `get_total_slots()`, `is_full()` - Room capacity utilities
- `summary()` - Generates room state summary for clients
- `assign_slot()` - Direct slot assignment (called by safe version)
- `join_room()` - Direct room joining (called by safe version)
- `exit_room()` - Player departure handling
- `start_game()` - **Dead Code**: Legacy game starting method (superseded by start_game_safe)
- `get_kicked_player()` - Determines if assignment would kick existing player
- `_generate_operation_id()` - Operation tracking utility

**Dead Code**:

- `start_game()` method (lines 474-489) - Legacy synchronous version, replaced by `start_game_safe()`
- Thai comment on line 203: `# สร้าง Game instance` (should be English)

**Dependencies**:

- Imports:
  - `engine.game.Game` - Core game logic
  - `engine.player.Player` - Player representation
  - `engine.state_machine.core.GamePhase` - Game phase enumeration
  - `engine.state_machine.game_state_machine.GameStateMachine` - State machine management
  - `.bot_manager.BotManager` (dynamic import in start_game_safe) - Bot AI management
- Used by: 
  - `backend.api.routes.ws.py` - WebSocket handler calls room methods
  - `backend.shared_instances` - Room manager maintains room instances

---

## 2. `/backend/engine/bot_manager.py`

**Status**: ✅ Checked  
**Purpose**: **Critical Bot AI System**: Centralized bot management with enterprise architecture compliance. Manages bot actions, prevents duplicate actions, and coordinates with state machine for automatic broadcasting.

**Classes/Functions**:

- `BotManager` class - Singleton bot management system
- `__new__()` - Singleton pattern implementation
- `__init__()` - Initializes active games dictionary
- `register_game()` - **Key method**: Registers game for bot management (called by room.py line 219)
- `unregister_game()` - Removes game from bot management
- `handle_game_event()` - **Key method**: Handles game events that trigger bot actions
- `GameBotHandler` class - Handles bot actions for specific game
- `__init__()` - Initializes game-specific bot handler
- `_get_game_state()` - Retrieves current game state
- `_generate_action_hash()` - Creates hash for duplicate detection
- `_is_duplicate_action()` - Prevents duplicate bot actions
- `_should_skip_bot_trigger()` - Determines if bot should skip action
- `handle_event()` - **Key method**: Routes events to appropriate handlers
- `_handle_enterprise_phase_change()` - Handles phase changes with enterprise compliance
- `_handle_declaration_phase()` - Manages bot declarations
- `_bot_declare()` - Executes bot declaration action
- `_handle_round_start()` - Handles round start events
- `_handle_turn_phase()` - Manages bot turn actions
- `_bot_play_turn()` - Executes bot piece play action
- `_handle_preparation_phase()` - Handles bot redeal decisions
- `_bot_redeal_decision()` - Executes bot redeal choice

**Dead Code**:

- None identified - All methods appear to be used for bot AI coordination

**Dependencies**:

- Imports:
  - `engine.ai` - AI decision-making logic
  - `engine.player.Player` - Player entity management
  - `engine.state_machine.core` (ActionType, GameAction) - State machine integration
- Used by:
  - `backend.engine.room.py` - Creates and registers bot manager (lines 217-221)
  - `backend.engine.state_machine.game_state_machine.py` - Notifies bot manager of events (multiple locations)

---

## 3. `/backend/engine/room_manager.py`

**Status**: ✅ Checked  
**Purpose**: Room lifecycle management service that handles creation, retrieval, deletion, and listing of all game rooms in the system.

**Classes/Functions**:
- `RoomManager` - Main class for managing all active game rooms
- `__init__()` - Initializes empty rooms dictionary
- `create_room(host_name)` - Creates new room with unique 6-character ID
- `get_room(room_id)` - Safely retrieves room by ID
- `delete_room(room_id)` - Removes room from manager
- `list_rooms()` - Returns all available (non-started) rooms

**Key Features**:
- **Unique ID Generation**: 6-character uppercase hexadecimal room IDs using UUID
- **Safe Retrieval**: Uses `.get()` method to avoid KeyError exceptions
- **Room Filtering**: Only lists rooms that haven't started games
- **Dictionary Storage**: Simple in-memory storage using room_id as key

**Dead Code**:
- None identified - All methods are actively used in the system

**Dependencies**:
- **Imports**: `uuid` (ID generation), `typing.Dict` (type hints), `engine.room.Room` (Room class)
- **Used by**: `/backend/shared_instances.py` (singleton creation), `/backend/api/routes/ws.py` (WebSocket operations), `/backend/api/routes/routes.py` (HTTP endpoints)

**Security Notes**:
- Room IDs are generated using UUID4 which provides good uniqueness
- No input validation on host_name parameter - potential for injection if not validated upstream

---

## 4. `/backend/shared_instances.py`

**Status**: ✅ Checked  
**Purpose**: Global singleton management module that provides shared instances of core manager classes for consistent state across the entire application.

**Classes/Functions**:
- `shared_room_manager` - Global RoomManager instance (line 10)
- `shared_bot_manager` - Global BotManager instance (line 11)

**Key Features**:
- **Singleton Pattern**: Ensures single instance of managers across application
- **Global State Management**: Provides consistent room and bot state
- **Simple Module Design**: Clean, minimal approach to dependency injection
- **Application-Wide Access**: Allows all components to share same manager instances

**Dead Code**:
- None identified - Simple module with essential global instances

**Dependencies**:
- **Imports**: `engine.bot_manager.BotManager` (bot management), `engine.room_manager.RoomManager` (room management)
- **Used by**: `/backend/api/routes/ws.py` (WebSocket handlers), `/backend/api/routes/routes.py` (HTTP endpoints), any module needing shared state

**Security Notes**:
- Global instances are instantiated at module load time
- No authentication or access control on shared instances - relies on application-level security

---

---

## 5. `/backend/socket_manager.py`

**Status**: ✅ Checked  
**Purpose**: Enterprise-grade WebSocket connection manager providing reliable message delivery, acknowledgment tracking, automatic retry, and real-time broadcasting for all game rooms.

**Classes/Functions**:
- `PendingMessage` - Dataclass for tracking unacknowledged messages with retry logic
- `MessageStats` - Dataclass for delivery statistics and latency tracking
- `SocketManager` - Main WebSocket management class with reliable messaging
- `__init__()` - Initializes connection pools, queues, and retry worker
- `_process_broadcast_queue(room_id)` - Async queue processor with error handling
- `register(room_id, websocket)` - WebSocket registration with connection tracking
- `unregister(room_id, websocket)` - Safe WebSocket cleanup with game protection
- `broadcast(room_id, event, data)` - Enhanced broadcasting with queue management
- `send_with_ack()` - Reliable message delivery with acknowledgment requirement
- `handle_ack()` - Acknowledgment processing with duplicate detection
- `_message_retry_worker()` - Background worker for automatic message retry
- `_retry_message()` - Individual message retry with exponential backoff
- `_handle_expired_message()` - Cleanup for failed/expired messages
- `request_client_sync()` - Client synchronization for missing events
- `get_message_stats()` - Comprehensive delivery statistics
- `get_room_stats()` - Connection and queue monitoring
- `ensure_lobby_broadcast_task()` - Lobby-specific broadcast management

**Key Features**:
- **Reliable Messaging**: Acknowledgment-based delivery with automatic retry
- **Connection Management**: Thread-safe registration/unregistration with statistics
- **Queue Processing**: Async broadcast queues with error handling and cleanup
- **Retry Logic**: Exponential backoff with configurable timeout and max attempts
- **Statistics Tracking**: Comprehensive metrics for latency, success rates, and failures
- **Game Protection**: Prevents cleanup of active game rooms during disconnections
- **Lobby Optimization**: Special handling for lobby broadcast reliability

**Dead Code**:
- Multiple empty debug print statements in `broadcast()` method (lines 288-330)
- Redundant JSON import inside exception handler (line 143)
- Unused `pass` statements in lobby debugging sections

**Dependencies**:
- **Imports**: `asyncio` (async operations), `json` (serialization), `time` (timestamps), `dataclasses` (data structures), `datetime` (timing), `typing` (type hints), `fastapi.websockets.WebSocket` (WebSocket handling)
- **Used by**: `/backend/api/routes/ws.py` (WebSocket event handling), `/backend/api/routes/routes.py` (HTTP endpoints), `/backend/shared_instances` (global access)

**Security Notes**:
- No authentication on WebSocket connections - relies on application-level security
- Message acknowledgment provides delivery guarantees but not encryption
- Room isolation prevents cross-room message leakage
- Exponential backoff prevents retry flooding

---

## 6. `/backend/api/services/event_store.py`

**Status**: ✅ Checked  
**Purpose**: **Event Sourcing System**: Provides persistent event storage, state reconstruction, and client recovery capabilities using SQLite database.

**Classes/Functions**:

- `GameEvent` - Dataclass representing a stored game event
- `to_dict()` - Converts GameEvent to dictionary for JSON serialization
- `from_dict()` - Creates GameEvent from dictionary
- `EventStore` class - Main event storage system
- `__init__()` - Initializes database connection and sequence counter
- `_init_database()` - Creates SQLite schema with indexes
- `_load_sequence_counter()` - Loads current sequence number from database
- `_next_sequence()` - Generates next sequence number (thread-safe)
- `store_event()` - **Key method**: Stores game event with sequence and timestamp
- `get_events_since()` - **Key method**: Retrieves events after specific sequence for client recovery
- `get_room_events()` - Gets all events for a room with optional limit
- `replay_room_state()` - **Key method**: Reconstructs room state from stored events
- `_apply_event_to_state()` - Applies single event to state during reconstruction
- `cleanup_old_events()` - Removes old events to prevent storage bloat
- `get_event_stats()` - Returns comprehensive event storage statistics
- `health_check()` - Performs health check on event store
- `event_store` - Global EventStore instance

**Event Types Supported**:
- `phase_change` - Game phase transitions
- `player_joined` - Player joining rooms
- `player_declared` - Player declarations
- `pieces_played` - Piece plays during turns
- `round_complete` - Round completion
- `game_started` - Game initialization

**Dead Code**:

- None identified - All methods are used for event sourcing

**Dependencies**:

- Imports:
  - `sqlite3` - Database storage
  - `asyncio` - Async support with locking
  - `json` - Event payload serialization
  - `datetime` - Timestamp handling
  - `dataclasses` - GameEvent structure
- Used by:
  - `backend.api.routes.routes.py` - Imports event_store for recovery endpoints
  - `backend.engine.state_machine.action_queue.py` - Imports for event persistence

---

## Summary

The infrastructure layer provides robust support systems for the game:

- **Room Management**: Thread-safe room operations with comprehensive state tracking
- **Bot AI System**: Sophisticated bot management with enterprise architecture compliance
- **Event Sourcing**: Complete event persistence and state reconstruction capabilities
- **Shared Instances**: Clean singleton pattern for global resource management
- **Database Storage**: Efficient SQLite-based event storage with indexing

**Key Strengths**:
- Thread-safe operations preventing race conditions
- Comprehensive bot AI integration with duplicate action prevention
- Complete event sourcing for debugging and client recovery
- Efficient database schema with proper indexing
- Clean separation of concerns between components

**Areas for Improvement**:
- Remove dead code in room.py (legacy start_game method)
- Translate Thai comment to English in room.py
- Consider adding connection pooling for event store in high-traffic scenarios
- Add more robust error handling in event store replay functionality
- Consider adding metrics/monitoring for bot action frequency