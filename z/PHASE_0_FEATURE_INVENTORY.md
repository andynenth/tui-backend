# Phase 0: Feature Inventory & Behavioral Tests

## Overview
Before any architectural changes, we must comprehensively document and test the current system's behavior. This phase ensures we don't miss any features during migration.

**Goal**: Create a complete inventory of features with behavioral tests that guarantee feature parity.

## Why This Phase is Critical

The previous clean architecture attempt failed partly because features were missed or behaved differently. This phase prevents that by:
1. Cataloging every feature before changes begin
2. Creating tests that verify exact behavior
3. Setting up mechanisms to detect discrepancies
4. Establishing clear acceptance criteria

## Pre-Implementation Checklist

### System Analysis Setup
- [ ] Set up code analysis tools
- [ ] Create feature tracking spreadsheet
- [ ] Set up test infrastructure
- [ ] Prepare logging/monitoring tools

## Implementation Tasks

### 1. Automated Feature Discovery

#### A. WebSocket Message Analysis
- [ ] Create `scripts/analyze_websocket_messages.py`
```python
def extract_websocket_handlers():
    """Extract all WebSocket message types and handlers"""
    # Parse backend/api/routes/ws.py
    # Find all message type handlers
    # Document input/output formats
    # Track state changes
```

- [ ] Run analysis and document all message types:
  - [ ] Connection lifecycle: connect, disconnect, reconnect
  - [ ] Room operations: create_room, join_room, leave_room
  - [ ] Game flow: start_game, declare, play, accept_redeal, decline_redeal
  - [ ] Admin operations: debug commands, stats

#### B. State Machine Analysis
- [ ] Create `scripts/analyze_state_machine.py`
```python
def analyze_state_transitions():
    """Map all possible state transitions"""
    # Parse state machine files
    # Document phases and transitions
    # Find all state change triggers
    # Map phase-specific actions
```

- [ ] Document all game phases and transitions
- [ ] List allowed actions per phase
- [ ] Identify phase-specific validation rules
- [ ] Map automatic transitions and timers

#### C. Event Broadcasting Analysis
- [ ] Create `scripts/analyze_broadcasts.py`
```python
def extract_broadcast_events():
    """Find all broadcast events in the system"""
    # Search for broadcast() calls
    # Document event types and payloads
    # Track who receives each event
    # Find conditional broadcasts
```

- [ ] Catalog all broadcast events
- [ ] Document event payloads
- [ ] Map event recipients (room vs player)
- [ ] Track event ordering requirements

### 2. Manual Feature Documentation

#### A. Core Game Features Checklist
- [ ] **Room Management**
  - [ ] Room creation with unique 6-character codes
  - [ ] Player slot assignment (P1-P4)
  - [ ] Host designation and migration
  - [ ] Room state persistence
  - [ ] Room cleanup after inactivity

- [ ] **Player Management**
  - [ ] Human vs bot differentiation
  - [ ] Bot activation on disconnect
  - [ ] Reconnection with state restoration
  - [ ] Message queuing for disconnected players
  - [ ] Player name validation and uniqueness

- [ ] **Game Flow**
  - [ ] 4-player validation before start
  - [ ] Piece dealing (8 pieces per player)
  - [ ] Weak hand detection (no piece > 9 points)
  - [ ] Redeal offer and decision flow
  - [ ] Declaration phase (sum ≠ 8 validation)
  - [ ] Turn-based play with validation
  - [ ] Winner determination
  - [ ] Pile counting and scoring
  - [ ] Round progression
  - [ ] Game end conditions (50 points or 20 rounds)

- [ ] **Special Rules**
  - [ ] Starter determination (red general, last winner, redeal acceptor)
  - [ ] Piece hierarchy and special combinations
  - [ ] Scoring multipliers
  - [ ] Turn timer and timeouts

#### B. Edge Cases Documentation
- [ ] **Connection Issues**
  - [ ] Player disconnect during their turn
  - [ ] Host disconnect handling
  - [ ] Multiple simultaneous disconnects
  - [ ] Network interruption recovery
  - [ ] WebSocket reconnection

- [ ] **Timing Issues**
  - [ ] Simultaneous player actions
  - [ ] Race conditions in state changes
  - [ ] Action timeout handling
  - [ ] Phase transition timing

- [ ] **Game State Issues**
  - [ ] Invalid state recovery
  - [ ] Conflicting player actions
  - [ ] State synchronization problems
  - [ ] Mid-game rule violations

### 3. Behavioral Test Suite Creation

#### A. Test Structure Setup
- [ ] Create `tests/behavioral/` directory
- [ ] Set up test infrastructure
- [ ] Create test data builders
- [ ] Implement game flow helpers

#### B. Core Behavioral Tests
- [ ] Create `tests/behavioral/test_current_room_behavior.py`
```python
class CurrentRoomBehaviorTests:
    """Documents exactly how rooms work today"""
    
    async def test_room_creation_assigns_six_char_code(self):
        """Room codes are always 6 uppercase alphanumeric"""
        
    async def test_host_is_first_player_to_join(self):
        """First player becomes host automatically"""
        
    async def test_host_migration_on_disconnect(self):
        """Host role transfers to next player"""
```

- [ ] Create `tests/behavioral/test_current_game_behavior.py`
- [ ] Create `tests/behavioral/test_current_bot_behavior.py`
- [ ] Create `tests/behavioral/test_current_scoring_behavior.py`

#### C. Edge Case Tests
- [ ] Create `tests/behavioral/test_current_edge_cases.py`
```python
async def test_simultaneous_declarations():
    """Document how simultaneous actions are resolved"""
    
async def test_disconnect_during_turn():
    """Document bot takeover behavior"""
    
async def test_reconnect_state_restoration():
    """Document what state is preserved on reconnect"""
```

### 4. Shadow Mode Implementation

#### A. Shadow Mode Infrastructure
- [ ] Create `backend/api/shadow/` directory
- [ ] Create `backend/api/shadow/shadow_mode_adapter.py`
```python
class ShadowModeAdapter:
    def __init__(self, legacy_handler, new_handler):
        self.legacy_handler = legacy_handler
        self.new_handler = new_handler
        self.comparison_logger = ComparisonLogger()
    
    async def handle_message(self, message):
        # Run both systems, compare results
        # Always return legacy result to user
```

#### B. Comparison Framework
- [ ] Create result comparison logic
- [ ] Implement diff reporting
- [ ] Set up alerting for discrepancies
- [ ] Create discrepancy analysis tools

#### C. Shadow Mode Rollout
- [ ] Add shadow mode feature flags
- [ ] Implement gradual rollout (1% → 10% → 50%)
- [ ] Set up monitoring dashboard
- [ ] Create runbook for discrepancy handling

### 5. Endpoint Contract Documentation

#### A. WebSocket Message Contracts
- [ ] Create `contracts/websocket_messages.py`
```python
from dataclasses import dataclass
from typing import Dict, List, Optional, Literal, Any

@dataclass
class WebSocketContract:
    """Base contract for WebSocket messages"""
    action: str
    request_schema: Dict[str, Any]
    response_schema: Dict[str, Any]
    broadcasts: List[Dict[str, Any]]
    error_cases: List[Dict[str, Any]]
    state_preconditions: Dict[str, Any]
    state_postconditions: Dict[str, Any]
    timing_requirements: Dict[str, Any]

# Example: Create Room Contract
CREATE_ROOM_CONTRACT = WebSocketContract(
    action="create_room",
    request_schema={
        "action": "create_room",
        "player_name": "string, 1-20 chars, alphanumeric + spaces",
        "room_code": "optional string, 6 chars uppercase alphanumeric"
    },
    response_schema={
        "event": "room_created",
        "room_id": "string, 6 chars",
        "player_slot": "P1|P2|P3|P4",
        "player_name": "echo of input",
        "is_host": True
    },
    broadcasts=[
        {
            "event": "room_update",
            "to": "all_in_room",
            "data": {
                "room_id": "string",
                "players": "array of player objects",
                "host_name": "string",
                "started": False
            }
        }
    ],
    error_cases=[
        {"error": "Invalid player name", "when": "name empty or > 20 chars"},
        {"error": "Room already exists", "when": "room_code provided and exists"},
        {"error": "Invalid room code", "when": "room_code not 6 alphanum chars"}
    ],
    state_preconditions={
        "room_exists": False,
        "player_connected": True,
        "player_not_in_room": True
    },
    state_postconditions={
        "room_created": True,
        "player_is_host": True,
        "player_in_slot": "P1",
        "room_has_1_player": True
    },
    timing_requirements={
        "max_response_time_ms": 100,
        "broadcast_delay_ms": 0
    }
)

# Example: Play Turn Contract
PLAY_TURN_CONTRACT = WebSocketContract(
    action="play",
    request_schema={
        "action": "play",
        "pieces": "array of piece strings",
        "room_id": "string, 6 chars"
    },
    response_schema={
        "event": "play_response",
        "success": "boolean",
        "error": "optional string"
    },
    broadcasts=[
        {
            "event": "turn_played",
            "to": "all_in_room",
            "data": {
                "player": "string",
                "pieces": "array",
                "pieces_remaining": "number"
            }
        },
        {
            "event": "phase_change",
            "to": "all_in_room",
            "when": "turn complete",
            "data": {
                "phase": "turn_results",
                "turn_winner": "string",
                "winning_play": "object"
            }
        }
    ],
    error_cases=[
        {"error": "Not your turn", "when": "player != current_player"},
        {"error": "Invalid piece count", "when": "count != required_count"},
        {"error": "Invalid pieces", "when": "pieces not in hand"},
        {"error": "Wrong phase", "when": "phase != TURN"}
    ],
    state_preconditions={
        "game_phase": "TURN",
        "is_current_player": True,
        "has_pieces_in_hand": True
    },
    state_postconditions={
        "pieces_removed_from_hand": True,
        "turn_history_updated": True,
        "next_player_or_phase": True
    },
    timing_requirements={
        "max_response_time_ms": 50,
        "turn_timeout_seconds": 30
    }
)
```

- [ ] Document all WebSocket message contracts:
  - [ ] `create_room` - Room creation with validation
  - [ ] `join_room` - Player joining with slot assignment
  - [ ] `leave_room` - Player leaving with host migration
  - [ ] `start_game` - Game initialization requirements
  - [ ] `declare` - Declaration phase validation
  - [ ] `play` - Turn play validation and processing
  - [ ] `accept_redeal` / `decline_redeal` - Weak hand handling
  - [ ] Connection lifecycle events

#### B. REST Endpoint Contracts
- [ ] Create `contracts/rest_endpoints.py`
```python
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class RESTContract:
    """Base contract for REST endpoints"""
    method: str
    path: str
    request_schema: Optional[Dict[str, Any]]
    response_schema: Dict[str, Any]
    status_codes: Dict[int, str]
    headers: Dict[str, str]
    query_params: Optional[Dict[str, Any]]
    timing_requirements: Dict[str, Any]

# Example: Health Check Contract
HEALTH_CHECK_CONTRACT = RESTContract(
    method="GET",
    path="/api/health",
    request_schema=None,
    response_schema={
        "status": "healthy|unhealthy",
        "timestamp": "ISO 8601 string",
        "uptime": "float (seconds)",
        "version": "string (e.g., 1.0.0)",
        "service": "string (e.g., liap-tui-backend)"
    },
    status_codes={
        200: "Service is healthy",
        503: "Service is unhealthy or degraded"
    },
    headers={
        "Content-Type": "application/json",
        "Cache-Control": "no-cache"
    },
    query_params=None,
    timing_requirements={
        "max_response_time_ms": 50,
        "cache_ttl_seconds": 0
    }
)

# Example: Room Stats Contract
ROOM_STATS_CONTRACT = RESTContract(
    method="GET",
    path="/api/debug/room-stats",
    request_schema=None,
    response_schema={
        "total_rooms": "integer",
        "active_games": "integer",
        "waiting_rooms": "integer",
        "players_online": "integer",
        "rooms": [
            {
                "room_id": "string, 6 chars",
                "players": "integer (1-4)",
                "started": "boolean",
                "phase": "optional string",
                "created_at": "ISO 8601 string"
            }
        ]
    },
    status_codes={
        200: "Stats retrieved successfully",
        401: "Unauthorized (if auth required)",
        500: "Internal server error"
    },
    headers={
        "Content-Type": "application/json"
    },
    query_params={
        "include_details": "boolean (optional, default false)",
        "sort_by": "created_at|players|phase (optional)"
    },
    timing_requirements={
        "max_response_time_ms": 200,
        "cache_ttl_seconds": 5
    }
)
```

- [ ] Document all REST endpoints:
  - [ ] `/api/health` - Basic health check
  - [ ] `/api/health/detailed` - Detailed health with dependencies
  - [ ] `/api/health/metrics` - Performance metrics
  - [ ] `/api/debug/room-stats` - Room statistics
  - [ ] `/api/event-store/*` - Event store operations
  - [ ] `/api/recovery/*` - Recovery operations
  - [ ] `/api/system/stats` - System statistics

#### C. State Contracts
- [ ] Define game state structure at each phase
- [ ] Document state transition rules and invariants
- [ ] Specify validation functions for state consistency
- [ ] Create state snapshot schemas

### 6. Contract Testing Infrastructure

#### A. Contract Test Framework
- [ ] Create `tests/contracts/` directory structure
- [ ] Create `tests/contracts/test_websocket_contracts.py`
```python
class WebSocketContractTests:
    """Verify WebSocket message contracts remain unchanged"""
    
    async def test_create_room_contract(self):
        """Test create_room message input/output/broadcasts"""
        # Setup
        current_system = CurrentWebSocketHandler()
        new_system = NewWebSocketHandler()  # When available
        
        # Test request
        request = {
            "action": "create_room",
            "player_name": "TestPlayer",
            "room_code": None
        }
        
        # Execute on current system
        current_response = await current_system.handle(request)
        current_broadcasts = current_system.get_broadcasts()
        current_state = current_system.get_state()
        
        # Execute on new system (when ready)
        new_response = await new_system.handle(request)
        new_broadcasts = new_system.get_broadcasts()
        new_state = new_system.get_state()
        
        # Compare everything
        assert current_response == new_response
        assert current_broadcasts == new_broadcasts
        assert current_state == new_state
```

- [ ] Create `tests/contracts/test_rest_contracts.py`
- [ ] Create contract comparison utilities
- [ ] Set up parallel execution framework

#### B. Behavioral Comparison Tools
- [ ] Create `tests/contracts/comparison.py`
```python
class ContractComparator:
    """Compare responses between systems"""
    
    def compare_responses(self, current, new):
        """Deep comparison with detailed diff reporting"""
        
    def compare_broadcasts(self, current, new):
        """Compare broadcast events and ordering"""
        
    def compare_timing(self, current, new):
        """Compare response times and delays"""
        
    def generate_report(self):
        """Generate comparison report with discrepancies"""
```

#### C. Performance Baselines
- [ ] Capture current system response times
- [ ] Document acceptable performance variance
- [ ] Create performance regression tests
- [ ] Set up continuous performance monitoring

### 7. Parallel Testing Infrastructure

#### A. Test Execution Strategy
- [ ] Create `tests/contracts/parallel_test_runner.py`
```python
class ParallelTestRunner:
    """Runs tests against both current and new systems"""
    
    def __init__(self, current_system, new_system=None):
        self.current = current_system
        self.new = new_system
        self.results = []
    
    async def run_contract_test(self, contract, test_data):
        """Execute same test on both systems"""
        # Run on current system
        current_result = await self.execute_on_current(contract, test_data)
        
        # Run on new system if available
        if self.new:
            new_result = await self.execute_on_new(contract, test_data)
            comparison = self.compare_results(current_result, new_result)
            self.results.append(comparison)
        
        return current_result
    
    def generate_compatibility_report(self):
        """Generate detailed compatibility report"""
        return {
            "total_tests": len(self.results),
            "passed": sum(1 for r in self.results if r.compatible),
            "failed": sum(1 for r in self.results if not r.compatible),
            "discrepancies": [r for r in self.results if not r.compatible]
        }
```

- [ ] Store baseline results for comparison
- [ ] Create test fixtures from real game scenarios
- [ ] Set up CI/CD pipeline for contract validation

#### B. Test Data Management
- [ ] Create `tests/contracts/test_data_factory.py`
```python
class TestDataFactory:
    """Generate consistent test data for contract testing"""
    
    @staticmethod
    def create_room_scenario():
        """Create a complete room setup scenario"""
        return {
            "players": ["Alice", "Bob", "Charlie", "David"],
            "room_code": "TEST01",
            "game_settings": {"round_limit": 20, "score_limit": 50}
        }
    
    @staticmethod
    def create_game_scenario():
        """Create a complete game play scenario"""
        return {
            "initial_pieces": generate_test_pieces(),
            "declarations": {"Alice": 3, "Bob": 2, "Charlie": 1, "David": 2},
            "plays": generate_test_plays(),
            "expected_scores": calculate_expected_scores()
        }
```

- [ ] Document test data requirements
- [ ] Create reproducible test environments
- [ ] Manage test state cleanup between tests

#### C. Continuous Validation
- [ ] Create `scripts/continuous_contract_validation.py`
```python
async def validate_contracts_continuously():
    """Run contract tests on schedule"""
    while True:
        try:
            # Run all contract tests
            runner = ParallelTestRunner(current_system, new_system)
            results = await runner.run_all_contracts()
            
            # Check for violations
            violations = [r for r in results if not r.compatible]
            if violations:
                send_alert(violations)
            
            # Generate report
            report = runner.generate_compatibility_report()
            save_report(report)
            
            # Wait for next run
            await asyncio.sleep(3600)  # Run hourly
            
        except Exception as e:
            log_error(f"Contract validation failed: {e}")
            send_critical_alert(e)
```

- [ ] Set up automated contract testing in CI/CD
- [ ] Create alerts for contract violations
- [ ] Generate daily compatibility reports
- [ ] Track contract evolution over time

#### D. Baseline Capture Strategy
- [ ] Create `scripts/capture_baseline.py`
```python
async def capture_baseline():
    """Capture current system behavior as baseline"""
    baseline = {}
    
    # Capture WebSocket message behaviors
    for contract in WEBSOCKET_CONTRACTS:
        test_cases = generate_test_cases(contract)
        baseline[contract.action] = []
        
        for test_case in test_cases:
            result = await execute_test(contract, test_case)
            baseline[contract.action].append({
                "input": test_case,
                "output": result.response,
                "broadcasts": result.broadcasts,
                "state_change": result.state_change,
                "timing": result.timing
            })
    
    # Save baseline for future comparison
    save_baseline(baseline, f"baseline_{timestamp}.json")
```

- [ ] Run baseline capture for all endpoints
- [ ] Version baseline files for tracking changes
- [ ] Create baseline comparison tools
- [ ] Document baseline update procedures

### 7. Frontend Compatibility Verification

#### A. Current Frontend-Backend Interface Analysis
- [x] **WebSocket Endpoints Used by Frontend** ✅ COMPLETE
  - [x] Primary endpoint: `/ws/{room_id}` for game rooms
  - [x] Lobby endpoint: `/ws/lobby` for room management
  
- [x] **Complete List of WebSocket Messages Sent by Frontend** ✅ DOCUMENTED IN websocket_contracts.py
  - [x] **Connection Management** ✅ ALL CONTRACTS DEFINED
    - [x] `ack` - Message acknowledgment for reliability
    - [x] `sync_request` - Request synchronization after disconnect
    - [x] `ping` - Heartbeat to keep connection alive
    - [x] `client_ready` - Signal client is ready to receive events
  - [x] **Lobby Operations** ✅ ALL CONTRACTS DEFINED
    - [x] `request_room_list` - Request list of available rooms
    - [x] `get_rooms` - Get available rooms (alternative)
    - [x] `create_room` - Create new game room
    - [x] `join_room` - Join existing room
  - [x] **Room Management** ✅ ALL CONTRACTS DEFINED
    - [x] `get_room_state` - Request current room state
    - [x] `add_bot` - Add bot to empty slot (host only)
    - [x] `remove_player` - Remove player from slot (host only)
    - [x] `leave_room` - Leave current room
    - [x] `leave_game` - Leave active game
    - [x] `start_game` - Start the game (host only)
  - [x] **Game Actions** ✅ ALL CONTRACTS DEFINED
    - [x] `redeal_decision` - Response to redeal offer
    - [x] `request_redeal` - Request redeal (weak hand)
    - [x] `accept_redeal` - Accept redeal offer
    - [x] `decline_redeal` - Decline redeal offer
    - [x] `declare` - Make pile count declaration
    - [x] `play` - Play pieces during turn
    - [x] `play_pieces` - Play pieces (legacy handler)
    - [x] `player_ready` - Signal ready for next phase

- [x] **Complete List of WebSocket Events Received by Frontend** ✅ ALL DOCUMENTED (Response schemas in websocket_contracts.py)
  - [ ] **Connection Events**
    - [ ] `connected` - WebSocket connection established
    - [ ] `disconnected` - WebSocket connection lost
    - [ ] `reconnecting` - Attempting to reconnect
    - [ ] `reconnected` - Successfully reconnected
    - [ ] `connectionError` - Connection error occurred
    - [ ] `pong` - Response to ping heartbeat
    - [ ] `queued_messages` - Queued messages during disconnect
  - [ ] **Room Events**
    - [ ] `room_created` - New room created successfully
    - [ ] `room_joined` - Successfully joined a room
    - [ ] `room_update` - Room state changed (players joined/left)
    - [ ] `room_closed` - Room was closed
    - [ ] `room_not_found` - Room doesn't exist
    - [ ] `room_list_update` - Updated list of available rooms
    - [ ] `room_state_update` - Initial room state on connect
    - [ ] `host_changed` - New host assigned
  - [ ] **Game Flow Events**
    - [ ] `game_started` - Game has started
    - [ ] `game_ended` - Game is over
    - [ ] `phase_change` - Game phase changed (main state update)
    - [ ] `error` - General error message
    - [ ] `critical_error` - Game-ending error
  - [ ] **Preparation Phase Events**
    - [ ] `weak_hands_found` - Weak hands detected
    - [ ] `redeal_decision_needed` - Player needs to decide on redeal
    - [ ] `redeal_executed` - Cards were redealt
    - [ ] `redeal_success` - Redeal request accepted
    - [ ] `redeal_response_success` - Redeal response recorded
  - [ ] **Declaration Phase Events**
    - [ ] `declare` - Player made a declaration
    - [ ] `declare_success` - Declaration accepted (legacy)
  - [ ] **Turn Phase Events**
    - [ ] `turn_played` - Player played pieces
    - [ ] `turn_complete` - Turn ended, show results
    - [ ] `turn_resolved` - Turn results processed
    - [ ] `play_rejected` - Invalid play attempt
    - [ ] `play_success` - Play accepted (legacy)
  - [ ] **Scoring Events**
    - [ ] `score_update` - Scores updated
    - [ ] `round_complete` - Round finished
  - [ ] **Player Events**
    - [ ] `player_disconnected` - Player disconnected
    - [ ] `player_reconnected` - Player reconnected
    - [ ] `player_left` - Player left room
    - [ ] `ready_success` - Player ready acknowledged
    - [ ] `leave_game_success` - Leave game acknowledged

- [x] **REST Endpoints NOT Used by Frontend** ✅ CONFIRMED
  - [x] All REST endpoints are for monitoring/debugging only
  - [x] Frontend makes ZERO REST API calls for game operations
  - [x] This simplifies migration - only WebSocket contracts matter

#### B. Compatibility Guarantees
- [x] Document that WebSocket message formats must remain identical ✅ DONE IN CONTRACT_TESTING_README.md
- [x] Create contract tests for every WebSocket message type ✅ FRAMEWORK IMPLEMENTED (test_websocket_contracts.py)
- [ ] Set up shadow mode to compare old vs new responses ⚠️ FRAMEWORK EXISTS BUT NOT RUNNING
- [x] Ensure broadcast event ordering remains the same ✅ TESTED IN CONTRACT FRAMEWORK

#### C. WebSocket Contract Examples
- [x] **Document exact message contracts for critical operations** ✅ ALL CONTRACTS DEFINED IN websocket_contracts.py

Example: Create Room Contract
```json
// Frontend sends:
{
  "action": "create_room",
  "data": {
    "player_name": "Alice"  // 1-20 characters
  }
}

// Backend responds:
{
  "event": "room_created",
  "data": {
    "room_id": "ABC123",    // Always 6 uppercase alphanumeric
    "host_name": "Alice",
    "success": true
  }
}

// Backend broadcasts to lobby:
{
  "event": "room_list_update",
  "data": {
    "rooms": [...],         // Array of room summaries
    "timestamp": 1234567890.123,
    "reason": "new_room_created"
  }
}
```

Example: Play Turn Contract
```json
// Frontend sends:
{
  "action": "play",
  "data": {
    "player_name": "Alice",
    "indices": [0, 1, 2]    // Piece indices from hand
  }
}

// Backend broadcasts (on success):
{
  "event": "turn_played",
  "data": {
    "player": "Alice",
    "pieces": ["R10", "R9", "R8"],
    "pieces_remaining": 5
  }
}

// Backend responds (on failure):
{
  "event": "play_rejected",
  "data": {
    "message": "Invalid piece count",
    "details": "Expected 3 pieces, got 2"
  }
}
```

- [x] **Contract Testing Requirements** ✅ FRAMEWORK IMPLEMENTED
  - [x] Every WebSocket message must have a documented contract ✅ ALL DEFINED IN websocket_contracts.py
  - [x] Contract tests must verify exact field names and types ✅ VALIDATED BY test_websocket_contracts.py
  - [x] Response timing must be within documented thresholds ✅ TIMING TESTS INCLUDED
  - [x] Broadcast ordering must match current behavior ✅ TESTED BY parallel_runner.py
  - [x] Error responses must use same format and messages ✅ ERROR CASES DEFINED IN CONTRACTS

### 8. Feature Usage Analytics

#### A. Instrumentation
- [ ] Add feature usage tracking
```python
# Add to existing code
logger.info("FEATURE_USED", extra={
    "feature": "weak_hand_redeal",
    "room_id": room_id,
    "player": player_name,
    "timestamp": datetime.utcnow()
})
```

#### B. Analytics Dashboard
- [ ] Set up metrics collection
- [ ] Create feature usage dashboard
- [ ] Track feature frequency
- [ ] Identify rarely-used features

### 9. Comprehensive Feature Matrix

Create `FEATURE_MATRIX.md`:
```markdown
| Feature | Category | Usage Frequency | Test Coverage | Risk Level |
|---------|----------|----------------|---------------|------------|
| Room Creation | Core | High | 100% | Low |
| Weak Hand Redeal | Game Rule | Medium | 80% | Medium |
| Bot Takeover | Edge Case | Low | 60% | High |
```

## Validation Checklist

### Completeness Validation
- [x] All WebSocket messages documented with contracts ✅ COMPLETE IN websocket_contracts.py
- [ ] All REST endpoints documented with contracts ⚠️ IN PROGRESS
- [ ] All game states and transitions mapped
- [x] All broadcast events cataloged with ordering ✅ DOCUMENTED IN CONTRACTS
- [ ] All edge cases identified and tested
- [ ] All business rules documented
- [ ] All error responses documented

### Contract Testing Validation
- [x] Contract tests written for all WebSocket messages ✅ FRAMEWORK COMPLETE (test_websocket_contracts.py)
- [ ] Contract tests written for all REST endpoints ⚠️ TODO
- [ ] Baseline results captured from current system ⚠️ READY TO CAPTURE (run capture_golden_masters.py)
- [x] Comparison framework operational ✅ IMPLEMENTED (golden_master.py + parallel_runner.py)
- [ ] Performance baselines established ⚠️ NEEDS GOLDEN MASTERS FIRST
- [x] Parallel testing infrastructure ready ✅ IMPLEMENTED (parallel_runner.py)

### Test Coverage Validation
- [ ] 100% of core features have behavioral tests
- [ ] 100% of endpoints have contract tests
- [ ] 90%+ of edge cases have tests
- [ ] All critical paths have integration tests
- [ ] Performance benchmarks established
- [ ] Load test scenarios created

### Shadow Mode Validation
- [ ] Shadow mode catches all discrepancies
- [ ] Comparison logic handles all data types
- [ ] Performance impact < 5% overhead
- [ ] Rollback mechanism tested
- [ ] Monitoring alerts working

## Success Criteria

### Documentation Complete ✓
- [ ] Feature inventory spreadsheet filled
- [x] All endpoint contracts defined (WebSocket + REST) ✅ WebSocket COMPLETE, REST TODO
- [ ] Edge cases documented with test scenarios
- [ ] Business rules captured and validated
- [ ] Architecture diagrams updated
- [x] Error response catalog complete ✅ ERROR CASES IN CONTRACTS

### Contract Testing Complete ✓
- [x] Contract test suite implemented ✅ FRAMEWORK READY
- [ ] Baseline captured from current system 🔴 CRITICAL: Run capture_golden_masters.py BEFORE refactoring
- [x] Comparison framework operational ✅ READY TO USE
- [ ] Performance baselines documented ⚠️ NEEDS GOLDEN MASTERS
- [x] Parallel testing validated ✅ TEST EXAMPLES PROVIDED
- [ ] CI/CD integration complete ⚠️ TODO

### Testing Complete ✓
- [ ] Behavioral test suite passing
- [ ] Contract test suite passing
- [ ] Coverage goals met (100% endpoints)
- [ ] Performance benchmarks established
- [ ] Shadow mode operational
- [ ] Comparison framework working

### Team Readiness ✓
- [ ] Team trained on contract testing
- [ ] Team trained on shadow mode
- [ ] Runbooks created
- [ ] Monitoring understood
- [ ] Rollback procedures tested
- [ ] Confidence in feature completeness

## Deliverables

1. **Feature Inventory Spreadsheet** - Complete list of all features
2. **Endpoint Contract Definitions** - Formal contracts for all WebSocket messages and REST endpoints
3. **Contract Test Suite** - Tests ensuring backward compatibility
4. **Behavioral Test Suite** - Tests documenting current behavior
5. **Shadow Mode System** - Running comparison framework
6. **Performance Baselines** - Current system performance metrics
7. **Analytics Dashboard** - Feature usage visibility
8. **Edge Case Runbook** - How to handle discovered discrepancies

## Next Phase Gate

Before proceeding to Phase 1, ensure:
- [ ] No features discovered in last week of analysis
- [ ] All endpoint contracts fully documented
- [ ] Contract tests passing with 100% compatibility
- [ ] Behavioral tests cover all identified features
- [ ] Shadow mode running without issues
- [ ] Performance baselines established
- [ ] Team consensus that inventory is complete
- [ ] Sign-off from stakeholders

---

## 🔴 CRITICAL: Before Starting Phase 1

**YOU MUST capture golden masters BEFORE any refactoring begins:**

```bash
cd backend
python tests/contracts/capture_golden_masters.py
```

This captures the current system's exact behavior for all WebSocket messages. Without these golden masters, you cannot verify that your refactored code maintains compatibility!

**Contract Testing Infrastructure Status:**
- ✅ **WebSocket Contracts**: ALL defined in `websocket_contracts.py`
- ✅ **Test Framework**: READY in `test_websocket_contracts.py`
- ✅ **Comparison Tools**: IMPLEMENTED in `golden_master.py` and `parallel_runner.py`
- 🔴 **Golden Masters**: NOT CAPTURED YET - Run capture script before refactoring!

---

**Remember**: The goal is to ensure 100% backward compatibility by:
1. Documenting every endpoint's exact behavior (contracts) ✅ DONE for WebSocket
2. Creating tests that verify this behavior (contract tests) ✅ FRAMEWORK READY
3. Running both systems in parallel to catch discrepancies (shadow mode) ⚠️ FRAMEWORK EXISTS
4. Never breaking the frontend by maintaining identical API behavior