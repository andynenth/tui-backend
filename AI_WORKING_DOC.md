# AI_WORKING_DOC.md - Current Sprint Workspace
**Purpose**: Dynamic workspace for immediate development tasks
**For history/reference**: → Use AI_CONTEXT.md

# 🎯 Current Status
**Active Task**: Task 2.3 - Implement Scoring State  
**Sprint**: Week 2 - Complete All 4 Phase States (75% done)  
**Next**: 1 state remaining, then integration testing

## Task Progress This Sprint
- ✅ Task 2.1: Preparation State (3h) 
- ✅ Task 2.2: Turn State + Bug Fix (2h)
- 🔧 **Task 2.3: Scoring State** ← CURRENT
- 🔧 Task 2.4: Add Scoring State to StateMachine (15min)
- 🔧 Task 2.5: Full Game Flow Test (1h)

# 🎯 CURRENT TASK: Scoring State Implementation

## What to Build
**File**: `backend/engine/state_machine/states/scoring_state.py`  
**Goal**: Calculate scores, apply multipliers, check win conditions, transition logic  
**Time**: ~60 minutes

## Success Criteria
- ✅ Calculate base scores: declared vs actual piles
- ✅ Apply redeal multipliers (×2, ×3, ×4, etc.)  
- ✅ Check for game winner (≥50 points)
- ✅ Transition to next round or end game
- ✅ Comprehensive test coverage (15+ tests)

## Implementation Template
```python
class ScoringState(GameState):
    @property
    def phase_name(self) -> GamePhase:
        return GamePhase.SCORING
    
    @property
    def next_phases(self) -> List[GamePhase]:
        return [GamePhase.PREPARATION]  # Next round
    
    def __init__(self, state_machine):
        super().__init__(state_machine)
        self.allowed_actions = {
            ActionType.VIEW_SCORES,  # May need to add to core.py
            ActionType.CONTINUE_ROUND,
            ActionType.PLAYER_DISCONNECT,
            ActionType.PLAYER_RECONNECT
        }
        
        # Phase-specific state
        self.round_scores: Dict[str, int] = {}
        self.game_complete: bool = False
        self.winner: Optional[str] = None
        
    # Copy pattern from preparation_state.py and turn_state.py
```

## Scoring Logic Reference
From Rules in project knowledge:
- **Perfect match**: declared + 5 bonus
- **Declared 0, got 0**: +3 bonus  
- **Declared 0, got >0**: -actual piles
- **Missed target**: -|difference|
- **Redeal multiplier**: Apply after base calculation

# 🧪 Working Test Commands
```bash
# Quick verification
cd backend && python run_tests.py

# Create new scoring tests  
pytest tests/test_scoring_state.py -v  # After creating

# Full test suite
pytest tests/ -v

# Previous state tests (working examples)
python run_turn_tests_fixed.py
pytest tests/test_turn_state.py -v
```

# 📋 Proven Implementation Pattern
**Copy from**: `preparation_state.py` and `turn_state.py`

## 1. State Class Structure
```python
async def _setup_phase(self) -> None:
    """Initialize scoring - gather data from game"""
    
async def _cleanup_phase(self) -> None:
    """Save results to game object"""
    
async def _validate_action(self, action: GameAction) -> bool:
    """Validate scoring actions"""
    
async def _process_action(self, action: GameAction) -> Dict[str, Any]:
    """Process valid actions"""
    
async def check_transition_conditions(self) -> Optional[GamePhase]:
    """Check if ready for next round or game end"""
```

## 2. Test Structure  
**Copy from**: `test_turn_state.py`
```python
class TestScoringState:
    @pytest_asyncio.fixture
    async def scoring_state(self, mock_game):
        # Setup pattern
        
    @pytest.mark.asyncio
    async def test_perfect_declarations(self, scoring_state):
        # Test perfect scores get +5 bonus
        
    @pytest.mark.asyncio
    async def test_zero_declarations(self, scoring_state):
        # Test declared 0, got 0 = +3
        # Test declared 0, got >0 = -actual
        
    @pytest.mark.asyncio
    async def test_redeal_multipliers(self, scoring_state):
        # Test ×2, ×3, ×4 multipliers
```

# 🔄 Daily Workflow
1. **Verify current state**: `python run_tests.py`
2. **Implement scoring_state.py** (60min)
3. **Create test_scoring_state.py** (30min)  
4. **Integration**: Add to game_state_machine.py (15min)
5. **Verify**: Run full test suite
6. **Update this doc**: Mark complete, move to Task 2.4

# 🎯 Next 2 Tasks (After Scoring)

## Task 2.4: Add Scoring State to StateMachine  
**File**: `backend/engine/state_machine/game_state_machine.py`
**Time**: 15 minutes
**Goal**: Register ScoringState in states dict, update imports

## Task 2.5: Full Game Flow Test
**File**: `backend/test_full_game_flow.py`  
**Time**: 60 minutes
**Goal**: Test complete cycle: Prep → Declaration → Turn → Scoring → Next Round

# 🔧 Quick Reference
- **Examples**: preparation_state.py, turn_state.py ✅
- **Core enums**: backend/engine/state_machine/core.py
- **Game rules**: Project Knowledge → Rules
- **Scoring rules**: Project Knowledge → Game Flow - Scoring Phase
- **Architecture**: AI_CONTEXT.md → Comprehensive Architecture Framework
- **Future planning**: AI_CONTEXT.md → Week 3-4 Implementation Roadmap

**Last Updated**: Ready for Task 2.3 - Scoring State implementation  
**Next Update**: After Scoring State complete