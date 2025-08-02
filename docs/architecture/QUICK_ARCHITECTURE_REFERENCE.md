# Quick Architecture Reference

**Purpose:** Prevent architectural confusion between Clean Architecture and Engine Layer systems.

## 🚨 CRITICAL DISTINCTIONS

### State Management vs State Machine

| Concept | System | Purpose | Files | Flag |
|---------|--------|---------|-------|------|
| **State Persistence** | Clean Architecture | Data storage & recovery | `StateManagementAdapter` | `USE_STATE_PERSISTENCE` |
| **State Machine** | Engine Layer | Game flow control | `GameStateMachine` | Engine internal |

**❌ NEVER:** Integrate GameStateMachine directly into Clean Architecture use cases  
**✅ ALWAYS:** Use StateManagementAdapter for Clean Architecture state needs

---

## System Boundaries

### Clean Architecture (Primary System)
```
Location: backend/
Purpose: Business logic, data persistence, WebSocket APIs
Layers: Domain → Application → Infrastructure → API
```

**Key Components:**
- `StateManagementAdapter` - State persistence coordination
- `CompositeEventPublisher` - Event distribution  
- `EventStore` - Event persistence
- Use cases in `application/use_cases/`

**Feature Flags:**
- `USE_STATE_PERSISTENCE: True` - Enable state management
- `USE_EVENT_SOURCING: True` - Enable event persistence
- `USE_CLEAN_ARCHITECTURE: True` - Enable Clean Architecture

### Engine Layer (Game Logic System)
```
Location: backend/engine/
Purpose: Game mechanics, phase transitions, bot behavior
Structure: Internal game engine components
```

**Key Components:**
- `GameStateMachine` - Game phase transitions
- `BotManager` - Bot behavior coordination
- Game rules and mechanics

**Integration:** Communicates with Clean Architecture through adapters only

---

## Terminology Glossary

### Clean Architecture Terms

| Term | Definition | Location | Don't Confuse With |
|------|------------|----------|-------------------|
| **State Persistence** | Saving/loading application state | `StateManagementAdapter` | State Machine |
| **Event Sourcing** | Storing events for replay | `EventStore` | State Machine events |
| **Use Case** | Business logic operation | `application/use_cases/` | Engine actions |
| **Domain Event** | Business event notification | `domain/events/` | State Machine transitions |
| **Repository** | Data access abstraction | `infrastructure/` | Engine storage |

### Engine Layer Terms

| Term | Definition | Location | Don't Confuse With |
|------|------------|----------|-------------------|
| **State Machine** | Game flow controller | `engine/state_machine/` | State Persistence |
| **Game State** | Current game phase | `GameStateMachine` | Persisted State |
| **Phase Transition** | Moving between game phases | Engine internal | Domain events |
| **Bot Logic** | AI player behavior | `engine/bot_manager.py` | Use cases |
| **Game Rules** | Mechanical constraints | Engine components | Business rules |

### Integration Terms

| Term | Definition | Purpose | Implementation |
|------|------------|---------|----------------|
| **Adapter Pattern** | Bridge between systems | Loose coupling | `StateManagementAdapter` |
| **Feature Flag** | Enable/disable features | Gradual rollout | `feature_flags.py` |
| **Circuit Breaker** | Prevent cascade failures | Resilience | Infrastructure layer |
| **Event Bridge** | Cross-system communication | Integration | Event publishers |

---

## Quick Decision Guide

### "Should I use State Machine or State Persistence?"

**For Game Flow (phases, turns, rules):**
- ✅ Use Engine Layer `GameStateMachine`
- ❌ Don't use Clean Architecture state

**For Data Storage (save/load, recovery):**
- ✅ Use Clean Architecture `StateManagementAdapter`
- ❌ Don't use Engine Layer directly

**For Business Logic (user actions, validation):**
- ✅ Use Clean Architecture use cases
- ❌ Don't put business rules in Engine

**For Game Mechanics (bot behavior, rules):**
- ✅ Use Engine Layer components
- ❌ Don't put game mechanics in Clean Architecture

### "Which component should I modify?"

| Need to... | Modify | Don't Touch |
|------------|--------|-------------|
| Add new user action | Clean Architecture use case | Engine state machine |
| Change game rules | Engine Layer | Clean Architecture domain |
| Add data persistence | Infrastructure layer | Engine components |
| Modify bot behavior | Engine bot manager | Application layer |
| Add WebSocket endpoint | API layer | Engine directly |
| Change phase logic | Engine state machine | Use cases |

---

## File Location Quick Reference

### Clean Architecture Files
```
backend/
├── domain/                    # Business entities & rules
│   ├── entities/game.py      # Game business entity
│   ├── events/game_events.py # Domain events
│   └── value_objects/        # Immutable values
├── application/
│   ├── use_cases/            # Business operations
│   │   └── game/start_game.py # Game start use case
│   └── adapters/             # System bridges
│       └── state_management_adapter.py # State persistence bridge
├── infrastructure/
│   ├── state_persistence/    # State storage
│   ├── event_store/         # Event storage
│   └── feature_flags.py     # Feature controls
└── api/                     # WebSocket endpoints
```

### Engine Layer Files
```
backend/engine/
├── state_machine/
│   └── game_state_machine.py # Game flow controller
├── bot_manager.py            # AI behavior
├── game.py                   # Core engine
└── rules/                    # Game mechanics
```

---

## Common Mistakes to Avoid

### ❌ Wrong Patterns

1. **Importing GameStateMachine into use cases**
   ```python
   # DON'T DO THIS
   from backend.engine.state_machine.game_state_machine import GameStateMachine
   ```

2. **Using Engine components for data persistence**
   ```python
   # DON'T DO THIS
   game_state_machine.save_to_database()
   ```

3. **Putting business logic in Engine Layer**
   ```python
   # DON'T DO THIS - business rules belong in Clean Architecture
   class GameStateMachine:
       def validate_user_action(self, user_id, action):
   ```

4. **Direct database access from Engine**
   ```python
   # DON'T DO THIS
   class BotManager:
       def save_bot_state(self):
           self.database.save(...)
   ```

### ✅ Correct Patterns

1. **Clean Architecture for user actions**
   ```python
   # USE CASES handle business logic
   class StartGameUseCase:
       def __init__(self, state_adapter: StateManagementAdapter):
   ```

2. **Engine Layer for game mechanics**
   ```python
   # ENGINE handles game flow
   class GameStateMachine:
       def transition_to_next_phase(self):
   ```

3. **Adapters for integration**
   ```python
   # ADAPTERS bridge the systems
   class StateManagementAdapter:
       async def track_phase_change(self, from_phase, to_phase):
   ```

---

## Validation Checklist

Before making changes, ask:

- [ ] Am I modifying the right system for this change?
- [ ] Am I using State Persistence (Clean) or State Machine (Engine)?
- [ ] Does this follow the single responsibility principle?
- [ ] Am I creating circular dependencies?
- [ ] Are feature flags properly used?
- [ ] Is this change documented in the right ADR?

---

## Emergency Recovery

If you realize you're mixing architectures:

1. **Stop immediately** - Don't continue the wrong path
2. **Check this reference** - Verify which system to use
3. **Consult ADR-001** - Review architectural decisions
4. **Use feature flags** - Enable/disable safely
5. **Test boundaries** - Ensure no circular dependencies

---

## Related Documentation

- [ADR-001: Clean Architecture vs Engine Layer](./ADR-001-Clean-Architecture-vs-Engine-Layer.md)
- [ARCHITECTURE_OVERVIEW.md](../backend/ARCHITECTURE_OVERVIEW.md)
- [Feature Flags Documentation](../backend/infrastructure/feature_flags.py)
- [State Management Guide](../backend/infrastructure/state_persistence/README.md)

---

**Last Updated:** 2025-01-01  
**Maintainer:** Development Team  
**Version:** 1.0.0