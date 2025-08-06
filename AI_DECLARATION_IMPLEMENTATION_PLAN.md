# AI Declaration Implementation Plan - Full Strategic System

## Overview
This plan details the implementation of ALL strategic features from the AI Declaration Strategy guide, transforming the current simple hand evaluation into a sophisticated context-aware system.

## Implementation Phases

### Phase 1: Fix Existing Bugs (Prerequisites)
These must be done before adding new features.

#### Task 1.1: Remove Starter Bonus
- [ ] **File**: `backend/engine/ai.py`, Line ~81
- [ ] **Action**: Delete the `if is_first_player: score += 1` block
- [ ] **Test**: Verify same hand produces same declaration regardless of position

#### Task 1.2: Fix Declaration Range Bug  
- [ ] **File**: `backend/engine/ai.py`, Line 89
- [ ] **Action**: Change `min(max(score, 1), 7)` to `min(max(score, 0), 8)`
- [ ] **Test**: Verify AI can declare 0 and 8 when appropriate

### Phase 2: Core Infrastructure
Build the foundation for strategic features.

#### Task 2.1: Create Strategy Context Class
- [ ] **Create**: New class `DeclarationContext` to hold all strategic data
- [ ] **Include**: 
  - `position_in_order: int`
  - `previous_declarations: List[int]`
  - `is_starter: bool`
  - `pile_room: int`
  - `field_strength: str` (weak/normal/strong)
- [ ] **Location**: Add to `backend/engine/ai.py` or new file

#### Task 2.2: Calculate Pile Room
- [ ] **Add function**: `calculate_pile_room(previous_declarations: List[int]) -> int`
- [ ] **Logic**: `return max(0, 8 - sum(previous_declarations))`
- [ ] **Test**: Unit test with various declaration combinations

#### Task 2.3: Assess Field Strength
- [ ] **Add function**: `assess_field_strength(previous_declarations: List[int]) -> str`
- [ ] **Logic**:
  ```python
  avg = sum(previous_declarations) / len(previous_declarations) if previous_declarations else 0
  if avg <= 1.0: return "weak"
  elif avg >= 3.5: return "strong"
  else: return "normal"
  ```
- [ ] **Test**: Verify correct categorization

### Phase 3: Strategic Analysis Functions

#### Task 3.1: Analyze Declaration Patterns
- [ ] **Add function**: `analyze_opponent_patterns(previous_declarations: List[int]) -> Dict`
- [ ] **Return**:
  - `has_combos: List[bool]` - which players likely have combos
  - `combo_opportunity: bool` - whether opponents might play 3+ pieces
- [ ] **Logic**: Players declaring 0-1 have NO combos, 4+ have strong combos

#### Task 3.2: Evaluate Opener Reliability
- [ ] **Add function**: `evaluate_opener_reliability(piece: Piece, field_strength: str) -> float`
- [ ] **Logic**:
  - GENERAL (13-14): Always 1.0
  - ADVISOR (11-12): 1.0 if weak field, 0.7 if strong
  - Others: 0.0
- [ ] **Test**: Various pieces in different field strengths

#### Task 3.3: Check GENERAL_RED Game Changer
- [ ] **Add function**: `has_general_red(hand: List[Piece]) -> bool`
- [ ] **Logic**: Check if any piece is GENERAL with 14 points
- [ ] **Impact**: If true AND weak field, enable combo plays

#### Task 3.4: Analyze Combo Opportunities
- [ ] **Add function**: `analyze_combo_opportunity(combos: List, context: DeclarationContext, has_opener: bool) -> List`
- [ ] **Logic**:
  - If starter OR has_opener: combos are playable
  - If opponents declared 0-2: 0% chance for combos
  - If opponents declared 3+: possible but uncertain
- [ ] **Return**: List of actually playable combos

### Phase 4: Core Declaration Algorithm Rewrite

#### Task 4.1: Refactor Main Declaration Logic
- [ ] **Modify**: `choose_declare()` function structure
- [ ] **IMPORTANT**: Maintain exact function signature for backward compatibility:
  ```python
  def choose_declare(
      hand,
      is_first_player: bool,
      position_in_order: int,
      previous_declarations: list[int],
      must_declare_nonzero: bool,
      verbose: bool = True,
  ) -> int:
  ```
- [ ] **New flow**:
  1. Create DeclarationContext
  2. Calculate pile room
  3. Assess field strength
  4. Analyze patterns
  5. Calculate base score
  6. Apply strategic adjustments
  7. Apply constraints

#### Task 4.2: Implement Pile Room Constraint
- [ ] **Add check**: Before counting any combo, verify `pile_room >= combo_size`
- [ ] **Logic**: If STRAIGHT needs 3 piles but room = 2, don't count it
- [ ] **Priority**: If limited room, prefer openers over combos

#### Task 4.3: Implement Starter vs Non-Starter Logic
- [ ] **For starter**: Count all combos at full value
- [ ] **For non-starter**: 
  - Check if have opener (especially GENERAL_RED)
  - Apply combo opportunity analysis
  - Reduce combo value if no opportunity

#### Task 4.4: Implement GENERAL_RED Special Logic
- [ ] **Detection**: `if has_general_red(hand) and field_strength == "weak"`
- [ ] **Effect**: Treat all combos as playable (like being starter)
- [ ] **Example**: Enable 5-pile declarations with GENERAL_RED + FOUR_OF_A_KIND

### Phase 5: Advanced Strategic Features

#### Task 5.1: Context-Aware Opener Valuation
- [ ] **Logic**: 
  ```python
  opener_value = 0
  for piece in hand:
      if piece.point >= 11:
          reliability = evaluate_opener_reliability(piece, field_strength)
          opener_value += reliability
  ```
- [ ] **Test**: Various hands in different contexts

#### Task 5.2: Combo Viability Filtering
- [ ] **Add function**: `filter_viable_combos(combos: List, context: DeclarationContext) -> List`
- [ ] **Consider**:
  - Pile room constraints
  - Combo opportunity from opponents
  - Combo strength (weak STRAIGHTs need special handling)
- [ ] **Test**: Edge cases like no room, no opportunity

#### Task 5.3: Last Player Special Rules
- [ ] **Add check**: If `position_in_order == 3`
- [ ] **Calculate**: What declaration would make sum = 8
- [ ] **Implement**: Alternative selection logic if ideal value is forbidden

### Phase 6: Integration and Testing

#### Task 6.1: Update Debug Output
- [ ] **Add to verbose output**:
  - Pile room calculation
  - Field strength assessment
  - Combo opportunity analysis
  - GENERAL_RED detection
  - Strategic adjustments applied

#### Task 6.2: Create Comprehensive Test Suite
- [ ] **Test scenarios**:
  - [ ] Starter with combos (should declare high)
  - [ ] Non-starter with combos, no opener (should declare low)
  - [ ] GENERAL_RED in weak field (should enable combos)
  - [ ] Strong hand with pile room = 0 (must declare 0)
  - [ ] Last player forbidden value handling
  - [ ] All 18 examples from documentation

#### Task 6.3: Performance Testing
- [ ] **Measure**: Declaration calculation time
- [ ] **Target**: < 100ms per decision
- [ ] **Optimize**: If needed, cache repeated calculations

### Phase 7: Final Validation

#### Task 7.1: Validate Against Examples
- [ ] Test all 18 examples from AI_DECLARATION_EXAMPLES.md
- [ ] Compare AI output with expected declarations
- [ ] Document any discrepancies

#### Task 7.2: Regression Testing
- [ ] Ensure no crashes or errors
- [ ] Verify game rules still enforced (sum ≠ 8, etc.)
- [ ] Check edge cases (empty previous_declarations, etc.)

#### Task 7.3: User Acceptance Testing
- [ ] Play 20+ games with new AI
- [ ] Observe declaration patterns
- [ ] Verify AI makes contextually appropriate decisions

## Code Architecture Overview

```
choose_declare()
├── Create DeclarationContext
├── Calculate Strategic Factors
│   ├── pile_room = calculate_pile_room()
│   ├── field_strength = assess_field_strength()
│   └── patterns = analyze_opponent_patterns()
├── Evaluate Hand
│   ├── combos = find_all_valid_combos()
│   ├── viable_combos = filter_viable_combos()
│   ├── opener_score = evaluate_openers()
│   └── has_game_changer = has_general_red()
├── Calculate Base Score
│   ├── Add piles from viable combos
│   └── Add reliable opener piles
├── Apply Strategic Adjustments
│   ├── GENERAL_RED bonus
│   ├── Position adjustments
│   └── Field strength modifiers
├── Apply Constraints
│   ├── Pile room ceiling
│   ├── Game rules (sum ≠ 8)
│   └── Valid range [0-8]
└── Return final declaration
```

## Priority Order

1. **Critical**: Fix existing bugs (Phase 1)
2. **High**: Implement pile room constraint (Phase 2-4)
3. **High**: Implement GENERAL_RED game changer (Phase 4)
4. **Medium**: Add field strength and pattern analysis (Phase 3)
5. **Medium**: Context-aware adjustments (Phase 5)
6. **Low**: Enhanced debug output (Phase 6)

## Estimated Timeline

- Phase 1: 30 minutes (bug fixes)
- Phase 2: 2 hours (infrastructure)
- Phase 3: 3 hours (analysis functions)
- Phase 4: 4 hours (core algorithm)
- Phase 5: 3 hours (advanced features)
- Phase 6: 2 hours (testing)
- Phase 7: 2 hours (validation)

**Total**: ~16 hours of implementation

## Success Criteria

1. AI respects pile room constraints absolutely
2. AI recognizes when combos are unplayable
3. AI leverages GENERAL_RED appropriately
4. AI declarations vary based on context
5. All 18 test examples produce expected results
6. No performance degradation
7. Code remains maintainable and well-documented

## Dependencies and Integration Points

### Code Dependencies
- **`backend/engine/ai.py`**: Main implementation file
- **`backend/engine/rules.py`**: For `is_valid_play()` and `get_play_type()`
- **`backend/engine/piece.py`**: Piece class definition
- **`backend/engine/async_bot_strategy.py`**: Async wrapper (no changes needed)
- **`backend/engine/bot_manager.py`**: Bot management (no changes needed)

### Key Risks and Mitigations

1. **Risk**: Breaking backward compatibility
   - **Mitigation**: Maintain exact function signature
   - **Test**: Run existing bot games before/after changes

2. **Risk**: Performance degradation from complex calculations
   - **Mitigation**: Profile code, optimize hot paths
   - **Target**: Keep decision time < 100ms

3. **Risk**: Over-complexity making AI unpredictable
   - **Mitigation**: Extensive logging in verbose mode
   - **Solution**: Clear debug output showing decision factors

4. **Risk**: Edge cases causing crashes
   - **Mitigation**: Defensive programming, handle empty lists
   - **Test**: Comprehensive edge case testing

## Alternative Approach (If Full Implementation Too Complex)

If the full strategic implementation proves too complex or risky, consider a phased approach:

1. **Phase A**: Just add pile room constraint (biggest impact)
2. **Phase B**: Add GENERAL_RED special handling
3. **Phase C**: Add field strength assessment
4. **Phase D**: Full strategic implementation

This allows incremental improvements while maintaining stability.