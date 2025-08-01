# Use Case Integration Design

## Overview

This document outlines the minimal changes required to integrate state management into existing use cases while preserving current behavior.

## Design Principles

1. **Minimal Intrusion**: Change as little code as possible in existing use cases
2. **Feature Flag Control**: All state management must be feature-flag controlled
3. **Backward Compatibility**: When disabled, behavior must be exactly as before
4. **Error Resilience**: State management failures should not break game flow

## StartGameUseCase Integration

### Current Flow (Line 149)
```python
game.start_game()
game.start_round()  # Direct call bypasses state management
```

### Proposed Integration
```python
class StartGameUseCase(UseCase[StartGameRequest, StartGameResponse]):
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        event_publisher: EventPublisher,
        state_adapter: Optional[StateManagementAdapter] = None,  # NEW
        metrics: Optional[MetricsCollector] = None,
    ):
        self._uow = unit_of_work
        self._event_publisher = event_publisher
        self._state_adapter = state_adapter  # NEW - Optional adapter
        self._metrics = metrics

    async def execute(self, request: StartGameRequest) -> StartGameResponse:
        # ... existing validation code ...
        
        # Create the game
        game = Game(room_id=room.room_id, players=game_players)
        
        # Track game start if adapter available
        if self._state_adapter:
            await self._state_adapter.track_game_start(
                game_id=game.room_id,
                room_id=room.room_id,
                players=[p.name for p in game_players],
                starting_player=starting_player.name
            )
        
        # Start the game (existing code)
        game.start_game()
        
        # Start the first round with state tracking
        old_phase = game.current_phase
        game.start_round()
        
        # Track phase change if adapter available
        if self._state_adapter and old_phase != game.current_phase:
            context = self._state_adapter.create_context(
                game_id=game.room_id,
                room_id=room.room_id,
                current_phase=str(old_phase)
            )
            await self._state_adapter.track_phase_change(
                context=context,
                from_phase=old_phase,
                to_phase=game.current_phase,
                trigger="start_round",
                payload={"round": game.round_number}
            )
        
        # ... rest of existing code ...
```

### Key Points
- State adapter is **optional** - None when feature flag disabled
- All state tracking is **conditional** - only runs if adapter present
- Original domain calls remain **unchanged**
- State tracking **failures don't break** game flow

## Other Use Cases Pattern

### DeclareUseCase
```python
class DeclareUseCase(UseCase[DeclareRequest, DeclareResponse]):
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        event_publisher: EventPublisher,
        state_adapter: Optional[StateManagementAdapter] = None,  # NEW
    ):
        # ... existing init ...
        self._state_adapter = state_adapter

    async def execute(self, request: DeclareRequest) -> DeclareResponse:
        # ... existing validation ...
        
        # Track player action if adapter available
        if self._state_adapter:
            context = self._state_adapter.create_context(
                game_id=game.room_id,
                room_id=room.room_id,
                player_id=request.player_id,
                current_phase=str(game.current_phase)
            )
            await self._state_adapter.track_player_action(
                context=context,
                action="declare",
                payload={
                    "declaration": request.declaration,
                    "pieces": request.pieces
                }
            )
        
        # ... existing game logic ...
        old_phase = game.current_phase
        game.process_declaration(...)
        
        # Track phase change if occurred
        if self._state_adapter and old_phase != game.current_phase:
            await self._state_adapter.track_phase_change(
                context=context,
                from_phase=old_phase,
                to_phase=game.current_phase,
                trigger="declaration_processed"
            )
```

### PlayPiecesUseCase
Similar pattern - track action before, phase change after

### RedealUseCase
Track as special action with phase implications

## Dependency Injection Changes

### Option 1: Conditional Adapter Creation
```python
# In infrastructure/dependencies.py
def _create_state_adapter(self) -> Optional[StateManagementAdapter]:
    """Create state adapter if enabled."""
    if not self._feature_flags.is_enabled("USE_STATE_PERSISTENCE"):
        return None
        
    state_manager = self.get(StatePersistenceManager)
    if not state_manager:
        return None
        
    return StateManagementAdapter(state_manager=state_manager)

# Register factory
self.register_factory(StateManagementAdapter, self._create_state_adapter)
```

### Option 2: Adapter Factory Pattern
```python
class StateAdapterFactory:
    @staticmethod
    def create(container: DependencyContainer) -> Optional[StateManagementAdapter]:
        feature_flags = get_feature_flags()
        if not feature_flags.is_enabled("USE_STATE_PERSISTENCE"):
            return None
            
        try:
            state_manager = container.get(StatePersistenceManager)
            return StateManagementAdapter(state_manager=state_manager)
        except:
            return None  # Graceful fallback
```

## Error Handling Strategy

### Principle: State Tracking Should Never Break Game Flow

```python
# In StateManagementAdapter
async def track_phase_change(self, ...) -> bool:
    """Track phase change - returns False on error but doesn't raise."""
    if not self.enabled or not self._state_manager:
        return True  # Pretend success when disabled
        
    try:
        # ... actual tracking ...
        return True
    except Exception as e:
        logger.error(f"State tracking failed: {e}")
        # Could emit metric here
        return False  # But don't raise!
```

### Use Case Error Handling
```python
# In use cases - optional logging of tracking failures
if self._state_adapter:
    success = await self._state_adapter.track_phase_change(...)
    if not success:
        logger.warning("State tracking failed but continuing game")
        # Optionally emit metric
```

## Testing Strategy

### 1. Existing Tests Continue to Pass
- No adapter provided = exact same behavior
- All characterization tests pass unchanged

### 2. New Integration Tests
```python
def test_start_game_with_state_tracking():
    # Given adapter is provided
    state_adapter = Mock(StateManagementAdapter)
    use_case = StartGameUseCase(uow, publisher, state_adapter)
    
    # When game starts
    response = await use_case.execute(request)
    
    # Then state is tracked
    state_adapter.track_game_start.assert_called_once()
    state_adapter.track_phase_change.assert_called()
    
    # And game behavior unchanged
    assert response == expected_response
```

### 3. Feature Flag Tests
```python
@pytest.mark.parametrize("flag_enabled", [True, False])
def test_state_tracking_controlled_by_feature_flag(flag_enabled):
    with mock_feature_flag("USE_STATE_PERSISTENCE", flag_enabled):
        # Adapter creation should respect flag
        adapter = container.get(StateManagementAdapter)
        if flag_enabled:
            assert adapter is not None
            assert adapter.enabled
        else:
            assert adapter is None
```

## Migration Order

### Phase 1: StartGameUseCase
- Most critical path
- Tests phase tracking
- Validates adapter pattern

### Phase 2: Player Action Use Cases
- DeclareUseCase
- PlayPiecesUseCase
- Less critical, good for testing action tracking

### Phase 3: Game Flow Use Cases
- EndTurnUseCase
- RedealUseCase
- CompleteGameUseCase

### Phase 4: Recovery Use Cases
- ReconnectUseCase (with state recovery)
- GetGameStateUseCase (with state validation)

## Rollback Plan

1. **Feature Flag Off**: Instant rollback, no adapter created
2. **Adapter Removal**: If needed, remove adapter parameter (backward compatible)
3. **Code Revert**: Git revert of integration commits if necessary

## Performance Considerations

- State tracking is async - doesn't block game flow
- Adapter caches feature flag check
- State manager has built-in batching
- Expected latency impact: < 5ms per tracked operation

## Summary

This design achieves state management integration with:
- **Minimal code changes** to existing use cases
- **Complete backward compatibility** via feature flags
- **Error resilience** - tracking failures don't break games
- **Gradual rollout** - one use case at a time
- **Easy rollback** - feature flag or code revert