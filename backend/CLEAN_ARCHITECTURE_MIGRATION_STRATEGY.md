# Clean Architecture Migration Strategy

## Overview

This document outlines the strategy for migrating the Liap Tui codebase from its current structure to the new clean architecture. The migration is designed to be gradual and non-breaking, allowing the system to continue operating during the transition.

## Migration Principles

1. **No Breaking Changes** - Frontend continues to work unchanged
2. **Gradual Migration** - Move one component at a time
3. **Parallel Operation** - Old and new code can coexist
4. **Feature Flags** - Toggle between implementations
5. **Backward Compatibility** - Maintain existing APIs

## Current State vs Target State

### Current Structure
```
backend/
├── api/
│   ├── routes/          # Mixed concerns
│   └── websocket.py     # Direct game logic
├── engine/              # All game logic together
├── socket_manager.py    # Infrastructure in root
└── config.py
```

### Target Structure
```
backend/
├── domain/              # Pure business logic
├── application/         # Use cases & services
├── infrastructure/      # External concerns
├── api/                 # Clean API layer
└── legacy/              # Old code during migration
```

## Migration Phases

### Phase 1: Parallel Structure Setup ✅
**Status: COMPLETE**

Create new structure alongside existing code:
- Domain layer with entities, value objects, services
- Application layer with use cases and commands
- Infrastructure adapters
- Keep old code untouched

### Phase 2: Dual Operation ✅
**Status: COMPLETE**

Run both systems in parallel:
- New clean architecture handles requests
- Old code remains as fallback
- Use dependency injection to switch

### Phase 3: Feature Flag Integration
**Status: IN PROGRESS**

Add feature flags to toggle between implementations:

```python
# config/feature_flags.py
FEATURE_FLAGS = {
    "use_clean_architecture": True,
    "use_event_system": True,
    "use_new_state_machine": False,  # Gradual rollout
}

# api/websocket/endpoints.py
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    if FEATURE_FLAGS["use_clean_architecture"]:
        # Use new clean handlers
        handler = UnifiedWebSocketHandler(container)
    else:
        # Use legacy handler
        handler = LegacyWebSocketHandler()
    
    await handler.handle(websocket, room_id)
```

### Phase 4: Component Migration

#### 4.1 Room Management ✅
- [x] CreateRoomUseCase replaces direct room creation
- [x] JoinRoomUseCase replaces direct joining logic
- [x] RoomRepository handles persistence

#### 4.2 Game Logic ✅
- [x] StartGameUseCase replaces game initialization
- [x] PlayTurnUseCase replaces turn handling
- [x] Game entity encapsulates rules

#### 4.3 Bot System ✅
- [x] BotStrategy interface for AI
- [x] BotService orchestrates bot actions
- [x] Event-driven bot triggers

#### 4.4 State Machine
- [ ] Adapter pattern wraps existing state machine
- [ ] Gradual migration of state logic
- [ ] Event-driven state transitions

### Phase 5: API Migration

#### Current WebSocket Handling
```python
# Old: Direct handling in websocket.py
async def handle_message(data):
    if data["type"] == "create_room":
        room = create_room(data["player_name"])
        await broadcast(room.id, "room_created", room.to_dict())
```

#### New WebSocket Handling
```python
# New: Command-based handling
async def handle_message(data):
    if data["type"] == "create_room":
        command = CreateRoomCommand(
            host_name=data["player_name"],
            room_settings=data.get("settings", {})
        )
        result = await command_bus.execute(command)
        # Events automatically trigger broadcasts
```

## Compatibility Layer

### WebSocket Message Compatibility

Ensure frontend receives same message format:

```python
# infrastructure/compatibility/message_adapter.py
class MessageAdapter:
    """Adapts new event format to legacy message format."""
    
    @staticmethod
    def adapt_game_started(event: GameStartedEvent) -> dict:
        """Convert to legacy format."""
        return {
            "type": "game_started",
            "room_id": event.aggregate_id,
            "players": event.data["players"],
            "phase": event.data["initial_phase"],
            # Legacy fields
            "game_id": event.aggregate_id,  # Old code expected this
        }
```

### Database Compatibility

For future database migration:

```python
# infrastructure/persistence/migration_adapter.py
class MigrationAdapter:
    """Handles data migration between old and new formats."""
    
    async def migrate_room(self, old_room_data: dict) -> Room:
        """Convert old room format to new domain model."""
        room = Room(id=old_room_data["id"])
        room.host = old_room_data["host_name"]
        # Map old fields to new structure
        return room
```

## Testing Strategy

### 1. Parallel Testing
Run tests against both implementations:

```python
@pytest.mark.parametrize("use_clean_arch", [True, False])
async def test_room_creation(use_clean_arch):
    """Test room creation with both implementations."""
    config.FEATURE_FLAGS["use_clean_architecture"] = use_clean_arch
    
    # Test should pass with either implementation
    result = await create_room("TestPlayer")
    assert result.success
```

### 2. Contract Testing
Ensure API contracts remain consistent:

```python
# tests/contract/test_websocket_api.py
async def test_websocket_message_format():
    """Verify message format hasn't changed."""
    # Connect and create room
    async with websocket_connect("/ws/lobby") as ws:
        await ws.send_json({
            "type": "create_room",
            "data": {"player_name": "TestPlayer"}
        })
        
        response = await ws.receive_json()
        
        # Verify legacy format
        assert "type" in response
        assert response["type"] == "room_created"
        assert "room_id" in response["data"]
        assert "join_code" in response["data"]
```

### 3. Integration Testing
Test new components with existing system:

```python
# tests/integration/test_legacy_compatibility.py
async def test_new_room_with_legacy_game():
    """Test new room system works with legacy game engine."""
    # Create room with new system
    room = await new_room_service.create_room("Host")
    
    # Start game with legacy system
    legacy_game = LegacyGameEngine(room.to_legacy_format())
    legacy_game.start()
    
    assert legacy_game.is_started
```

## Rollback Plan

If issues arise during migration:

1. **Immediate Rollback**
   ```python
   # Set all feature flags to False
   FEATURE_FLAGS = {
       "use_clean_architecture": False,
       "use_event_system": False,
   }
   ```

2. **Partial Rollback**
   ```python
   # Rollback specific components
   FEATURE_FLAGS["use_clean_game_logic"] = False
   # Keep other components on new system
   ```

3. **Data Recovery**
   - Event store maintains full history
   - Can replay events to restore state
   - Legacy data remains untouched

## Monitoring During Migration

### Key Metrics

1. **Performance Metrics**
   - Response time comparison
   - Memory usage
   - CPU utilization

2. **Error Rates**
   - Track errors by implementation
   - Compare error rates

3. **User Experience**
   - WebSocket connection stability
   - Message delivery reliability

### Monitoring Implementation

```python
# infrastructure/monitoring/migration_metrics.py
class MigrationMetrics:
    """Track metrics during migration."""
    
    async def track_request(self, implementation: str, duration: float):
        """Track request performance by implementation."""
        metrics.histogram(
            "request_duration",
            duration,
            tags={"implementation": implementation}
        )
    
    async def track_error(self, implementation: str, error: Exception):
        """Track errors by implementation."""
        metrics.increment(
            "request_errors",
            tags={
                "implementation": implementation,
                "error_type": type(error).__name__
            }
        )
```

## Timeline

### Week 1-2: Setup ✅
- Create clean architecture structure
- Implement core domain and application layers
- Set up infrastructure adapters

### Week 3-4: Parallel Operation ✅
- Wire up dependency injection
- Implement event system
- Create compatibility layer

### Week 5-6: Gradual Migration
- Enable feature flags
- Monitor metrics
- Fix compatibility issues

### Week 7-8: Completion
- Remove legacy code
- Update documentation
- Performance optimization

## Success Criteria

1. **Zero Downtime** - No service interruptions
2. **No Breaking Changes** - Frontend works unchanged
3. **Performance Maintained** - No degradation
4. **All Tests Pass** - Both old and new tests
5. **Clean Codebase** - Proper separation of concerns

## Next Steps

1. Implement feature flag system
2. Create monitoring dashboard
3. Set up A/B testing for gradual rollout
4. Document new API for future frontend updates
5. Plan database migration strategy