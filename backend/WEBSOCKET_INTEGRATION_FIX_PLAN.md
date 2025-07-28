# WebSocket Integration Fix Plan

## Date: 2025-01-28
## Status: Planning

### Executive Summary

This document outlines a systematic approach to fix the broken WebSocket integration layer discovered after Phase 7 legacy code removal. The plan addresses immediate bugs while establishing proper architectural boundaries for long-term maintainability.

### Current State Analysis

#### Integration Layer Issues

1. **Variable Name Mismatch in ws.py**
   - Uses `registered_ws` (lines 381, 407, 425, 431) but actual variable is `websocket`
   - Causes immediate connection failure: "name 'registered_ws' is not defined"

2. **Broken Imports in ws_adapter_wrapper.py**
   - Line 164: `from shared_instances import shared_room_manager` (module removed)
   - Prevents adapter system from functioning when room state needed

3. **Architectural Coupling**
   - ws.py mixes infrastructure (WebSocket handling) with business logic routing
   - Adapter system has embedded legacy assumptions
   - No clear separation of concerns

#### System Architecture Post-Phase 7

```
Current Flow (Broken):
WebSocket → ws.py → adapter_wrapper → adapter_system → clean architecture
                ↓           ↓
            [ERROR]    [Import Error]
```

### Solution Approach

#### Phase 1: Immediate Fixes (Priority: CRITICAL)

**Objective**: Restore basic functionality

1. **Fix ws.py variable references**
   - Replace all `registered_ws` with `websocket`
   - Verify WebSocket connection lifecycle

2. **Fix ws_adapter_wrapper.py imports**
   - Remove shared_instances import
   - Use clean architecture repositories for room state
   - Update room state retrieval logic

**Checkpoint 1**: System can establish WebSocket connections and handle basic messages

#### Phase 2: Decouple Infrastructure from Business Logic (Priority: HIGH)

**Objective**: Separate concerns properly

1. **Extract WebSocket infrastructure**
   - Create `infrastructure/websocket/websocket_server.py` for pure WebSocket handling
   - Move connection management, rate limiting, validation to infrastructure
   - Keep ws.py as thin routing layer

2. **Refactor message routing**
   - Create `application/websocket/message_router.py` for business logic routing
   - Define clear message flow: Infrastructure → Router → Business Logic
   - Remove business logic from ws.py

**Checkpoint 2**: Clear separation between infrastructure and application layers

#### Phase 3: Modernize Adapter System (Priority: MEDIUM)

**Objective**: Remove legacy assumptions from adapters

1. **Update adapter system architecture**
   - Remove all legacy imports and patterns
   - Use dependency injection for clean architecture services
   - Simplify adapter_wrapper to pure message transformation

2. **Consider adapter removal**
   - Evaluate if adapters are still needed post-migration
   - If kept: modernize completely
   - If removed: direct integration with clean architecture

**Checkpoint 3**: Adapter system works with clean architecture only

#### Phase 4: Establish Clear Boundaries (Priority: MEDIUM)

**Objective**: Prevent future integration issues

1. **Define architectural contracts**
   - Create interface definitions for layer boundaries
   - Document message formats and transformations
   - Establish clear ownership of each component

2. **Add integration tests**
   - Test WebSocket → Clean Architecture flow
   - Verify message handling across boundaries
   - Add contract tests for interfaces

**Checkpoint 4**: Robust, maintainable integration layer

### Implementation Strategy

#### Priorities

1. **Critical**: Fix immediate bugs (Phase 1) - 1-2 hours
2. **High**: Decouple infrastructure (Phase 2) - 4-6 hours  
3. **Medium**: Modernize adapters (Phase 3) - 3-4 hours
4. **Medium**: Establish boundaries (Phase 4) - 2-3 hours

#### Risk Mitigation

1. **Test at each checkpoint** before proceeding
2. **Keep changes focused** - one concern per commit
3. **Maintain backward compatibility** during transition
4. **Use feature flags** if needed for gradual rollout

#### Testing Strategy

1. **Unit Tests**: Each component in isolation
2. **Integration Tests**: Cross-layer communication
3. **E2E Tests**: Full game flow through WebSocket
4. **Load Tests**: Ensure performance maintained

### Architectural Vision

```
Target Architecture:
WebSocket Client
        ↓
[Infrastructure Layer]
websocket_server.py (pure WebSocket handling)
        ↓
[Application Layer]  
message_router.py (business routing)
        ↓
[Clean Architecture]
Use Cases → Domain → Repositories
```

### Success Criteria

1. **Immediate**: Game loads and functions properly
2. **Short-term**: Clean separation of concerns
3. **Long-term**: Maintainable, testable architecture
4. **Quality**: No legacy dependencies or patterns

### Rollback Plan

1. **Git history** available for each phase
2. **Feature flags** can disable new routing if needed
3. **Legacy backup** archive available as last resort

### Next Steps

1. Review and approve this plan
2. Execute Phase 1 (immediate fixes)
3. Validate checkpoint 1
4. Proceed with subsequent phases

### Appendix: File Modifications

#### Phase 1 Files
- `api/routes/ws.py` - Fix variable names
- `api/routes/ws_adapter_wrapper.py` - Fix imports

#### Phase 2 Files  
- Create: `infrastructure/websocket/websocket_server.py`
- Create: `application/websocket/message_router.py`
- Modify: `api/routes/ws.py` - Extract infrastructure

#### Phase 3 Files
- Modify: `api/routes/ws_adapter_wrapper.py` - Modernize
- Modify: `api/adapters/integrated_adapter_system.py` - Remove legacy

#### Phase 4 Files
- Create: `application/interfaces/websocket_contracts.py`
- Create: `tests/integration/test_websocket_flow.py`