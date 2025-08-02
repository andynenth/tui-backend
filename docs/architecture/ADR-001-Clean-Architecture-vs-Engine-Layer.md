# ADR-001: Clean Architecture vs Engine Layer Separation

**Status:** Accepted  
**Date:** 2025-01-01  
**Decision Makers:** Development Team  
**Stakeholders:** Backend Developers, System Architects

## Context

The Liap TUI backend project contains two distinct architectural patterns that operate independently:

1. **Clean Architecture Implementation** (375+ files across 4 layers)
2. **Engine Layer with State Machine** (separate game engine)

This separation has led to architectural confusion and integration issues, specifically:
- Phase transition bugs due to disconnected components
- State persistence not functioning correctly
- Misunderstanding of component responsibilities during development

## Decision

We establish clear architectural boundaries and responsibilities between these two systems:

### Clean Architecture (Primary System)
- **Location:** `backend/` directory
- **Layers:** Domain, Application, Infrastructure, API
- **State Management:** `StateManagementAdapter` + `USE_STATE_PERSISTENCE` flag
- **Event Handling:** `USE_EVENT_SOURCING` flag + `CompositeEventPublisher`
- **Responsibility:** Business logic, data persistence, WebSocket APIs

### Engine Layer (Game Logic System)  
- **Location:** `backend/engine/` directory
- **Components:** `GameStateMachine`, game rules, bot management
- **State Management:** Internal state machine coordination
- **Responsibility:** Game mechanics, phase transitions, bot behavior

## Rationale

### Why Keep Them Separate

1. **Single Responsibility Principle**
   - Clean Architecture handles enterprise concerns (persistence, APIs, business rules)
   - Engine Layer handles game-specific logic (state machines, game flow)

2. **Maintainability**
   - Clear boundaries prevent architectural violations
   - Easier to understand and modify each system independently

3. **Testability**
   - Each system can be tested in isolation
   - Reduces coupling and complexity

### Integration Points

The systems interact through well-defined interfaces:

```
Clean Architecture Use Cases → Engine Layer Services
Clean Architecture Events ← Engine Layer State Changes
```

## Implementation Details

### Feature Flag Strategy

**Clean Architecture flags:**
- `USE_EVENT_SOURCING: True` - Enables database event persistence
- `USE_STATE_PERSISTENCE: True` - Enables state management adapter
- `USE_CLEAN_ARCHITECTURE: True` - Enables Clean Architecture patterns

**Engine Layer flags:**
- Operates independently with internal configuration
- Communicates with Clean Architecture through adapters

### Component Responsibilities

| Component | Responsibility | Layer |
|-----------|----------------|-------|
| `StateManagementAdapter` | State persistence coordination | Clean Architecture |
| `GameStateMachine` | Game phase transitions | Engine Layer |
| `CompositeEventPublisher` | Event distribution | Clean Architecture |
| `EventStore` | Event persistence | Clean Architecture |
| `BotManager` | Bot behavior coordination | Engine Layer |

### Directory Structure

```
backend/
├── domain/           # Clean Architecture - Business entities
├── application/      # Clean Architecture - Use cases, adapters
├── infrastructure/   # Clean Architecture - Persistence, events
├── api/             # Clean Architecture - WebSocket endpoints
└── engine/          # Engine Layer - Game mechanics, state machine
    ├── state_machine/
    ├── bot_manager.py
    └── game.py
```

## Consequences

### Positive
- **Clear Separation of Concerns:** Each system has well-defined responsibilities
- **Reduced Architectural Confusion:** Developers know which system handles what
- **Better Maintainability:** Changes to one system don't affect the other
- **Improved Testability:** Each system can be tested independently

### Negative
- **Integration Complexity:** Requires careful coordination between systems
- **Potential Duplication:** Some concepts (like GamePhase) exist in both systems
- **Learning Curve:** Developers must understand both architectural patterns

### Mitigation Strategies
- Create clear integration adapters between systems
- Establish naming conventions to distinguish components
- Provide comprehensive documentation and examples
- Use feature flags to enable/disable integration points

## Compliance

### Validation Rules

1. **Clean Architecture Compliance:**
   - Domain layer has zero dependencies on Engine layer
   - Infrastructure layer implements Application layer interfaces
   - Dependency inversion principle maintained

2. **Engine Layer Compliance:**
   - Game logic remains independent of persistence concerns
   - State machine operates through well-defined interfaces
   - No direct database or WebSocket dependencies

3. **Integration Compliance:**
   - Communication through adapters only
   - No circular dependencies between systems
   - Clear error handling and fallback mechanisms

### Monitoring

- Automated architecture tests validate layer boundaries
- Code review checklist includes architectural compliance
- Feature flag monitoring ensures proper system coordination

## References

- [Clean Architecture Principles](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [ARCHITECTURE_OVERVIEW.md](../backend/ARCHITECTURE_OVERVIEW.md)
- [BACKEND_LAYER_ANALYSIS.md](../backend/BACKEND_LAYER_ANALYSIS.md)
- [Game Engine Design Patterns](https://gameprogrammingpatterns.com/)

## Revision History

| Date | Author | Changes |
|------|--------|---------|
| 2025-01-01 | Development Team | Initial ADR creation |

---

**Next ADRs:**
- ADR-002: State Machine Integration Patterns
- ADR-003: Event Sourcing Strategy
- ADR-004: Feature Flag Management