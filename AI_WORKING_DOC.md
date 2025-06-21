# Updated AI_WORKING_DOC.md
# AI_WORKING_DOC.md - Liap Tui Development Guide
# 📖 How to Use This Document
**Start HERE for daily work.** This has everything needed for current tasks.
* AI_CONTEXT.md = Historical decisions and current status overview
* This doc = What to do TODAY

⠀🎯 **Quick Context** **Project**: Liap Tui multiplayer board game (FastAPI + PixiJS) **Status**: ✅ Week 1 COMPLETE - State machine foundation working perfectly **Current Task**: Week 2 - Implement remaining 3 phases (Preparation, Turn, Scoring) **Philosophy**: Prevention by design - make bugs impossible
# 📁 Essential Files to Check
Based on what you're working on:
* **State machine core** → backend/engine/state_machine/core.py
* **Declaration implementation** → backend/engine/state_machine/states/declaration_state.py
* **Action queue** → backend/engine/state_machine/action_queue.py
* **Tests** → backend/tests/test_state_machine.py and python backend/run_tests.py
* **Game mechanics** → Read Rules + Game Flow files
* **Current routes** → backend/api/routes/routes.py (to be refactored in Week 3)

⠀🎉 Week 1 - COMPLETED ✅
### ✅ Achievements Unlocked:
* **Phase violations impossible** ✅ Declaration phase only exists when valid
* **Race conditions prevented** ✅ Action queue processes sequentially
* **Clean architecture** ✅ State pattern working perfectly
* **Comprehensive testing** ✅ All tests passing
* **Integration proven** ✅ Works with existing game class

⠀✅ Files Created and Working:

backend/engine/state_machine/
├── core.py                 ✅ Enums and data classes
├── action_queue.py         ✅ Race condition prevention  
├── base_state.py          ✅ Abstract state interface
├── game_state_machine.py  ✅ Central coordinator
└── states/
    └── declaration_state.py ✅ Complete declaration logic

backend/tests/
├── test_state_machine.py   ✅ Comprehensive test suite
├── test_integration.py     ✅ Integration tests
└── __init__.py

backend/
├── run_tests.py           ✅ Quick test runner
└── pytest.ini            ✅ Test configuration
### ✅ Test Results:

🚀 Running quick state machine test...
✅ Started in phase: declaration
✅ Player1 declared: 1
✅ Player2 declared: 2
✅ Player3 declared: 3
✅ Player4 declared: 4
📊 Expected: {'Player1': 1, 'Player2': 2, 'Player3': 3, 'Player4': 4}
📊 Actual:   {'Player1': 1, 'Player2': 2, 'Player3': 3, 'Player4': 4}
🎯 ✅ ALL TESTS PASSED!
# 🔧 Week 2 - IN PROGRESS
### Goal: Complete All 4 Phase States
Transform the remaining game phases into state classes following the proven declaration pattern.
### Current Status:
* ✅ **Declaration State**: Complete and tested
* 🔧 **Preparation State**: Not started
* 🔧 **Turn State**: Not started
* 🔧 **Scoring State**: Not started

⠀📋 Week 2 Tasks
### Task 2.1: Create Preparation State ⏭️ NEXT
**File:** backend/engine/state_machine/states/preparation_state.py**Time:** 90 minutes**Goal:** Handle dealing, weak hands, redeals, starter determination
**What to implement:**

### python
class PreparationState(GameState):
    @property
    def phase_name(self) -> GamePhase:
        return GamePhase.PREPARATION
    
    @property
    def next_phases(self) -> List[GamePhase]:
        return [GamePhase.DECLARATION]
    
    def __init__(self, state_machine):
        super().__init__(state_machine)
        self.allowed_actions = {
            ActionType.REDEAL_REQUEST,
            ActionType.REDEAL_RESPONSE,
            ActionType.PLAYER_DISCONNECT,
            ActionType.PLAYER_RECONNECT
        }
    
    *# Implement: deal cards, check weak hands, handle redeals, determine starter*
**Success criteria:**
* Can deal 8 pieces to each player
* Detects weak hands (no piece > 9 points)
* Handles redeal requests and responses
* Determines round starter correctly
* Transitions to declaration when ready

⠀
### Task 2.2: Create Turn State
**File:** backend/engine/state_machine/states/turn_state.py**Time:** 90 minutes**Goal:** Handle turn sequence, piece play, winner determination
**What to implement:**

### python
class TurnState(GameState):
    @property
    def phase_name(self) -> GamePhase:
        return GamePhase.TURN
    
    @property
    def next_phases(self) -> List[GamePhase]:
        return [GamePhase.SCORING]
    
    def __init__(self, state_machine):
        super().__init__(state_machine)
        self.allowed_actions = {
            ActionType.PLAY_PIECES,
            ActionType.PLAYER_DISCONNECT,
            ActionType.PLAYER_RECONNECT,
            ActionType.TIMEOUT
        }
    
    *# Implement: starter plays 1-6 pieces, others match count, determine winner*
**Success criteria:**
* Starter can play 1-6 pieces
* Other players must match piece count
* Turn winner determined correctly
* Winner gets piles and starts next turn
* Transitions to scoring when all hands empty

⠀
### Task 2.3: Create Scoring State
**File:** backend/engine/state_machine/states/scoring_state.py**Time:** 60 minutes**Goal:** Calculate scores, check win conditions
**What to implement:**

### python
class ScoringState(GameState):
    @property
    def phase_name(self) -> GamePhase:
        return GamePhase.SCORING
    
    @property
    def next_phases(self) -> List[GamePhase]:
        return [GamePhase.PREPARATION]  *# Next round or game end*
    
    def __init__(self, state_machine):
        super().__init__(state_machine)
        self.allowed_actions = {
            ActionType.PLAYER_DISCONNECT,
            ActionType.PLAYER_RECONNECT
        }
    
    *# Implement: calculate scores, check for winner ≥50 points, start next round*
**Success criteria:**
* Calculates scores based on declared vs actual
* Applies redeal multipliers correctly
* Checks for game winner (≥50 points)
* Transitions to preparation for next round or ends game

⠀
### Task 2.4: Add All States to State Machine
**File:** Update backend/engine/state_machine/game_state_machine.py**Time:** 30 minutes**Goal:** Register all 4 states in the state machine
**What to update:**

### python
*# Add imports*
from .states.preparation_state import PreparationState
from .states.turn_state import TurnState  
from .states.scoring_state import ScoringState

*# Update states dict*
self.states = {
    GamePhase.PREPARATION: PreparationState(self),    *# NEW*
    GamePhase.DECLARATION: DeclarationState(self),    *# EXISTING ✅*
    GamePhase.TURN: TurnState(self),                  *# NEW*
    GamePhase.SCORING: ScoringState(self)             *# NEW*
}
**Success criteria:**
* All 4 states registered
* State machine can start in any phase
* Automatic transitions work between all phases

⠀
### Task 2.5: Full Game Flow Test
**File:** backend/test_full_game_flow.py**Time:** 60 minutes**Goal:** Test complete game from preparation through scoring
**What to test:**
* Complete round: Preparation → Declaration → Turn → Scoring
* Multiple rounds until someone wins
* All state transitions automatic
* Game state preserved across phases

⠀🎮 Current Testing Commands (WORKING)

### bash
*# Quick state machine test (WORKING)*
cd backend
python run_tests.py

*# Full pytest suite (WORKING)*  
pytest tests/ -v

*# Individual test files (WORKING)*
pytest tests/test_state_machine.py -v
pytest tests/test_integration.py -v

*# Test specific state (WORKING for declaration)*
pytest tests/test_state_machine.py::TestDeclarationState -v
# 📊 Implementation Pattern (PROVEN)
Based on successful declaration state, use this pattern for all new states:
### 1. State Class Structure ✅ PROVEN:

### python
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
    
    async def _setup_phase(self) -> None:
        *# Initialize phase-specific data*
    
    async def _cleanup_phase(self) -> None:
        *# Copy results to game object*
    
    async def _validate_action(self, action: GameAction) -> bool:
        *# Validate action for this phase*
    
    async def _process_action(self, action: GameAction) -> Dict[str, Any]:
        *# Process valid actions*
    
    async def check_transition_conditions(self) -> Optional[GamePhase]:
        *# Check if ready to transition*
### 2. Testing Pattern ✅ PROVEN:

### python
class Test[Phase]State:
    @pytest_asyncio.fixture
    async def [phase]_state(self, mock_game):
        *# Create and setup state*
        
    @pytest.mark.asyncio  
    async def test_enter_phase_setup(self, [phase]_state):
        *# Test phase initialization*
        
    @pytest.mark.asyncio
    async def test_valid_action(self, [phase]_state):
        *# Test valid action processing*
        
    @pytest.mark.asyncio
    async def test_invalid_action(self, [phase]_state):
        *# Test invalid action rejection*
        
    @pytest.mark.asyncio
    async def test_transition_conditions(self, [phase]_state):
        *# Test when phase should transition*
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

⠀🔧 Week 2: Complete All Phases - IN PROGRESS
* Create Preparation State (Task 2.1) ⏭️ NEXT
* Create Turn State (Task 2.2)
* Create Scoring State (Task 2.3)
* Add all states to state machine (Task 2.4)
* Full game flow test (Task 2.5)
* Performance test all phases
* Documentation updates

⠀📅 Week 3-4: Integration & Refactoring
* Extract phase logic from routes.py → State classes
* Extract bot logic from bot_manager.py → State classes
* Replace all if phase == checks → State pattern
* Update WebSocket handlers to use state machine
* Add comprehensive integration tests
* Performance test with bots

⠀🚫 NOT Doing (Scope Limit)
* ❌ Tournaments
* ❌ Spectator mode
* ❌ Ranking system
* ❌ Payment/monetization
* ❌ Complex social features
* ❌ Fixing existing bugs (we're preventing them with architecture)

⠀✅ Success Criteria (25% Complete)
**1** ✅ **Architectural**: Phase violations impossible by design (PROVEN for declaration) **2** 🔧 **Centralized**: All phase logic in state classes (25% complete)**3** ✅ **Thread-safe**: Race conditions prevented by queuing (PROVEN) **4** 🔧 **Clear boundaries**: Each state handles only its actions (25% complete) **5** ✅ **Maintainable**: Easy to add new features without bugs (PROVEN)
# 🔄 Daily Workflow
**1** **Start**: Run tests to verify current state: python backend/run_tests.py **2** **Code**: Implement next task (currently Task 2.1 - Preparation State) **3** **Test**: Create tests for new state**4** **Verify**: Run full test suite: pytest backend/tests/ -v **5** **Integrate**: Add state to state machine **6** **Document**: Update this file with progress
# 🎯 Remember
* ✅ **Working foundation exists** - declaration state proves the pattern works
* 🔧 **Copy proven patterns** - use declaration state as template
* ✅ **Architecture over patches** - make bugs impossible by design
* ✅ **Test constantly** - every state needs comprehensive tests
* ✅ **Incremental progress** - one state at a time

⠀**Current Status**: Ready for Task 2.1 - Preparation State Implementation**Last Updated**: After Week 1 completion with working state machine foundation**Next Review**: After all 4 phases complete
