# Feature Flag Strategy for State Management Integration

## Overview

This document outlines the feature flag strategy for safely rolling out state management integration across the application.

## Flag Hierarchy

### Master Flag
```python
USE_STATE_PERSISTENCE = "use_state_persistence"
```
- Controls overall state management system activation
- When False: No state adapter created, zero impact
- When True: Enables state management infrastructure

### Sub-Feature Flags
```python
ENABLE_STATE_SNAPSHOTS = "enable_state_snapshots"
ENABLE_STATE_RECOVERY = "enable_state_recovery"
PERSIST_PLAYER_ACTIONS = "persist_player_actions"
ENABLE_STATE_VALIDATION = "enable_state_validation"
```

## Configuration Patterns

### 1. Environment-Based Configuration
```bash
# Development - Full features
export FF_USE_STATE_PERSISTENCE=true
export FF_ENABLE_STATE_SNAPSHOTS=true
export FF_ENABLE_STATE_RECOVERY=true

# Staging - Gradual rollout
export FF_USE_STATE_PERSISTENCE=50  # 50% of games
export FF_ENABLE_STATE_SNAPSHOTS=false
export FF_ENABLE_STATE_RECOVERY=false

# Production - Safe initial rollout
export FF_USE_STATE_PERSISTENCE=5   # 5% canary
export FF_ENABLE_STATE_SNAPSHOTS=false
export FF_ENABLE_STATE_RECOVERY=false
```

### 2. Per-Room Configuration
```python
def is_state_persistence_enabled(room_id: str) -> bool:
    """Check if state persistence enabled for specific room."""
    flags = get_feature_flags()
    
    # Check room-specific override first
    if room_id in BETA_TEST_ROOMS:
        return True
        
    # Check percentage rollout
    return flags.is_enabled(
        "USE_STATE_PERSISTENCE",
        context={"room_id": room_id}
    )
```

### 3. Per-Use-Case Configuration
```python
# In infrastructure/state_management_config.py
STATE_MANAGEMENT_USE_CASES = {
    "StartGameUseCase": {
        "enabled": True,
        "track_actions": False,
        "create_snapshots": True,
    },
    "DeclareUseCase": {
        "enabled": True,
        "track_actions": True,
        "create_snapshots": False,
    },
    "PlayPiecesUseCase": {
        "enabled": False,  # Not ready yet
        "track_actions": False,
        "create_snapshots": False,
    },
}

# In StateManagementAdapter
def is_enabled_for_use_case(self, use_case_name: str) -> bool:
    """Check if state management enabled for specific use case."""
    if not self.enabled:
        return False
        
    config = STATE_MANAGEMENT_USE_CASES.get(use_case_name, {})
    return config.get("enabled", False)
```

## Rollout Phases

### Phase 1: Shadow Mode (Week 1-2)
```python
# State management runs but doesn't affect game
USE_STATE_PERSISTENCE = True
STATE_PERSISTENCE_MODE = "shadow"  # Log only, no recovery

# In adapter
if self.mode == "shadow":
    logger.info(f"[SHADOW] Would track: {transition}")
    return True  # Don't actually persist
```

### Phase 2: Canary Deployment (Week 3-4)
```python
# 5% of new games get state management
USE_STATE_PERSISTENCE = 5  # Percentage
ENABLE_STATE_SNAPSHOTS = False
ENABLE_STATE_RECOVERY = False

# Monitor metrics
- Latency impact
- Error rates
- Memory usage
```

### Phase 3: Gradual Rollout (Week 5-8)
```python
# Increase percentage gradually
Week 5: USE_STATE_PERSISTENCE = 10
Week 6: USE_STATE_PERSISTENCE = 25
Week 7: USE_STATE_PERSISTENCE = 50
Week 8: USE_STATE_PERSISTENCE = 75

# Enable features gradually
Week 6: ENABLE_STATE_SNAPSHOTS = True
Week 7: ENABLE_STATE_RECOVERY = True
```

### Phase 4: Full Rollout (Week 9+)
```python
USE_STATE_PERSISTENCE = True  # 100%
ENABLE_STATE_SNAPSHOTS = True
ENABLE_STATE_RECOVERY = True
PERSIST_PLAYER_ACTIONS = True
```

## Testing with Feature Flags

### Unit Test Helpers
```python
@contextmanager
def state_management_enabled():
    """Context manager for testing with state management."""
    flags = get_feature_flags()
    flags.override("USE_STATE_PERSISTENCE", True)
    try:
        yield
    finally:
        flags.clear_override("USE_STATE_PERSISTENCE")

# Usage
def test_game_with_state_management():
    with state_management_enabled():
        response = await use_case.execute(request)
        # Assert state was tracked
```

### Integration Test Scenarios
```python
@pytest.mark.parametrize("flags", [
    {},  # All disabled
    {"USE_STATE_PERSISTENCE": True},  # Basic enabled
    {"USE_STATE_PERSISTENCE": True, "ENABLE_STATE_SNAPSHOTS": True},  # With snapshots
    {"USE_STATE_PERSISTENCE": True, "ENABLE_STATE_RECOVERY": True},  # With recovery
])
def test_game_flow_with_various_flags(flags):
    with mock_feature_flags(flags):
        # Test game flow works correctly
```

## Monitoring & Alerts

### Key Metrics to Track
```python
# In StateManagementAdapter
async def track_transition(self, ...):
    start_time = time.time()
    try:
        result = await self._state_manager.handle_transition(...)
        
        # Track success metric
        self._metrics.increment(
            "state_management.transition.success",
            tags={
                "use_case": self.current_use_case,
                "phase": transition.to_state
            }
        )
        
        # Track latency
        self._metrics.histogram(
            "state_management.transition.latency",
            time.time() - start_time,
            tags={"use_case": self.current_use_case}
        )
        
        return result
        
    except Exception as e:
        # Track failure metric
        self._metrics.increment(
            "state_management.transition.error",
            tags={
                "use_case": self.current_use_case,
                "error_type": type(e).__name__
            }
        )
        raise
```

### Alert Conditions
1. **Error Rate**: > 1% state tracking failures
2. **Latency**: > 50ms for state operations
3. **Recovery Failures**: Any recovery operation failures
4. **Memory**: State storage > 100MB per game

## Emergency Rollback

### Quick Disable Options

1. **Environment Variable**
```bash
# Emergency disable
export FF_USE_STATE_PERSISTENCE=false
# Restart services
```

2. **Runtime API**
```python
# Admin endpoint
@app.post("/admin/feature-flags/disable-state-management")
async def disable_state_management():
    flags = get_feature_flags()
    flags.override("USE_STATE_PERSISTENCE", False)
    return {"status": "disabled"}
```

3. **Circuit Breaker**
```python
class StateManagementCircuitBreaker:
    def __init__(self, error_threshold=10, timeout=60):
        self.error_count = 0
        self.error_threshold = error_threshold
        self.last_reset = time.time()
        self.timeout = timeout
        self.is_open = False
    
    def record_error(self):
        self.error_count += 1
        if self.error_count >= self.error_threshold:
            self.is_open = True
            logger.error("State management circuit breaker OPEN")
    
    def can_execute(self) -> bool:
        if time.time() - self.last_reset > self.timeout:
            self.reset()
        return not self.is_open
```

## A/B Testing Configuration

### Split by Room ID
```python
def get_state_management_variant(room_id: str) -> str:
    """Determine A/B test variant for room."""
    hash_value = hash(f"state_mgmt:{room_id}") % 100
    
    if hash_value < 50:
        return "control"  # No state management
    elif hash_value < 90:
        return "basic"    # State tracking only
    else:
        return "full"     # All features including recovery
```

### Metrics Comparison
```python
# Track metrics by variant
self._metrics.increment(
    "game.completed",
    tags={
        "variant": get_state_management_variant(room_id),
        "with_errors": str(had_errors).lower()
    }
)
```

## Configuration Management

### Development Settings
```json
{
  "USE_STATE_PERSISTENCE": true,
  "ENABLE_STATE_SNAPSHOTS": true,
  "ENABLE_STATE_RECOVERY": true,
  "STATE_PERSISTENCE_MODE": "full",
  "STATE_LOG_LEVEL": "DEBUG"
}
```

### Production Settings
```json
{
  "USE_STATE_PERSISTENCE": 5,
  "ENABLE_STATE_SNAPSHOTS": false,
  "ENABLE_STATE_RECOVERY": false,
  "STATE_PERSISTENCE_MODE": "production",
  "STATE_LOG_LEVEL": "WARNING"
}
```

## Summary

This feature flag strategy provides:
- **Safe rollout** with multiple control points
- **Gradual adoption** from shadow mode to full deployment
- **Quick rollback** via multiple mechanisms
- **Fine-grained control** per use case and room
- **Comprehensive monitoring** for confidence in rollout