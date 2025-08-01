# State Management Integration Guide

## Overview

This guide documents how the Clean Architecture has been integrated with the sophisticated state management infrastructure in the backend.

## Architecture

The integration follows an adapter pattern to bridge the Clean Architecture use cases with the existing state persistence infrastructure:

```
WebSocket → CleanArchitectureAdapter → UseCase → StateManagementAdapter → StatePersistenceManager
                                                           ↓
                                                   Circuit Breaker + Metrics
```

## Key Components

### 1. StateManagementAdapter

Located at: `application/adapters/state_management_adapter.py`

This adapter provides a clean interface between use cases and the state persistence infrastructure:

- Handles feature flag checks
- Maps between domain and state machine concepts  
- Provides fallback behavior when disabled
- Includes circuit breaker for resilience
- Tracks metrics for monitoring

### 2. StateAdapterFactory

Located at: `infrastructure/state_persistence/state_adapter_factory.py`

Factory pattern for creating state adapters with proper configuration:

- Centralizes adapter creation
- Manages StatePersistenceManager lifecycle
- Configures monitoring and resilience

### 3. Unified GamePhase Enum

Located at: `domain/value_objects/game_phase.py`

Unified enum that bridges the domain (6 phases) and state machine (11 phases) representations:

- Single source of truth for game phases
- Conversion methods between representations
- Migration helpers for existing code

## Feature Flag Control

State management is controlled by the `USE_STATE_PERSISTENCE` feature flag:

```python
# Enable state persistence (default is False)
export USE_STATE_PERSISTENCE=true

# Or in code
flags = FeatureFlags()
enabled = flags.is_enabled("USE_STATE_PERSISTENCE", context)
```

## Integration Points

### Use Cases

All major game use cases have been integrated:

1. **StartGameUseCase**
   - Tracks game start transitions
   - Records initial game state
   - Handles phase changes

2. **DeclareUseCase**
   - Tracks player declarations
   - Records phase transitions when all declare

3. **PlayUseCase**
   - Tracks player actions
   - Records turn transitions

### Dependency Injection

The CleanArchitectureAdapter automatically injects state adapters:

```python
# In CleanArchitectureAdapter._handle_start_game()
state_adapter = StateAdapterFactory.create_for_use_case("StartGameUseCase", context)
use_case = StartGameUseCase(uow, publisher, state_adapter)
```

## Monitoring

### Metrics Collected

- State transition success/failure rates
- Operation latency (p50, p95, p99)
- Circuit breaker status
- Error counts by type

### Circuit Breaker

Protects against state persistence failures:

- 5 failures trigger open circuit
- 30 second recovery timeout
- 3 successes required to close

## Testing

### Unit Tests
- `test_state_management_adapter.py` - Adapter behavior
- `test_unified_game_phase.py` - Phase mapping

### Integration Tests
- `test_state_management_integration.py` - End-to-end flows
- `test_state_monitoring_setup.py` - Monitoring verification

## Deployment Checklist

Before enabling in production:

1. ✅ Verify all use cases have state adapters
2. ✅ Confirm monitoring dashboards are set up
3. ✅ Test circuit breaker behavior
4. ❌ Enable feature flag gradually (currently disabled)
5. ❌ Monitor metrics during rollout
6. ❌ Verify state recovery works

## Configuration

### State Persistence Config

```python
PersistenceConfig(
    strategy=PersistenceStrategy.HYBRID,
    snapshot_enabled=True,
    event_sourcing_enabled=True,
    recovery_enabled=True,
    persist_on_phase_change=True,
    snapshot_interval=timedelta(minutes=5)
)
```

### Monitoring Config

```python
CircuitBreakerConfig(
    failure_threshold=5,
    recovery_timeout=timedelta(seconds=30),
    success_threshold=3
)
```

## Troubleshooting

### State Not Persisting

1. Check feature flag is enabled
2. Verify StatePersistenceManager is initialized
3. Check circuit breaker status
4. Review error logs

### Performance Issues

1. Check metrics for latency spikes
2. Verify caching is enabled
3. Review batch operation settings
4. Check snapshot frequency

## Next Steps

1. Enable feature flag in staging environment
2. Run load tests with state persistence
3. Set up production monitoring dashboards
4. Plan gradual production rollout