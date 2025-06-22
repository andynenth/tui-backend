# AI_WORKING_DOC.md - Liap Tui Development Guide
# 📖 How to Use This Document
**Start HERE for daily work.** This has everything needed for current tasks.
* AI_CONTEXT.md = Historical decisions and current status overview
* This doc = What to do TODAY

## 🎯 Quick Context
**Project**: Liap Tui multiplayer board game (FastAPI + PixiJS)  
**Status**: ✅ Week 1 COMPLETE, Week 2 Task 2.2 COMPLETE WITH BUG FIX  
**Current Task**: Week 2 Task 2.3 - Implement Scoring State  
**Philosophy**: Prevention by design - make bugs impossible

# 📁 Essential Files to Check
Based on what you're working on:
* **State machine core** → backend/engine/state_machine/core.py
* **Preparation example** → backend/engine/state_machine/states/preparation_state.py ✅
* **Declaration example** → backend/engine/state_machine/states/declaration_state.py ✅
* **Turn example** → backend/engine/state_machine/states/turn_state.py ✅
* **Tests** → backend/tests/test_*.py and python backend/run_tests.py
* **Game mechanics** → Read Rules + Game Flow files
* **Current routes** → backend/api/routes/routes.py (to be refactored in Week 3)

## 🎉 Week 1 - COMPLETED ✅
### ✅ Achievements Unlocked:
* **Phase violations impossible** ✅ Declaration phase only exists when valid
* **Race conditions prevented** ✅ Action queue processes sequentially
* **Clean architecture** ✅ State pattern working perfectly
* **Comprehensive testing** ✅ All tests passing
* **Integration proven** ✅ Works with existing game class

## 🔧 Week 2 - IN PROGRESS (75% COMPLETE)
### Goal: Complete All 4 Phase States
Transform the remaining game phases into state classes following the proven pattern.

### Current Status:
* ✅ **Declaration State**: Complete and tested
* ✅ **Preparation State**: Complete with full weak hand/redeal logic
* ✅ **Turn State**: Complete and tested with bug fix ✅ NEW
* 🔧 **Scoring State**: Not started - NEXT UP

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

## ✅ Task 2.2: Turn State - COMPLETED WITH BUG FIX ✅ NEW
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

**Bug Found & Fixed**:
- **Issue**: Turn completion automatically started next turn, erasing results
- **Root Cause**: Responsibility boundary violation - Turn State doing too much
- **Fix**: Removed automatic turn restart, preserved results, added manual control
- **Lesson**: Single Responsibility Principle prevents complex bugs

**Key Learning**: Winner determination follows priority: play_type match → play_value (descending) → play_order (ascending for ties). Turn State should manage one turn, not turn sequences.

## 📋 Week 2 Tasks

### ✅ Task 2.2: Create Turn State - COMPLETED
**File:** backend/engine/state_machine/states/turn_state.py  
**Time:** 90 minutes  
**Goal:** Handle turn sequence, piece play, winner determination

**Success criteria:** ✅ ALL ACHIEVED
* ✅ Starter can play 1-6 pieces
* ✅ Other players must match piece count
* ✅ Turn winner determined correctly
* ✅ Winner gets piles and starts next turn
* ✅ Transitions to scoring when all hands empty

### Task 2.3: Create Scoring State ⏭️ NEXT
**File:** backend/engine/state_machine/states/scoring_state.py  
**Time:** 60 minutes  
**Goal:** Calculate scores, check win conditions

**What to implement:**
```python
class ScoringState(GameState):
    @property
    def phase_name(self) -> GamePhase:
        return GamePhase.SCORING
    
    @property
    def next_phases(self) -> List[GamePhase]:
        return [GamePhase.PREPARATION]  # Next round or end game
    
    def __init__(self, state_machine):
        super().__init__(state_machine)
        self.allowed_actions = {
            ActionType.CONTINUE_GAME,
            ActionType.END_GAME,
            ActionType.PLAYER_DISCONNECT,
            ActionType.PLAYER_RECONNECT
        }
    
    # Implement: calculate scores, apply multipliers, check win conditions
```

**Success criteria:**
* Calculates scores based on declared vs actual piles
* Applies redeal multipliers correctly
* Checks for game winner (≥50 points)
* Transitions to preparation for next round or ends game

### Task 2.4: Add All States to State Machine
**File:** Update backend/engine/state_machine/game_state_machine.py  
**Time:** 30 minutes  
**Goal:** Register all 4 states in the state machine

### Task 2.5: Full Game Flow Test
**File:** backend/test_full_game_flow.py  
**Time:** 60 minutes  
**Goal:** Test complete game from preparation through scoring

## 🎮 Current Testing Commands (WORKING)
```bash
# Quick state machine test
cd backend
python run_tests.py

# All preparation tests (20 tests)
./run_preparation_tests.sh

# Turn state tests ✅ NEW
python run_turn_tests_fixed.py
python test_fix.py  # Bug fix verification

# Full pytest suite
pytest tests/ -v

# Test specific state
pytest tests/test_preparation_state.py -v
pytest tests/test_weak_hand_scenarios.py -v
pytest tests/test_turn_state.py -v  # ✅ NEW
```

# 📊 Implementation Pattern (PROVEN)
Based on successful declaration, preparation, and turn states, use this pattern:

### 1. State Class Structure:
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
        self.allowed_actions = {
            ActionType.[RELEVANT_ACTIONS]
        }
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

### 2. Testing Pattern:
```python
class Test[Phase]State:
    @pytest_asyncio.fixture
    async def [phase]_state(self, mock_game):
        # Create and setup state
        
    @pytest.mark.asyncio  
    async def test_enter_phase_setup(self, [phase]_state):
        # Test phase initialization
        
    @pytest.mark.asyncio
    async def test_valid_action(self, [phase]_state):
        # Test valid action processing
        
    @pytest.mark.asyncio
    async def test_invalid_action(self, [phase]_state):
        # Test invalid action rejection
        
    @pytest.mark.asyncio
    async def test_transition_conditions(self, [phase]_state):
        # Test when phase should transition
```

# 📋 Implementation Checklist
### ✅ Week 1: Architecture Foundation - COMPLETE
* ✅ Design state pattern for phases
* ✅ Create abstract State base class
* ✅ Implement state transition logic
* ✅ Design action queue system
* ✅ Create declaration state class
* ✅ Build basic state machine
* ✅ Integration test with existing game
* ✅ Comprehensive test suite with pytest

### 🔧 Week 2: Complete All Phases - IN PROGRESS (75% COMPLETE)
* ✅ Create Preparation State (Task 2.1) 
* ✅ Create Turn State (Task 2.2) ✅ NEW
* 🔧 Create Scoring State (Task 2.3) ⏭️ NEXT
* 🔧 Add all states to state machine (Task 2.4)
* 🔧 Full game flow test (Task 2.5)
* 🔧 Performance test all phases
* 🔧 Documentation updates

### 📅 Week 3-4: Integration & Refactoring
* Extract phase logic from routes.py → State classes
* Extract bot logic from bot_manager.py → State classes
* Replace all if phase == checks → State pattern
* Update WebSocket handlers to use state machine
* Add comprehensive integration tests
* Performance test with bots

### 🚫 NOT Doing (Scope Limit)
* ❌ Tournaments
* ❌ Spectator mode
* ❌ Ranking system
* ❌ Payment/monetization
* ❌ Complex social features
* ❌ Fixing existing bugs (we're preventing them with architecture)

## ✅ Success Criteria (75% Complete)
1. ✅ **Architectural**: Phase violations impossible by design (PROVEN)
2. ✅ **Centralized**: All phase logic in state classes (75% complete)
3. ✅ **Thread-safe**: Race conditions prevented by queuing (PROVEN)
4. ✅ **Clear boundaries**: Each state handles only its actions (75% complete)
5. ✅ **Maintainable**: Easy to add new features without bugs (PROVEN)

# 🔄 Daily Workflow
1. **Start**: Run tests to verify current state: `python backend/run_tests.py`
2. **Code**: Implement next task (currently Task 2.3 - Scoring State)
3. **Test**: Create tests for new state
4. **Verify**: Run full test suite: `pytest backend/tests/ -v`
5. **Integrate**: Add state to state machine
6. **Document**: Update this file with progress

# 🎯 Remember
* ✅ **Working foundation exists** - declaration, preparation, and turn states prove the pattern
* 🔧 **Copy proven patterns** - use existing states as templates
* ✅ **Architecture over patches** - make bugs impossible by design
* ✅ **Test constantly** - every state needs comprehensive tests
* ✅ **Incremental progress** - one state at a time
* ✅ **Play order matters** - redeal changes affect everything
* ✅ **Winner logic** - play type matching, then value, then order
* ✅ **Single responsibility** - each state handles one concern only

**Current Status**: Ready for Task 2.3 - Scoring State Implementation  
**Last Updated**: After Task 2.2 completion with bug fix (Turn State)  
**Next Review**: After Scoring State complete