# WebSocket Integration Fix Plan (Revised)

## Date: 2025-01-28
## Status: Phase 1 Complete, Phase 2 Ready for Execution

### Executive Summary

This document provides a detailed, actionable plan to fix WebSocket integration issues and establish proper architectural boundaries. Each phase includes specific tasks, testing requirements, and documentation updates following a test-driven, documentation-first workflow.

### Current State (Post-Phase 1)

- ✅ Immediate bugs fixed (variable names, imports)
- ✅ WebSocket connections working
- ❌ Architecture still tightly coupled
- ❌ No clear separation of concerns
- ❌ Adapter system contains legacy patterns

---

## Phase 1: Immediate Fixes ✅ COMPLETED

### Objective
Restore basic WebSocket functionality

### Tasks Completed
1. Fixed variable references in ws.py (registered_ws → websocket)
2. Fixed imports in ws_adapter_wrapper.py (removed shared_instances)
3. Created and ran connection tests

### Results
- WebSocket connections establish successfully
- Room creation and game operations work
- See `PHASE_1_WEBSOCKET_FIX_SUMMARY.md` for details

---

## Phase 2: Decouple Infrastructure from Business Logic

### Objective
Separate WebSocket infrastructure from business logic routing

### Pre-Phase Documentation
1. **Document current message flow**
   - File: `docs/websocket/CURRENT_MESSAGE_FLOW.md`
   - Map all WebSocket events and their handlers
   - Identify which code belongs to infrastructure vs business logic

### Task 2.1: Extract WebSocket Infrastructure
**Files to modify:**
- Create: `infrastructure/websocket/websocket_server.py`
- Modify: `api/routes/ws.py`

**Specific actions:**
1. Create `websocket_server.py` with:
   ```python
   class WebSocketServer:
       """Pure WebSocket infrastructure handling"""
       def __init__(self, connection_manager, rate_limiter):
           self.connection_manager = connection_manager
           self.rate_limiter = rate_limiter
       
       async def handle_connection(self, websocket: WebSocket, room_id: str):
           """Handle WebSocket lifecycle"""
           # Move lines 349-363 from ws.py
       
       async def handle_disconnect(self, websocket: WebSocket, room_id: str):
           """Handle disconnection logic"""
           # Move lines 74-185 from ws.py
   ```

2. Extract from `ws.py`:
   - Connection registration (lines 361-363)
   - Disconnection handling (lines 74-185)
   - Rate limiting logic (lines 13-15, validation imports)
   - Message queue operations (lines 42-63)

3. Update `ws.py` imports:
   ```python
   from infrastructure.websocket.websocket_server import WebSocketServer
   ```

### Task 2.2: Create Message Router
**Files to create:**
- `application/websocket/message_router.py`
- `application/websocket/route_registry.py`

**Specific actions:**
1. Create `message_router.py`:
   ```python
   class MessageRouter:
       """Routes WebSocket messages to appropriate handlers"""
       def __init__(self, adapter_wrapper):
           self.adapter_wrapper = adapter_wrapper
           self.routes = self._build_routes()
       
       async def route_message(self, websocket, message, room_id):
           """Route message to appropriate handler"""
           # Extract routing logic from ws.py lines 400-440
   ```

2. Create `route_registry.py`:
   ```python
   # Define all WebSocket event routes
   WEBSOCKET_ROUTES = {
       "get_rooms": "lobby_adapters.handle_get_rooms",
       "create_room": "room_adapters.handle_create_room",
       # ... map all events from adapter system
   }
   ```

3. Update `ws.py` to use router:
   ```python
   # Replace lines 400-440 with:
   response = await message_router.route_message(websocket, message, room_id)
   ```

### Task 2.3: Update Connection Flow
**Files to modify:**
- `api/routes/ws.py`
- `infrastructure/websocket/connection_singleton.py`

**Specific actions:**
1. Simplify `websocket_endpoint` in ws.py to:
   ```python
   @router.websocket("/ws/{room_id}")
   async def websocket_endpoint(websocket: WebSocket, room_id: str):
       server = WebSocketServer(connection_manager, rate_limiter)
       router = MessageRouter(adapter_wrapper)
       
       await server.handle_connection(websocket, room_id)
       try:
           while True:
               message = await websocket.receive_json()
               await router.route_message(websocket, message, room_id)
       except WebSocketDisconnect:
           await server.handle_disconnect(websocket, room_id)
   ```

### Task 2.4: Write Tests
**Files to create:**
- `tests/infrastructure/websocket/test_websocket_server.py`
- `tests/application/websocket/test_message_router.py`
- `tests/integration/test_websocket_infrastructure.py`

**Test coverage required:**
1. Unit tests for WebSocketServer:
   - Connection lifecycle
   - Disconnection handling
   - Rate limiting

2. Unit tests for MessageRouter:
   - Message routing logic
   - Error handling
   - Unknown event handling

3. Integration tests:
   - Full message flow from WebSocket to handlers
   - Connection/disconnection scenarios
   - Error propagation

### Task 2.5: Update Documentation
**Files to create/update:**
- `docs/websocket/ARCHITECTURE.md` - New WebSocket architecture
- `docs/websocket/MESSAGE_ROUTING.md` - How messages are routed
- `infrastructure/websocket/README.md` - Infrastructure components
- `application/websocket/README.md` - Application layer components

### Phase 2 Completion Criteria
- [ ] All infrastructure code extracted from ws.py
- [ ] Message router handles all business logic routing
- [ ] All tests passing (unit + integration)
- [ ] Documentation updated to reflect new architecture
- [ ] No business logic in infrastructure layer
- [ ] No infrastructure concerns in application layer

---

## Phase 2.5: Adapter System Analysis

### Objective
Evaluate whether the adapter system is still needed post-Phase 2

### Analysis Tasks

1. **Document Current Adapter Usage**
   - File: `docs/adapters/CURRENT_USAGE_ANALYSIS.md`
   - List all adapter files and their purposes
   - Map adapter dependencies and interactions
   - Identify value provided by each adapter

2. **Evaluate Direct Integration Feasibility**
   - Can MessageRouter call use cases directly?
   - What transformation logic do adapters provide?
   - Are adapters just pass-through layers now?

3. **Cost/Benefit Analysis**
   - File: `docs/adapters/COST_BENEFIT_ANALYSIS.md`
   - Maintenance cost of keeping adapters
   - Complexity added by adapter layer
   - Benefits of direct use case integration

4. **Create Decision Matrix**
   ```
   | Factor | Keep Adapters | Remove Adapters |
   |--------|---------------|-----------------|
   | Complexity | Medium | Low |
   | Maintainability | Medium | High |
   | Testing | Complex | Simple |
   | Migration Risk | Low | Medium |
   ```

5. **Make Recommendation**
   - Based on analysis, recommend either:
     - Option A: Simplify adapters (Phase 3A)
     - Option B: Remove adapters entirely (Phase 3B)

### Deliverables
- [ ] Usage analysis document
- [ ] Cost/benefit analysis
- [ ] Decision matrix with recommendation
- [ ] Updated Phase 3 plan based on decision

---

## Phase 3A: Simplify Adapter System (If Keeping)

### Objective
Modernize adapters to work with clean architecture only

### Task 3A.1: Remove Legacy Patterns
**Files to modify:**
- All files in `api/adapters/`
- `api/routes/ws_adapter_wrapper.py`

**Specific actions:**
1. Remove all legacy imports
2. Replace with dependency injection
3. Simplify adapter interfaces

### Task 3A.2: Consolidate Adapters
**Actions:**
1. Merge similar adapters
2. Remove pass-through methods
3. Create single adapter per domain

### Task 3A.3: Write Tests
- Unit tests for each adapter
- Integration tests with use cases
- Performance benchmarks

### Task 3A.4: Update Documentation
- Update adapter documentation
- Create adapter usage guide
- Document adapter patterns

---

## Phase 3B: Remove Adapter System (If Removing)

### Objective
Direct integration between WebSocket routing and use cases

### Task 3B.1: Create Direct Use Case Integration
**Files to create:**
- `application/websocket/use_case_dispatcher.py`

**Specific actions:**
1. Create dispatcher to call use cases directly:
   ```python
   class UseCaseDispatcher:
       def __init__(self, unit_of_work):
           self.uow = unit_of_work
           self.use_cases = self._initialize_use_cases()
       
       async def dispatch(self, event: str, data: dict):
           """Dispatch event to appropriate use case"""
           use_case = self.use_cases.get(event)
           if not use_case:
               raise UnknownEventError(f"Unknown event: {event}")
           return await use_case.execute(data)
   ```

2. Map events to use cases directly

### Task 3B.2: Update Message Router
**Files to modify:**
- `application/websocket/message_router.py`

**Actions:**
1. Replace adapter calls with use case dispatcher
2. Handle response transformation
3. Update error handling

### Task 3B.3: Remove Adapter Files
**Actions:**
1. Delete `api/adapters/` directory
2. Delete `api/routes/ws_adapter_wrapper.py`
3. Update all imports

### Task 3B.4: Write Tests
- Unit tests for dispatcher
- Integration tests for direct flow
- E2E tests for all game operations

### Task 3B.5: Update Documentation
- Document new direct integration
- Update architecture diagrams
- Create migration guide

---

## Phase 4: Establish Clear Boundaries

### Objective
Define and enforce architectural boundaries

### Task 4.1: Define Layer Contracts
**Files to create:**
- `application/interfaces/websocket_contracts.py`
- `infrastructure/interfaces/websocket_infrastructure.py`

**Specific actions:**
1. Define infrastructure interface:
   ```python
   class IWebSocketInfrastructure(ABC):
       @abstractmethod
       async def accept_connection(self, websocket: WebSocket) -> str:
           """Accept and register connection"""
       
       @abstractmethod
       async def send_message(self, connection_id: str, message: dict):
           """Send message to connection"""
   ```

2. Define application interface:
   ```python
   class IMessageHandler(ABC):
       @abstractmethod
       async def handle_message(self, connection_id: str, message: dict) -> dict:
           """Handle incoming message"""
   ```

### Task 4.2: Implement Contract Tests
**Files to create:**
- `tests/contracts/test_infrastructure_contracts.py`
- `tests/contracts/test_application_contracts.py`

**Test requirements:**
1. Verify all interfaces are properly implemented
2. Test contract violations fail appropriately
3. Ensure backward compatibility

### Task 4.3: Add Architectural Tests
**Files to create:**
- `tests/architecture/test_layer_boundaries.py`

**Tests to implement:**
1. Infrastructure doesn't import from application
2. Application doesn't import from API
3. Domain remains pure (no external imports)

### Task 4.4: Create Monitoring
**Files to create:**
- `infrastructure/monitoring/websocket_metrics.py`

**Metrics to track:**
1. Connection count
2. Message throughput
3. Error rates by layer
4. Response times

### Task 4.5: Final Documentation
**Files to create/update:**
- `docs/ARCHITECTURE_GUIDE.md` - Complete architecture overview
- `docs/INTEGRATION_PATTERNS.md` - How layers integrate
- `docs/TROUBLESHOOTING_GUIDE.md` - Common issues and solutions
- `README.md` - Update with new architecture

### Phase 4 Completion Criteria
- [ ] All contracts defined and implemented
- [ ] Contract tests passing
- [ ] Architectural tests enforcing boundaries
- [ ] Monitoring in place
- [ ] Complete documentation suite

---

## Success Metrics

### Per-Phase Metrics
1. **Test Coverage**: Minimum 90% for new code
2. **Documentation**: All new components documented
3. **Performance**: No degradation from current baseline
4. **Complexity**: Cyclomatic complexity < 10 per method

### Overall Project Metrics
1. **Separation of Concerns**: Clear layer boundaries
2. **Maintainability**: Easy to add new WebSocket events
3. **Testability**: Can test each layer in isolation
4. **Observability**: Full visibility into message flow

---

## Risk Management

### Phase 2 Risks
- **Risk**: Breaking existing functionality
- **Mitigation**: Comprehensive integration tests before refactoring

### Phase 3 Risks
- **Risk**: Performance impact from additional layers
- **Mitigation**: Benchmark before/after, optimize hot paths

### Phase 4 Risks
- **Risk**: Over-engineering boundaries
- **Mitigation**: Focus on practical enforcement, not perfection

---

## Timeline

- **Phase 2**: 6-8 hours (including tests and docs)
- **Phase 2.5**: 2-3 hours (analysis only)
- **Phase 3**: 4-6 hours (depending on decision)
- **Phase 4**: 3-4 hours

**Total**: 15-21 hours of focused development

---

## Next Steps

1. Review and approve this revised plan
2. Begin Phase 2 implementation
3. Follow test-driven development approach
4. Update documentation continuously
5. Review at each phase completion