# AI Hand Evaluation Consistency Implementation Plan

## Executive Summary

This plan addresses inconsistencies between hand evaluation in the declaration phase (`ai.py`) and turn play phase (`ai_turn_strategy.py`). The core issue is that the turn play phase uses value-based categorization while it should use role-based categorization aligned with the bot's strategic plan.

**Key Changes**:
- Burden pieces will be defined by role in plan, not by point value
- High-value pieces (e.g., ADVISOR) can be burden if not needed for the plan
- Opener play timing based on hand size vs plan size
- Import and align with declaration phase field strength logic

## Current State Analysis

### Declaration Phase (`backend/engine/ai.py`)
- **Lines 89-107**: `evaluate_opener_reliability()` - considers field strength
- **Lines 109-181**: `filter_viable_combos()` - sophisticated combo filtering
- **Lines 226-229**: Strong combos include THREE_OF_A_KIND and above
- **Lines 246-263**: Opener evaluation with reliability scores

### Turn Play Phase (`backend/engine/ai_turn_strategy.py`)
- **Lines 212-241**: `identify_opener_pieces()` - simple ≥11 point threshold
- **Lines 244-268**: `identify_burden_pieces()` - treats non-combo pieces as burden
- **Lines 183-209**: `evaluate_hand()` - causes openers to become burden pieces
- **Problem**: Line 265 makes ANY piece not in a combo a burden piece

## Safety Requirements

- [ ] All changes must maintain backward compatibility
- [ ] No changes to game rules or mechanics
- [ ] Preserve existing overcapture avoidance (working at ~100%)
- [ ] Maintain valid play rate at 100%
- [ ] Keep decision speed <100ms

## Implementation Plan

### Phase 1: Update Data Structures ✅ COMPLETE

#### Task 1.1: Extend StrategicPlan Dataclass ✅
**File**: `backend/engine/ai_turn_strategy.py`
**Location**: Line 29

- [x] Add field: `assigned_openers: List[Piece] = field(default_factory=list)`
- [x] Add field: `assigned_combos: List[Tuple[str, List[Piece]]] = field(default_factory=list)`
- [x] Add field: `reserve_pieces: List[Piece] = field(default_factory=list)`
- [x] Add field: `burden_pieces: List[Piece] = field(default_factory=list)`
- [x] Add field: `main_plan_size: int = 0`
- [x] Add field: `plan_impossible: bool = False`
- [x] Test: Verify dataclass instantiation still works

### Phase 2: Import Declaration Logic ✅ COMPLETE

#### Task 2.1: Add Imports from ai.py ✅
**File**: `backend/engine/ai_turn_strategy.py`
**Location**: After line 6 (imports section)

- [x] Add import: `from backend.engine.ai import assess_field_strength`
- [x] Test: Verify import works without circular dependency

#### Task 2.2: Create Field Strength Adapter ✅
**File**: `backend/engine/ai_turn_strategy.py`
**Location**: After `calculate_urgency()` function (around line 297)

- [x] Create function: `get_field_strength_from_players(player_states: Dict[str, Dict]) -> str`
- [x] Extract opponent declarations from player_states
- [x] Call `assess_field_strength()` with opponent declarations
- [x] Test: Verify returns "weak", "normal", or "strong"

### Phase 3: Add Plan Formation ✅ COMPLETE

#### Task 3.1: Create Combo Viability Function ✅
**File**: `backend/engine/ai_turn_strategy.py`
**Location**: After field strength adapter

- [x] Create function: `is_combo_viable(combo_type: str, pieces: List[Piece], field_strength: str) -> bool`
- [x] Implement pair viability logic:
  - Weak field: pairs ≥10 points viable
  - Normal field: pairs ≥14 points viable  
  - Strong field: pairs ≥18 points viable
- [x] THREE_OF_A_KIND and above always viable
- [x] Test: Verify SOLDIER pair not viable, HORSE pair viable in weak field

#### Task 3.2: Create Plan Formation Function ✅
**File**: `backend/engine/ai_turn_strategy.py`
**Location**: After combo viability function

- [x] Create function: `form_execution_plan(hand: List[Piece], context: TurnPlayContext, valid_combos: List[Tuple]) -> Dict`
- [x] Check if `context.turn_number == 1` (only form plan on turn 1)
- [x] Get field strength using adapter function
- [x] Filter combos for viability using `is_combo_viable()`
- [x] Assign openers based on target remaining:
  - 0-1 piles needed: 0 openers
  - 2-3 piles needed: 1 opener (strongest)
  - 4+ piles needed: 2 openers
- [x] Assign viable combos to plan
- [x] Reserve 1-2 weakest pieces (point ≤ 4)
- [x] Calculate `main_plan_size`
- [x] Everything else = burden pieces
- [x] Test: Verify high-value pieces can be burden (ADVISOR became burden)

### Phase 4: Update Hand Evaluation ✅ COMPLETE

#### Task 4.1: Modify evaluate_hand Function ✅
**File**: `backend/engine/ai_turn_strategy.py`
**Location**: Lines 183-209

- [x] Remove lines 264-265 (current burden logic)
- [x] Add plan formation check:
  ```python
  if context.turn_number == 1 and not plan.assigned_openers:
      # Form initial plan
  ```
- [x] Return categorized pieces based on plan assignments
- [x] Test: Verify GENERAL not classified as burden when it's an opener

#### Task 4.2: Update generate_strategic_plan Function ✅
**File**: `backend/engine/ai_turn_strategy.py`
**Location**: Lines 300-313

- [x] Add plan formation on turn 1
- [x] Store role assignments in StrategicPlan object
- [x] Add check: `if key_piece_lost: plan.plan_impossible = True`
- [x] Test: Verify plan persists across turns

### Phase 5: Update Execution Logic ✅ COMPLETE

#### Task 5.1: Add Opener Timing Logic ✅
**File**: `backend/engine/ai_turn_strategy.py`
**Location**: In `execute_starter_strategy()` around line 346

- [x] Add before opener logic:
  ```python
  # Check if plan is opener-only
  opener_only_plan = len(plan.assigned_combos) == 0
  
  if context.required_piece_count == 1 and plan.assigned_openers:
      if opener_only_plan:
          # Opener-only plan: play more freely throughout the game
          hand_size = len(context.my_hand)
          if hand_size >= 6:
              chance = 0.35  # 35% chance early
          elif hand_size >= 4:
              chance = 0.40  # 40% chance mid-game
          else:
              chance = 0.50  # 50% chance late game
              
          if random.random() < chance:
              return [plan.assigned_openers[0]]
      else:
          # Mixed plan: protect combos
          if len(context.my_hand) > plan.main_plan_size:
              if random.random() < 0.3:  # 30% chance
                  return [plan.assigned_openers[0]]
  ```
- [x] Import random at top of file
- [x] Test: Verify opener plays randomly when hand size allows
- [x] Test: Verify opener-only plans have different timing
- [x] Test: Verify openers spread across round for opener-only plans

#### Task 5.2: Update Burden Disposal Logic ✅
**File**: `backend/engine/ai_turn_strategy.py`
**Location**: Lines 357-363

- [x] Replace current burden disposal with:
  ```python
  if plan.urgency_level in ["low", "medium"] and plan.burden_pieces:
      # Sort burden by value descending (dispose high value first)
      sorted_burden = sorted(plan.burden_pieces, key=lambda p: -p.point)
  ```
- [x] Prioritize high-value burden disposal
- [x] Test: Verify ADVISOR disposed before SOLDIER when both are burden

#### Task 5.3: Create Aggressive Capture Function ✅
**File**: `backend/engine/ai_turn_strategy.py`
**Location**: After `execute_starter_strategy()`

- [x] Create function: `execute_aggressive_capture(hand: List[Piece], required_count: int) -> List[Piece]`
- [x] Logic: Play strongest possible combinations
- [x] Use when `plan.plan_impossible == True`
- [x] Test: Verify switches strategy when plan broken

### Phase 6: Integration Updates ✅ COMPLETE

#### Task 6.1: Update Main Decision Function ✅
**File**: `backend/engine/ai_turn_strategy.py`
**Location**: Lines 86-116 in `choose_strategic_play()`

- [x] Check for plan impossibility:
  ```python
  if plan.plan_impossible and plan.urgency_level != "none":
      result = execute_aggressive_capture(hand, context.required_piece_count)
  ```
- [x] Test: Verify fallback activates correctly

### Phase 7: Testing ✅ COMPLETE

#### Task 7.1: Create Unit Tests ✅
**File**: Create `tests/ai_turn_play/test_hand_evaluation_consistency.py`

- [x] Test: ADVISOR not burden when assigned as opener
- [x] Test: ADVISOR is burden when GENERAL is only opener needed
- [x] Test: Mid-value pieces marked as burden correctly
- [x] Test: Reserve pieces preserved (1-2 weak pieces)
- [x] Test: Opener timing based on hand size
- [x] Test: Plan formation only on turn 1
- [x] Test: Field strength affects combo viability

#### Task 7.2: Integration Testing ✅
- [x] Run existing test suite - all must pass
- [x] Test overcapture avoidance still works
- [x] Test decision speed remains <100ms
- [x] Play test games to verify no breaks

## Rollback Plan

If issues arise:
1. The changes are modular - each phase can be rolled back independently
2. Git commit after each phase completion
3. Existing `choose_best_play()` fallback remains intact
4. All new functions are additions, not replacements

## Success Metrics ✅ ALL ACHIEVED

- [x] Burden classification matches between phases
- [x] High-value pieces can be burden when appropriate
- [x] Opener play timing appears natural (not always same turn)
- [x] Target achievement rate improves or stays same
- [x] No game-breaking bugs introduced

## Implementation Order

1. **Start with Phase 1-2**: Data structures and imports (low risk)
2. **Test thoroughly**
3. **Implement Phase 3-4**: Plan formation and evaluation
4. **Test with logging** to verify correct behavior
5. **Implement Phase 5-6**: Execution logic
6. **Full integration testing**

## Notes

- Each checkbox represents ~15-30 minutes of work
- Total estimated time: 8-10 hours
- Can be implemented incrementally
- Each phase can be tested independently