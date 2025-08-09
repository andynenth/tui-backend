# AI Baseline Test Modification Plan

## Overview

This document outlines how to modify the existing baseline tests (`tests/ai_declaration/test_baseline.py`) to be compatible with the new AI declaration structure while ensuring the tests validate the correct behavior according to the new logic.

## Key Changes in New Structure

### 1. Different Logic for Starters vs Non-Starters

**Old Structure**: Similar logic for both starters and non-starters
**New Structure**:
- **Starters**: Find combos first → then individual pieces
- **Non-starters**: Find ONE opener → then combos → then more pieces → fit to pile room

### 2. Strong Combo Definition

**Old Structure**: Predefined combo types list
**New Structure**: Combos where average piece value > HORSE_RED (6 points)

### 3. Explicit Play List Tracking

**Old Structure**: Implicit counting and overlap handling
**New Structure**: Explicit play list with piece removal to avoid overlap

### 4. Individual Piece Thresholds

**Old Structure**: Fixed opener threshold (11+ points)
**New Structure**: Dynamic thresholds based on pile room (using `get_piece_threshold()`)

## Expected Value Changes

Based on the new logic, some test scenarios will have different expected values:

### Scenarios That Will Change

1. **baseline_01**: ADVISOR_RED + CHARIOT-HORSE-CANNON straight + SOLDIER pairs
   - **Old**: 4 (1 opener + 3-piece straight)
   - **New**: 4 (same, but starter finds straight first)

2. **baseline_04**: No opener, CHARIOT-HORSE-CANNON straight + SOLDIER pairs
   - **Old**: 3 (straight only)
   - **New**: 5 (straight + SOLDIER pair, starters find all strong combos)

3. **baseline_05**: Same hand but non-starter in weak field
   - **Old**: 1 (some combo opportunity)
   - **New**: 0 (no opener found, non-starter declares 0)

4. **baseline_07**: GENERAL_RED + ADVISOR_BLACK + high pieces
   - **Old**: 2 (both openers)
   - **New**: 2 (same, individual pieces meet thresholds)

5. **baseline_09**: Weak hand (ELEPHANT pairs) as starter
   - **Old**: 1 (weak starter advantage)
   - **New**: 2 (ELEPHANT pair is strong combo, avg > 6)

6. **baseline_11**: 5 SOLDIERs + CHARIOT-HORSE-CANNON
   - **Old**: 8 (5 + 3)
   - **New**: 5 (FIVE_OF_A_KIND only, straight not strong enough)

7. **baseline_12**: Same hand, non-starter after [5]
   - **Old**: 0 (no control)
   - **New**: 0 (no opener, non-starter declares 0)

8. **baseline_15**: Double THREE_OF_A_KIND (SOLDIER×3 + SOLDIER×3)
   - **Old**: 6 (both three-of-a-kinds)
   - **New**: 3 (only one THREE_OF_A_KIND, avg value too low for both)

9. **baseline_17**: GENERAL_RED + SOLDIER×4 + straight
   - **Old**: 8 (transforms strategy)
   - **New**: 4 (1 opener + weak straight not counted)

## Test File Modifications

### 1. Create New Test File

```python
# tests/ai_declaration/test_baseline_v2.py
```

### 2. Import New Declaration Function

```python
from backend.engine.ai import choose_declare_strategic_v2  # New function
```

### 3. Updated Test Scenarios

```python
def get_baseline_v2_scenarios():
    """Get baseline test scenarios updated for new AI logic."""
    
    baseline_v2_tests = [
        # Strong hands with opener
        ("baseline_01", "[ADVISOR_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK]",
         0, [], 4, "Strong Hand with Opener (As Starter)", True, "Starter finds straight first, then opener"),
        
        ("baseline_02", "[ADVISOR_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK]",
         2, [0, 1], 1, "Same Hand, Weak Field", False, "Non-starter finds opener, limited by pile room"),
        
        ("baseline_03", "[ADVISOR_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK]",
         2, [5, 4], 1, "Same Hand, Strong Field (No Room)", False, "Pile room = 1, only opener counts"),
        
        # Good combos without opener
        ("baseline_04", "[CHARIOT_RED, HORSE_RED, CANNON_RED, ELEPHANT_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK]",
         0, [], 5, "Good Combos, No Opener (Starter)", True, "Starter finds straight + SOLDIER pair"),
        
        ("baseline_05", "[CHARIOT_RED, HORSE_RED, CANNON_RED, ELEPHANT_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK]",
         2, [0, 1], 0, "Good Combos, No Opener (Weak Field)", False, "Non-starter with no opener declares 0"),
        
        # ... continue with updated expected values
    ]
```

### 4. Test Execution Modifications

```python
def execute_test_scenario_v2(scenario: TestScenario, verbose: bool = False) -> TestResult:
    """Execute test scenario using new v2 declaration logic."""
    hand = parse_hand(scenario.hand_str)
    
    # Use new v2 function
    actual = choose_declare_strategic_v2(
        hand=hand,
        is_first_player=scenario.is_starter,
        position_in_order=scenario.position,
        previous_declarations=scenario.previous_decl,
        must_declare_nonzero=False,
        verbose=verbose
    )
    
    passed = (actual == scenario.expected)
    
    return TestResult(
        scenario=scenario,
        actual_result=actual,
        passed=passed
    )
```

## Validation Strategy

### 1. Side-by-Side Comparison

Run both old and new tests to understand differences:

```python
def compare_v1_v2_results():
    """Compare results between v1 and v2 declaration logic."""
    v1_scenarios = get_baseline_scenarios()
    v2_scenarios = get_baseline_v2_scenarios()
    
    for v1, v2 in zip(v1_scenarios, v2_scenarios):
        v1_result = execute_test_scenario(v1)
        v2_result = execute_test_scenario_v2(v2)
        
        if v1_result.actual_result != v2_result.actual_result:
            print(f"{v1.scenario_id}: v1={v1_result.actual_result}, v2={v2_result.actual_result}")
```

### 2. Explanation Mode

Add detailed logging to understand why values changed:

```python
def explain_declaration_v2(scenario: TestScenario):
    """Explain the v2 declaration decision step by step."""
    print(f"\n{'='*60}")
    print(f"Explaining {scenario.scenario_id}")
    print(f"{'='*60}")
    
    result = execute_test_scenario_v2(scenario, verbose=True)
    # Verbose mode will show play list construction
```

## Migration Steps

### Phase 1: Create Parallel Tests
1. Copy test_baseline.py to test_baseline_v2.py
2. Update imports to use v2 function
3. Update expected values based on new logic
4. Keep both test files running

### Phase 2: Validate Logic
1. Run both test suites
2. Document all differences
3. Verify each difference is intentional
4. Add explanatory comments

### Phase 3: Testing & Validation
1. Run both test suites locally
2. Compare results and verify improvements
3. Test with actual game scenarios
4. Switch to v2 once validated

### Phase 4: Cleanup
1. Mark v1 tests as deprecated
2. Move v2 tests to primary location
3. Archive v1 tests for reference
4. Update documentation

## Test Categories Affected

### High Impact (Major Changes)
- Starter combo detection (find combos first)
- Non-starter with no opener (declare 0)
- Strong combo definition (avg > 6)

### Medium Impact (Some Changes)
- Pile room constraints (dynamic thresholds)
- Combo overlap handling (explicit removal)
- Individual piece evaluation

### Low Impact (Minor/No Changes)
- Forbidden value handling
- Field strength assessment
- Last player constraints

## Success Criteria

1. **All Tests Pass**: 100% pass rate with v2 logic
2. **Clear Documentation**: Each changed value is explained
3. **No Regressions**: Bot performance improves or stays same
4. **Maintainability**: Tests are clear and easy to update

## Timeline

- **Week 1**: Create v2 test file and update values
- **Week 2**: Validate all changes and document
- **Week 3**: Run parallel testing in staging
- **Week 4**: Complete migration to v2