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

### Phase 1: Update Data Structures

#### Task 1.1: Extend StrategicPlan Dataclass
**File**: `backend/engine/ai_turn_strategy.py`
**Location**: Line 29

- [ ] Add field: `assigned_openers: List[Piece] = field(default_factory=list)`
- [ ] Add field: `assigned_combos: List[Tuple[str, List[Piece]]] = field(default_factory=list)`
- [ ] Add field: `reserve_pieces: List[Piece] = field(default_factory=list)`
- [ ] Add field: `burden_pieces: List[Piece] = field(default_factory=list)`
- [ ] Add field: `main_plan_size: int = 0`
- [ ] Add field: `plan_impossible: bool = False`
- [ ] Test: Verify dataclass instantiation still works

### Phase 2: Import Declaration Logic

#### Task 2.1: Add Imports from ai.py
**File**: `backend/engine/ai_turn_strategy.py`
**Location**: After line 6 (imports section)

- [ ] Add import: `from backend.engine.ai import assess_field_strength`
- [ ] Test: Verify import works without circular dependency

#### Task 2.2: Create Field Strength Adapter
**File**: `backend/engine/ai_turn_strategy.py`
**Location**: After `calculate_urgency()` function (around line 297)

- [ ] Create function: `get_field_strength_from_players(player_states: Dict[str, Dict]) -> str`
- [ ] Extract opponent declarations from player_states
- [ ] Call `assess_field_strength()` with opponent declarations
- [ ] Test: Verify returns "weak", "normal", or "strong"

### Phase 3: Add Plan Formation

#### Task 3.1: Create Combo Viability Function
**File**: `backend/engine/ai_turn_strategy.py`
**Location**: After field strength adapter

- [ ] Create function: `is_combo_viable(combo_type: str, pieces: List[Piece], field_strength: str) -> bool`
- [ ] Implement pair viability logic:
  - Weak field: pairs ≥12 points viable
  - Normal field: pairs ≥16 points viable  
  - Strong field: pairs ≥20 points viable
- [ ] THREE_OF_A_KIND and above always viable
- [ ] Test: Verify SOLDIER pair not viable, ELEPHANT pair viable in weak field

#### Task 3.2: Create Plan Formation Function
**File**: `backend/engine/ai_turn_strategy.py`
**Location**: After combo viability function

- [ ] Create function: `form_execution_plan(hand: List[Piece], context: TurnPlayContext, valid_combos: List[Tuple]) -> Dict`
- [ ] Check if `context.turn_number == 1` (only form plan on turn 1)
- [ ] Get field strength using adapter function
- [ ] Filter combos for viability using `is_combo_viable()`
- [ ] Assign openers based on target remaining:
  - 0-1 piles needed: 0 openers
  - 2-3 piles needed: 1 opener (strongest)
  - 4+ piles needed: 2 openers
- [ ] Assign viable combos to plan
- [ ] Reserve 1-2 weakest pieces (point ≤ 4)
- [ ] Calculate `main_plan_size`
- [ ] Everything else = burden pieces
- [ ] Test: Verify high-value pieces can be burden

### Phase 4: Update Hand Evaluation

#### Task 4.1: Modify evaluate_hand Function
**File**: `backend/engine/ai_turn_strategy.py`
**Location**: Lines 183-209

- [ ] Remove lines 264-265 (current burden logic)
- [ ] Add plan formation check:
  ```python
  if context.turn_number == 1 and not hasattr(plan, 'assigned_openers'):
      # Form initial plan
  ```
- [ ] Return categorized pieces based on plan assignments
- [ ] Test: Verify GENERAL not classified as burden when it's an opener

#### Task 4.2: Update generate_strategic_plan Function
**File**: `backend/engine/ai_turn_strategy.py`
**Location**: Lines 300-313

- [ ] Add plan formation on turn 1
- [ ] Store role assignments in StrategicPlan object
- [ ] Add check: `if key_piece_lost: plan.plan_impossible = True`
- [ ] Test: Verify plan persists across turns

### Phase 5: Update Execution Logic

#### Task 5.1: Add Opener Timing Logic
**File**: `backend/engine/ai_turn_strategy.py`
**Location**: In `execute_starter_strategy()` around line 346

- [ ] Add before opener logic:
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
- [ ] Import random at top of file
- [ ] Test: Verify opener plays randomly when hand size allows
- [ ] Test: Verify opener-only plans have different timing
- [ ] Test: Verify openers spread across round for opener-only plans

#### Task 5.2: Update Burden Disposal Logic
**File**: `backend/engine/ai_turn_strategy.py`
**Location**: Lines 357-363

- [ ] Replace current burden disposal with:
  ```python
  if plan.urgency_level in ["low", "medium"] and plan.burden_pieces:
      # Sort burden by value descending (dispose high value first)
      sorted_burden = sorted(plan.burden_pieces, key=lambda p: -p.point)
  ```
- [ ] Prioritize high-value burden disposal
- [ ] Test: Verify ADVISOR disposed before SOLDIER when both are burden

#### Task 5.3: Create Aggressive Capture Function
**File**: `backend/engine/ai_turn_strategy.py`
**Location**: After `execute_starter_strategy()`

- [ ] Create function: `execute_aggressive_capture(hand: List[Piece], required_count: int) -> List[Piece]`
- [ ] Logic: Play strongest possible combinations
- [ ] Use when `plan.plan_impossible == True`
- [ ] Test: Verify switches strategy when plan broken

### Phase 6: Integration Updates

#### Task 6.1: Update Main Decision Function
**File**: `backend/engine/ai_turn_strategy.py`
**Location**: Lines 86-116 in `choose_strategic_play()`

- [ ] Check for plan impossibility:
  ```python
  if plan.plan_impossible and plan.urgency_level != "none":
      result = execute_aggressive_capture(hand, context.required_piece_count)
  ```
- [ ] Test: Verify fallback activates correctly

### Phase 7: Testing

#### Task 7.1: Create Unit Tests
**File**: Create `tests/ai_turn_play/test_hand_evaluation_consistency.py`

- [ ] Test: ADVISOR not burden when assigned as opener
- [ ] Test: ADVISOR is burden when GENERAL is only opener needed
- [ ] Test: CANNON pieces marked as burden correctly
- [ ] Test: Reserve pieces preserved (1-2 weak pieces)
- [ ] Test: Opener timing based on hand size
- [ ] Test: Plan formation only on turn 1
- [ ] Test: Field strength affects combo viability

#### Task 7.2: Integration Testing
- [ ] Run existing test suite - all must pass
- [ ] Test overcapture avoidance still works
- [ ] Test decision speed remains <100ms
- [ ] Play test games to verify no breaks

## Rollback Plan

If issues arise:
1. The changes are modular - each phase can be rolled back independently
2. Git commit after each phase completion
3. Existing `choose_best_play()` fallback remains intact
4. All new functions are additions, not replacements

## Success Metrics

- [ ] Burden classification matches between phases
- [ ] High-value pieces can be burden when appropriate
- [ ] Opener play timing appears natural (not always same turn)
- [ ] Target achievement rate improves or stays same
- [ ] No game-breaking bugs introduced

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