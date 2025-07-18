# API Layer Audit

## Overview
This document contains detailed analysis of all API layer components including WebSocket endpoints, HTTP routes, validation, and rate limiting.

---

## 1. `/backend/api/routes/ws.py`

**Status**: ✅ Checked  
**Purpose**: WebSocket endpoint handler for real-time game communication. Manages all WebSocket events for both lobby and game rooms.

**Classes/Functions**:

- `websocket_endpoint()` - Main WebSocket handler that processes all incoming messages

**Key Event Handlers**:

- Lobby events: `create_room`, `join_room`, `get_rooms`, `request_room_list`
- Room management: `add_bot`, `remove_player`, `leave_room`, `get_room_state`
- **Game events**: `start_game` (line 1228), `declare`, `play`, `play_pieces`, `request_redeal`, `accept_redeal`, `decline_redeal`
- System events: `ping`, `client_ready`, `ack`, `sync_request`

**Dead Code**:

- `play_pieces` event handler (lines 827-901) appears to be legacy - duplicates `play` handler
- Empty except blocks at lines 1276-1278 (WebSocketDisconnect handling)

**Dependencies**:

- Imports:
  - `backend.socket_manager` - For WebSocket registration and broadcasting
  - `backend.shared_instances` - For shared room manager
  - `api.validation` - For message validation
  - `api.middleware.websocket_rate_limit` - For rate limiting
  - `.routes` (relative import) - For notify functions and redeal controller
  - `engine.state_machine.core` - For GameAction and ActionType
- Used by: Main FastAPI application mounts this router

---

## 2. `/backend/socket_manager.py`

**Status**: ✅ Checked  
**Purpose**: **Critical WebSocket Infrastructure**: Manages WebSocket connections, reliable message delivery, and broadcasting for all game events. Handles connection registration, message queuing, and acknowledgment system.

**Classes/Functions**:

- `PendingMessage` - Dataclass for messages awaiting acknowledgment
- `MessageStats` - Dataclass for delivery tracking statistics
- `SocketManager` - Main WebSocket management class
- `__init__()` - Initializes connection pools and background tasks
- `__del__()` - Cleanup background tasks
- `_process_broadcast_queue()` - Enhanced queue processor with monitoring
- `register()` - **Key method**: Registers WebSocket for room (called by ws.py)
- `unregister()` - **Key method**: Removes WebSocket from room
- `_unregister_async()` - Async version of unregister
- `broadcast()` - **Key method**: Broadcasts events to all connections in room
- `_next_sequence()` - Generates message sequence numbers
- `send_with_ack()` - Sends messages with acknowledgment tracking
- `handle_ack()` - Processes acknowledgment messages
- `_message_retry_worker()` - Background task for message retry
- `_retry_message()` - Retries failed messages
- `_handle_expired_message()` - Handles expired messages
- `request_client_sync()` - Requests client synchronization
- `get_message_stats()` - Returns message delivery statistics
- `get_room_stats()` - Returns room connection statistics
- `ensure_lobby_broadcast_task()` - Ensures lobby broadcast task exists
- Global `register()` and `broadcast()` functions - Module-level convenience functions

**Dead Code**:

- None identified - All methods appear to be used

**Dependencies**:

- Imports:
  - `fastapi.websockets.WebSocket` - WebSocket connection handling
  - Standard library modules for async, JSON, time, dataclasses
- Used by:
  - `backend.api.routes.ws.py` - Primary consumer, imports register, broadcast, unregister
  - `backend.engine.state_machine.game_state_machine.py` - Uses broadcast_callback
  - `backend.engine.state_machine.base_state.py` - Uses broadcast for enterprise architecture

---

## 3. `/backend/api/validation/__init__.py`

**Status**: ✅ Checked  
**Purpose**: Validation module entry point that exports all validation functions for both REST API and WebSocket message validation across the application.

**Classes/Functions**:
- Module-level imports from `rest_validators` and `websocket_validators`
- `RestApiValidator` - REST API validation class export
- `get_validated_declaration()` - Player declaration validation export
- `get_validated_play_turn()` - Turn play validation export
- `get_validated_player_name()` - Player name validation export
- `get_validated_room_id()` - Room ID validation export
- `WebSocketMessageValidator` - WebSocket validation class export
- `validate_websocket_message()` - WebSocket message validation export

**Key Features**:
- **Clean Module Interface**: Single import point for all validation functions
- **Separation of Concerns**: Separates REST and WebSocket validation
- **Explicit Exports**: `__all__` list ensures controlled API surface
- **Centralized Validation**: All validation logic accessible from single module

**Dead Code**:
- None identified - Clean module interface with essential exports

**Dependencies**:
- **Imports**: `.rest_validators` (REST API validation), `.websocket_validators` (WebSocket validation)
- **Used by**: `/backend/api/routes/ws.py` (WebSocket handlers), `/backend/api/routes/routes.py` (REST endpoints), any module requiring input validation

**Security Notes**:
- Provides centralized validation interface for input sanitization
- Validation functions help prevent injection attacks and malformed data
- Clean separation between REST and WebSocket validation domains

---

## 4. `/backend/api/middleware/websocket_rate_limit.py`

**Status**: ✅ Checked  
**Purpose**: Comprehensive WebSocket rate limiting system with per-connection, per-event-type, and room-based limiting to prevent abuse and flooding attacks.

**Classes/Functions**:
- `WebSocketRateLimiter` - Main WebSocket rate limiting class
- `__init__()` - Initializes rate limiter with connection and room tracking
- `_get_client_id(websocket, room_id)` - Generates unique client identifier using MD5 hash
- `check_websocket_message_rate_limit()` - Primary rate limit check with priority handling
- `check_room_flood(room_id, threshold)` - Detects room-wide message flooding
- `get_connection_stats(client_id)` - Returns connection statistics
- `cleanup_connection(websocket, room_id)` - Async cleanup after disconnect
- `get_websocket_rate_limiter()` - Global singleton instance getter
- `check_websocket_rate_limit()` - Convenience function for rate limit checks
- `send_rate_limit_error(websocket, rate_info)` - Sends rate limit error to client

**Key Features**:
- **Per-Connection Rate Limiting**: Individual client tracking with unique IDs
- **Event-Type Specific Limits**: Different limits for system, lobby, room, and game events
- **Priority System Integration**: Critical events can bypass rate limits
- **Grace Period Support**: Temporary limit increases for new connections
- **Room Flood Detection**: Detects and prevents room-wide message flooding
- **Configurable Fallbacks**: Hardcoded defaults if configuration modules unavailable

**Dead Code**:
- Dynamic import attempts with fallback behavior (lines 19-37) - Not dead code, provides graceful degradation
- None identified - All functionality appears to be actively used

**Dependencies**:
- **Imports**: `fastapi.WebSocket` (WebSocket handling), `.rate_limit` (core rate limiting), `.event_priority` (priority management), optional `error_codes` and `rate_limits` config modules
- **Used by**: `/backend/api/routes/ws.py` (WebSocket event handling), `/backend/api/routes/routes.py` (statistics endpoints)

**Security Notes**:
- Client identification uses MD5 hashing for privacy protection
- Comprehensive rate limits prevent various types of abuse
- Grace period system prevents legitimate new users from being blocked
- Room flood detection prevents coordinated attacks
- Configurable block durations for severe violations

---

## 5. `/backend/api/routes/routes.py`

**Status**: ✅ Checked  
**Purpose**: HTTP API endpoints for debugging, monitoring, health checks, event sourcing, and system statistics, plus lobby notification functions used by WebSocket handlers.

**Classes/Functions**:
- `get_room_stats(room_id)` - Debug endpoint for room statistics
- `notify_lobby_room_created(room_data)` - Broadcasts new room creation to lobby
- `notify_lobby_room_updated(room_data)` - Broadcasts room updates to lobby
- `notify_lobby_room_closed(room_id, reason)` - Broadcasts room closure to lobby
- `get_room_events_since(room_id, since_sequence)` - Client recovery endpoint
- `get_room_reconstructed_state(room_id)` - State reconstruction for client recovery
- `get_all_room_events(room_id, limit)` - Debug endpoint for all room events
- `get_event_store_stats()` - Event store statistics
- `cleanup_old_events(older_than_hours)` - Event cleanup endpoint
- `health_check()` - Basic health check for load balancers
- `detailed_health_check()` - Comprehensive health information
- `health_metrics()` - Prometheus-compatible metrics endpoint
- `recovery_status()` - Recovery system status
- `trigger_recovery(procedure_name, context)` - Manual recovery trigger
- `rate_limit_stats()` - Rate limiting statistics
- `system_stats()` - Comprehensive system statistics
- `get_rate_limit_metrics()` - Detailed rate limit metrics

**Key Features**:
- **Event Sourcing**: Client recovery endpoints for state reconstruction
- **Health Monitoring**: Multiple health check endpoints with different detail levels
- **Metrics Export**: Prometheus-compatible metrics for monitoring
- **Debug Endpoints**: Room statistics and system information
- **Lobby Notifications**: WebSocket broadcasting for lobby updates
- **Recovery System**: Manual recovery triggers and status monitoring

**Dead Code**:
- Comments about removed redeal controller endpoints (lines 36-48)
- Migration notes indicating complete REST-to-WebSocket transition
- Debug print statement (line 34) for socket_manager ID

**Dependencies**:
- **Imports**: `backend.socket_manager` (broadcasting), `backend.shared_instances` (managers), `api.validation.RestApiValidator` (validation), `api.models.game_models` (response models), `api.services.*` (optional services), `engine.state_machine.core` (actions)
- **Used by**: Main FastAPI application (router mounting), `/backend/api/routes/ws.py` (lobby notification functions)

**Security Notes**:
- Debug endpoints expose internal system information
- Health endpoints are typically public for load balancers
- Recovery endpoints could be used for system manipulation
- Rate limit metrics provide visibility into abuse patterns

---

**Classes/Functions**:

**Debug/Monitoring Endpoints**:
- `get_room_stats()` - Returns room statistics for debugging
- `get_rate_limit_metrics()` - Comprehensive rate limit metrics
- `system_stats()` - System statistics including health and performance
- `rate_limit_stats()` - Rate limiting statistics

**Health Check Endpoints**:
- `health_check()` - Basic health check for load balancers
- `detailed_health_check()` - Comprehensive health information with system metrics
- `health_metrics()` - Prometheus-compatible metrics endpoint

**Event Sourcing & Recovery Endpoints**:
- `get_room_events_since()` - Client recovery: Get events after sequence number
- `get_room_reconstructed_state()` - Client recovery: Get current room state
- `get_all_room_events()` - Get all events for room (debugging)
- `get_event_store_stats()` - Event store statistics
- `cleanup_old_events()` - Clean up old events

**Recovery System Endpoints**:
- `recovery_status()` - Get recovery system status
- `trigger_recovery()` - Manually trigger recovery procedure

**Lobby Notification Functions** (used by WebSocket handlers):
- `notify_lobby_room_created()` - Notify lobby about new room creation
- `notify_lobby_room_updated()` - Notify lobby about room updates
- `notify_lobby_room_closed()` - Notify lobby about room closure

**Dead Code**:

- Comments about removed redeal controller endpoints (lines 36-48) - **Legacy documentation**
- Multiple migration notes indicating REST-to-WebSocket migration is complete

**Dependencies**:

- Imports:
  - `backend.socket_manager` - For broadcasting lobby notifications
  - `backend.shared_instances` - For shared room/bot managers
  - `api.validation.RestApiValidator` - For input validation
  - `api.models.game_models` - For response models
  - `api.services.event_store` - For event persistence (optional)
  - `api.services.health_monitor` - For health checking
  - `api.services.recovery_manager` - For recovery operations
  - `engine.state_machine.core` - For GameAction and ActionType
- Used by:
  - Main FastAPI application mounts this router
  - `backend.api.routes.ws.py` - Imports lobby notification functions

---

## Summary

The API layer is well-structured with clear separation of concerns:

- **WebSocket System**: Robust real-time communication with enterprise broadcasting
- **Rate Limiting**: Comprehensive protection against abuse and flooding
- **HTTP Endpoints**: Focused on monitoring, debugging, and system health
- **Validation**: Centralized input validation for both REST and WebSocket
- **Event Sourcing**: Complete event persistence and recovery capabilities

**Key Strengths**:
- Enterprise-grade WebSocket management with acknowledgments and retry logic
- Comprehensive rate limiting with per-connection and per-event tracking
- Full event sourcing for client recovery and debugging
- Extensive health monitoring and metrics endpoints

**Areas for Improvement**:
- Remove legacy code comments about removed redeal controller
- Clean up unused imports in rate limiting module
- Consider consolidating some debug endpoints