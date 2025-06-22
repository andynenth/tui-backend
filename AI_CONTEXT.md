# AI_CONTEXT.md - Reference & Historical Record
**Purpose**: Stable reference information and project history for AI assistant
**For current work**: → Use AI_WORKING_DOC.md

# 🎯 Project Quick Facts
- **Type**: Liap Tui multiplayer board game (FastAPI + PixiJS)
- **Status**: Implementation Phase - State machine architecture 75% complete
- **Current Sprint**: Week 2 - Complete all 4 phase states
- **Philosophy**: Prevention by design - make bugs impossible

# 📊 Implementation History & Lessons

## ✅ Task 2.1: Preparation State - COMPLETED
**Time Taken**: ~3 hours  
**Files Created**:
- backend/engine/state_machine/states/preparation_state.py
- backend/tests/test_preparation_state.py (14 tests)
- backend/tests/test_weak_hand_scenarios.py (6 tests)

**Key Implementations**:
- ✅ Initial deal of 8 pieces per player
- ✅ Weak hand detection (no piece > 9 points)
- ✅ Redeal request/response handling
- ✅ Play order changes when starter changes
- ✅ No redeal limit (can continue indefinitely)
- ✅ Disconnection handling (auto-decline)
- ✅ Comprehensive test coverage (20 tests total)

**Key Learning**: When a player accepts redeal, they become starter AND the play order rotates (A,B,C,D → B,C,D,A if B accepts).

## ✅ Task 2.2: Turn State - COMPLETED WITH BUG FIX
**Time Taken**: ~120 minutes (including bug investigation and fix)  
**Files Created**:
- backend/engine/state_machine/states/turn_state.py
- backend/tests/test_turn_state.py (25 tests)
- backend/run_turn_tests_fixed.py (integration test runner)
- backend/test_fix.py (bug fix verification)
- backend/investigate_bug.py (debugging script)
- Updated backend/engine/state_machine/game_state_machine.py
- Updated backend/engine/state_machine/states/__init__.py

**Key Implementations**:
- ✅ Turn sequence management (starter sets piece count, others follow)
- ✅ Piece count validation (1-6 for starter, must match for others)
- ✅ Winner determination by play value and play order
- ✅ Play type filtering (only matching starter's type can win)
- ✅ Pile distribution to winner
- ✅ Next turn starter assignment (winner starts next)
- ✅ Turn completion and hand management
- ✅ Disconnection/timeout handling with auto-play
- ✅ State machine integration
- ✅ Comprehensive test coverage (25 tests)

**Critical Bug Found & Fixed**:
- **Issue**: Turn completion automatically started next turn, erasing results
- **Root Cause**: Responsibility boundary violation - Turn State doing too much
- **Fix**: Removed automatic turn restart, preserved results, added manual control
- **Lesson**: Single Responsibility Principle prevents complex bugs

**Key Learning**: Winner determination follows priority: play_type match → play_value (descending) → play_order (ascending for ties). Turn State should manage one turn, not turn sequences.

**Proven Testing Approach**:
- Create debug scripts for investigation (investigate_bug.py)
- Build fix verification tests (test_fix.py)  
- Use comprehensive test coverage (25 tests caught the bug)
- Test-driven development prevents integration issues

## 🧪 Proven Testing Patterns
**Working Test Commands** (established and verified):
```bash
# Quick integration test
python backend/run_tests.py

# All preparation tests (20 tests)
./backend/run_preparation_tests.sh

# Turn state tests (25 tests)
python backend/run_turn_tests_fixed.py
python backend/test_fix.py  # Bug fix verification

# Full test suite
pytest backend/tests/ -v

# Individual state tests
pytest backend/tests/test_preparation_state.py -v
pytest backend/tests/test_weak_hand_scenarios.py -v
pytest backend/tests/test_turn_state.py -v
```

**Successful Test Structure Pattern**:
```python
class TestStatePattern:
    @pytest_asyncio.fixture
    async def state_fixture(self, mock_game):
        # Setup pattern that works
        
    @pytest.mark.asyncio
    async def test_enter_phase_setup(self, state_fixture):
        # Test phase initialization
        
    @pytest.mark.asyncio
    async def test_valid_action_processing(self, state_fixture):
        # Test successful action flow
        
    @pytest.mark.asyncio
    async def test_invalid_action_rejection(self, state_fixture):
        # Test validation works
        
    @pytest.mark.asyncio
    async def test_transition_conditions(self, state_fixture):
        # Test when phase should end
```

**Successful Test Structure Pattern**:
```python
class TestStatePattern:
    @pytest_asyncio.fixture
    async def state_fixture(self, mock_game):
        # Setup pattern that works
        
    @pytest.mark.asyncio
    async def test_enter_phase_setup(self, state_fixture):
        # Test phase initialization
        
    @pytest.mark.asyncio
    async def test_valid_action_processing(self, state_fixture):
        # Test successful action flow
        
    @pytest.mark.asyncio
    async def test_invalid_action_rejection(self, state_fixture):
        # Test validation works
        
    @pytest.mark.asyncio
    async def test_transition_conditions(self, state_fixture):
        # Test when phase should end
```

## 🏗️ Proven Implementation Patterns
**State Class Structure** (working template):
```python
class [Phase]State(GameState):
    @property
    def phase_name(self) -> GamePhase:
        return GamePhase.[PHASE]
    
    @property  
    def next_phases(self) -> List[GamePhase]:
        return [GamePhase.[NEXT_PHASE]]
    
    def __init__(self, state_machine):
        super().__init__(state_machine)
        self.allowed_actions = {ActionType.[RELEVANT_ACTIONS]}
        # Phase-specific state variables
    
    async def _setup_phase(self) -> None:
        # Initialize phase-specific data
    
    async def _cleanup_phase(self) -> None:
        # Copy results to game object
    
    async def _validate_action(self, action: GameAction) -> bool:
        # Validate action for this phase
    
    async def _process_action(self, action: GameAction) -> Dict[str, Any]:
        # Process valid actions
    
    async def check_transition_conditions(self) -> Optional[GamePhase]:
        # Check if ready to transition
```

**Development Velocity Tracking**:
- Task 2.1 (Preparation): 3 hours (first state, learning curve)
- Task 2.2 (Turn): 2 hours (including bug fix, pattern established)
- **Estimated Task 2.3 (Scoring)**: 1 hour (pattern proven, simpler logic)

# 📊 Overall Progress Tracking
- **Week 1**: ✅ COMPLETE - State machine foundation working
- **Week 2**: 🔧 75% COMPLETE - 3 of 4 states implemented (Prep, Declaration, Turn)
- **Week 3-4**: 🔧 PLANNED - Integration & refactoring

# 🏗️ Architecture Decisions (PROVEN)
## ✅ Working Design Patterns
1. **State Pattern**: Each game phase = separate state class
2. **Action Queue**: Sequential processing prevents race conditions  
3. **Single Responsibility**: Each state handles only its phase logic
4. **Test-Driven**: Comprehensive tests before integration
5. **Phase Validation**: Invalid actions impossible by design

## 🔥 Critical Bugs Prevented
- **Phase Violations**: States only exist during valid phases
- **Race Conditions**: Action queue processes sequentially
- **Responsibility Boundaries**: Turn state bug caught - each state handles one concern only
- **Play Order Confusion**: Redeal changes tracked properly

# 📁 Files I've Created (Reference for Future Work)

## Core Architecture (Templates to Copy)
- `backend/engine/state_machine/core.py` - Enums and data classes ✅ REFERENCE
- `backend/engine/state_machine/base_state.py` - Abstract state interface ✅ TEMPLATE
- `backend/engine/state_machine/game_state_machine.py` - Central coordinator ✅ INTEGRATION POINT

## Working State Examples (Copy These Patterns)
- `backend/engine/state_machine/states/preparation_state.py` ✅ COMPLEX STATE TEMPLATE
- `backend/engine/state_machine/states/turn_state.py` ✅ LATEST WORKING PATTERN
- `backend/engine/state_machine/states/__init__.py` ✅ REMEMBER TO UPDATE

## Test Patterns That Work
- `backend/tests/test_turn_state.py` ✅ COMPREHENSIVE TEST TEMPLATE
- `backend/run_turn_tests_fixed.py` ✅ INTEGRATION TEST PATTERN

## Debug Tools (For Future Bugs)
- `backend/test_fix.py` ✅ BUG FIX VERIFICATION PATTERN
- `backend/investigate_bug.py` ✅ DEBUGGING SCRIPT TEMPLATE

## Files I Don't Need to Track
- Individual test files (follow the pattern)
- Simple runners (just copy existing ones)
- Documentation updates (not code reference)

# 📁 File & Directory Map
- `Rules` - Complete game mechanics, piece values, scoring
- `Game Flow - *Phase` - Detailed phase requirements and validation

## Legacy Code (To Integrate Later)
- `backend/engine/rules.py` - Game rule implementations
- `backend/api/routes/routes.py` - Current handlers (Week 3 refactor)
- `backend/engine/bot_manager.py` - Bot logic (Week 3 integration)

# 🧠 Key Learning Points
## Play Order Management
**Rule**: When player accepts redeal → becomes starter AND play order rotates
**Example**: A,B,C,D → B accepts → New order: B,C,D,A
**Affects**: All subsequent phases (declaration, turns, etc.)

## Winner Determination Logic
**Priority**: play_type match → play_value (desc) → play_order (asc)
**Key**: Only matching starter's play type can win

## Responsibility Boundaries  
**Lesson**: Turn State should complete one turn and stop
**Anti-pattern**: Automatically starting next turn erases results
**Fix**: External control of turn sequences

## State Transition Rules
**Principle**: States only transition when their specific conditions are met
**Validation**: Transition map prevents invalid phase jumps

# 🎮 Existing Working Systems
- Complete game engine with rules, AI, scoring
- Room system (create, join, host management)  
- WebSocket real-time updates
- Bot players with AI decision making
- Frontend with PixiJS scenes and UI
- Full game flow from lobby to scoring (legacy)

# 📅 Detailed Implementation Roadmap

## Week 3-4: Integration & Refactoring
### Phase Logic Extraction
- Extract phase logic from `routes.py` → State classes
- Extract bot logic from `bot_manager.py` → State classes  
- Replace all `if phase ==` checks → State pattern
- Update WebSocket handlers to use state machine
- Add comprehensive integration tests
- Performance test with bots

### Bot System Integration
- Update bot decision making to use state machine
- Implement fixed delay timing strategy (see Architecture Framework)
- Phase-specific bot behaviors
- Disconnection/reconnection handling for bots

### Route Refactoring
- Replace manual phase checks with state machine validation
- Centralize action processing through state machine
- Update WebSocket message handlers
- Implement delta/patch state synchronization

### Testing & Validation
- End-to-end game flow testing
- Multi-game concurrent testing (5-10 games target)
- Bot vs human testing scenarios
- Network disconnection testing
- Performance benchmarking

## 🏗️ Comprehensive Architecture Framework

### Core Problem Analysis
**Primary Challenges:**
- Phase Violations: Bots declaring during redeal phase
- Race Conditions: Multiple actions happening simultaneously  
- State Synchronization: Keeping all clients in sync
- Complex Game Flow: Multiple phases with specific rules

### Architectural Philosophy
**Guiding Principles:**
- **Single Source of Truth**: Server owns all game state
- **Strict Phase Boundaries**: No action crosses phase lines
- **Event-Driven Design**: Everything is a reaction to events
- **Fail-Safe Defaults**: When in doubt, reject the action

### System Architecture Decisions

#### 1. Phase Transitions: Locked States
**Transition Flow**: Current Phase → [LOCK] → Transition Period → [UNLOCK] → Next Phase
- **Lock Duration**: 450-800ms total
- **Benefits**: No race conditions, clean state boundaries
- **Implementation**: Global action lock during transitions

#### 2. Bot Timing Strategy: Fixed Delays
**Delay Categories:**
- Quick Actions: 500-1000ms (acknowledging, viewing)
- Medium Actions: 1500-3000ms (redeal decisions, declarations)
- Complex Actions: 2000-4000ms (analyzing plays)
- Strategic Actions: 3000-5000ms (critical moments)

#### 3. Conflict Resolution: Phase-Specific Rules
**Timer System:**
- Decision Timer: Time to make game decisions (10-15s)
- Disconnection Timer: Time to reconnect before bot replacement (30s)

**Key Resolution Patterns:**
- Redeal: Process by player order, ALL weak players must decide
- Declaration: Strict turn order, auto-select on timeout
- Turn: Starter processed first, others auto-matched on timeout
- Priority: Server authority, deterministic outcomes

#### 4. State Synchronization: Delta/Patch Updates
**Delta Structure:**
```javascript
{
  type: "state_delta",
  sequence: 1234,
  changes: [{
    path: "players.player1.hand",
    operation: "remove", 
    value: [2, 5]
  }]
}
```
**Benefits**: 90% bandwidth reduction, smooth updates, audit trail

#### 5. Error Handling: Fail Fast and Notify
**Strategy**: Detect → Log → Stop → Notify → Monitor
**Categories**: Validation, State, Network, System errors
**Recovery Boundaries**: Clear what we do/don't attempt to recover

### Scalability Requirements
- **Target**: 5-10 concurrent games (small scale launch)
- **Latency**: 200-1000ms acceptable
- **Reliability**: 30s reconnection window, bot replacement
- **Architecture**: Fat Server/Thin Client, data-driven rules

### Risk Mitigation Strategies
- **Phase Violation Prevention**: Hard boundaries, explicit protocols
- **Race Condition Elimination**: Sequential processing, proper locking
- **State Consistency**: Regular snapshots, reconciliation protocols

### Implementation Components
- **Game Flow Controller**: Orchestrates lifecycle, manages transitions
- **Phase State Machine**: Enforces transitions, stores phase data
- **Action Processing System**: Queues, validates, processes in order
- **Bot Behavior System**: Phase-aware, scheduled actions
- **Client Sync Layer**: WebSocket management, real-time updates

# 🚫 Out of Scope
- Tournaments, spectator mode, ranking system
- Payment/monetization features  
- Complex social features
- Fixing existing legacy bugs (we're preventing them with architecture)

**Last Updated**: After Turn State completion with bug fix
**Next Major Update**: After Scoring State implementation
**Architecture Framework**: Comprehensive 5-aspect system defined