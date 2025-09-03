# AI Testing Patterns and Regression Framework

## Overview

This document describes the comprehensive testing patterns and regression framework used to ensure AI reliability in the Liap Tui game. Our approach emphasizes evidence-based testing, regression prevention, and continuous validation of AI behavior.

## Core Testing Philosophy

### Evidence-Based Testing
- **No Assumptions**: Every AI behavior must be validated with actual execution traces
- **Reproducible Scenarios**: All bugs must be reproducible with specific test cases
- **Measurable Outcomes**: Test success is determined by concrete, verifiable results

### Regression Prevention
- **Fix History Tracking**: Every bug fix is documented in `tests/ai_regression/FIX_HISTORY.md`
- **Regression Test Creation**: Each fix gets a corresponding regression test
- **Continuous Validation**: All regression tests run before any AI changes

## Testing Framework Architecture

### AIDecisionTester Framework

The core testing framework provides reusable components for AI scenario testing:

```python
from tests.ai_regression.ai_decision_framework import AIDecisionTester

class AIDecisionTester:
    """Reusable tester for AI decision-making scenarios"""
    
    def create_hand_from_specs(self, piece_specs: List[Tuple[str, int]]) -> List[Piece]:
        """Create a hand from piece specifications"""
        
    def create_context(self, bot_name: str, hand: List[Piece], 
                      declared: int, captured: int, required_pieces: int) -> TurnPlayContext:
        """Create a game context for testing"""
        
    def analyze_decision(self, context: TurnPlayContext) -> Dict:
        """Analyze AI decision for given context"""
```

### Test Organization

```
tests/
├── ai_regression/          # Regression tests for fixed bugs
│   ├── conftest.py        # Shared fixtures
│   ├── ai_decision_framework.py
│   ├── run_all_regression_tests.py
│   ├── FIX_HISTORY.md     # Complete fix documentation
│   └── test_*.py          # Individual regression tests
├── ai_debug/              # Debug and analysis tools
└── ai_declaration/        # Declaration strategy tests
```

## Common Testing Patterns

### 1. Declaration Testing Pattern

Tests AI declaration logic under various constraints:

```python
def test_zero_streak_declaration():
    """Test bot respects zero streak rule"""
    
    # Create scenario with zero streak
    hand = create_weak_hand()
    declaration = choose_declare(
        hand=hand,
        position_in_order=3,
        previous_declarations=[3, 3, 2],
        must_declare_nonzero=True,  # Zero streak active
        verbose=True
    )
    
    assert declaration >= 1, "Bot must declare at least 1 with zero streak"
```

### 2. Turn Play Testing Pattern

Tests AI turn play decisions:

```python
def test_combo_disposal_when_declaring_zero():
    """Test bot disposes combos when declaring 0"""
    
    # Create context with bot declaring 0
    context = tester.create_context(
        bot_name="Bot 3",
        hand=hand_with_combo,
        declared=0,  # Key: declaring 0
        captured=0,
        required_pieces=4
    )
    
    # Analyze decision
    result = tester.analyze_decision(context)
    chosen_pieces = result['chosen_play']
    
    # Verify combo pieces are disposed
    assert any(p.kind == "ADVISOR_RED" for p in chosen_pieces)
```

### 3. Edge Case Testing Pattern

Tests boundary conditions and special scenarios:

```python
def test_last_player_forbidden_sum():
    """Test last player handles forbidden sum + zero streak"""
    
    # Previous declarations sum to 7
    # Bot has zero streak (can't declare 0)
    # Bot is last player (can't make sum 8)
    # Therefore must declare >= 2
    
    declaration = choose_declare(
        hand=good_hand,
        position_in_order=3,  # Last player
        previous_declarations=[3, 2, 2],  # Sum = 7
        must_declare_nonzero=True,
        verbose=True
    )
    
    assert declaration >= 2, "Must avoid both 0 and 1"
```

## Regression Test Categories

### 1. Combo Management Tests

**Pattern**: Verify combo preservation/disposal logic

**Tests**:
- `test_combo_preservation_fix.py` - Combos disposed when declaring 0
- `test_combo_rank_priority.py` - Combo rank beats point value

### 2. Declaration Strategy Tests

**Pattern**: Verify declaration calculation accuracy

**Tests**:
- `test_zero_streak_fix.py` - Zero streak rule enforcement
- `test_opener_assignment_fix.py` - Opener scaling with declaration
- `test_smart_opener_assignment.py` - Combo-aware opener assignment

### 3. Object Comparison Tests

**Pattern**: Verify proper object equality handling

**Tests**:
- `test_object_comparison_fix.py` - Piece comparison by kind not identity

### 4. Urgency and Strategy Tests

**Pattern**: Verify strategic decision-making

**Tests**:
- `test_urgency_random_opener.py` - Random play when not urgent

## Running Regression Tests

### Full Test Suite

```bash
cd tests/ai_regression
source ../../venv/bin/activate
python run_all_regression_tests.py
```

### Individual Test

```bash
python test_zero_streak_fix.py
```

### Test Output Format

```
AI REGRESSION TEST SUITE
Date: 2025-08-29 10:30:45
============================================================
Found 7 test files:
  - test_combo_preservation_fix.py
  - test_combo_rank_priority.py
  - test_object_comparison_fix.py
  ...

============================================================
Running: test_zero_streak_fix.py
============================================================
Running zero streak declaration fix tests...
✅ Test passed: Bot correctly declared 1 (>= 1) with no pile room
✅ Test passed: Bot correctly declared 1 (>= 1) with no opener
✅ Test passed: Bot correctly declared 2 (avoiding both 0 and 1)
✅ All zero streak tests passed!

============================================================
REGRESSION TEST SUMMARY
============================================================
✅ PASSED: test_zero_streak_fix.py
✅ PASSED: test_combo_preservation_fix.py
...

Total: 7/7 tests passed
```

## Creating New Regression Tests

### Step 1: Reproduce the Bug

Create a minimal reproduction scenario:

```python
# Reproduce exact game state that triggers bug
hand = [Piece("ADVISOR_RED"), Piece("ADVISOR_RED"), ...]
context = create_test_context(declared=0, captured=0, ...)
```

### Step 2: Write the Test

Follow the standard pattern:

```python
#!/usr/bin/env python3
"""
Regression test for [BUG DESCRIPTION]

Bug: [What went wrong]
Root Cause: [Why it happened]
Fix: [How it was fixed]
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.engine.piece import Piece
from backend.engine.ai import choose_declare
# Import other needed modules

def test_specific_scenario():
    """Test that [expected behavior]"""
    
    # Setup
    # ...
    
    # Execute
    result = ai_function_under_test(...)
    
    # Verify
    assert result == expected, f"Expected {expected}, got {result}"
    print(f"✅ Test passed: {description}")
    return True

if __name__ == "__main__":
    print(f"Running {test_name} tests...")
    print("=" * 60)
    
    success = True
    try:
        test_specific_scenario()
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        success = False
        
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
        sys.exit(1)
```

### Step 3: Document in FIX_HISTORY.md

Add entry with:
- Date
- Bug description
- Root cause analysis
- Fix implementation
- Test file reference
- Impact assessment

## Test Data Patterns

### Creating Test Hands

```python
# Pattern 1: Specific piece composition
hand_specs = [
    ("ADVISOR_RED", 2),      # Pair
    ("SOLDIER_BLACK", 3),    # For straight
    ("CANNON_BLACK", 1),
    ("HORSE_RED", 1),
]

# Pattern 2: Weak hand (no openers)
weak_hand = [
    Piece("SOLDIER_RED"),    # 2 pts
    Piece("SOLDIER_BLACK"),  # 1 pts
    Piece("CANNON_BLACK"),   # 3 pts
    ...  # All < 11 points
]

# Pattern 3: Strong hand (multiple openers)
strong_hand = [
    Piece("GENERAL_RED"),    # 14 pts
    Piece("ADVISOR_RED"),    # 12 pts
    Piece("ELEPHANT_RED"),   # 10 pts
    ...
]
```

### Creating Test Contexts

```python
# Pattern 1: Specific game state
context = TurnPlayContext(
    my_name="Bot 1",
    my_hand=hand,
    my_captured=2,
    my_declared=5,
    required_piece_count=3,
    turn_number=2,
    am_i_starter=False,
    current_plays=[],
    player_states={
        "Player1": {"captured": 0, "declared": 7},
        "Player2": {"captured": 3, "declared": 3},
        ...
    }
)

# Pattern 2: Edge case scenarios
# Zero declaration context
zero_context = create_context(declared=0, captured=0, ...)

# At-target context  
at_target_context = create_context(declared=3, captured=3, ...)

# Critical urgency context
urgent_context = create_context(
    declared=4, 
    captured=1,
    turn_number=3,  # Late game
    pieces_per_player=3  # Few pieces left
)
```

## Debugging Test Failures

### Enable Verbose Output

Most AI functions accept `verbose=True`:

```python
result = choose_declare(
    hand=test_hand,
    verbose=True  # Shows decision reasoning
)
```

### Add Diagnostic Output

```python
def analyze_decision(self, context, show_plan_details=True):
    # Shows execution plan formation
    if show_plan_details:
        print(f"  - Assigned combos: {results['assigned_combos']}")
        for combo_type, pieces in plan['assigned_combos']:
            piece_str = "+".join([f"{p.kind}({p.point})" for p in pieces])
            print(f"    - {combo_type}: {piece_str}")
```

### Trace Execution Flow

Add strategic print statements:

```python
print(f"DEBUG: Urgency={urgency}, Risk={risk_level}")
print(f"DEBUG: Available combos: {len(valid_combos)}")
print(f"DEBUG: Chosen play: {chosen_pieces}")
```

## Performance Considerations

### Test Execution Time

- Individual test: < 1 second
- Full suite: < 30 seconds
- Use subprocess timeout: 30 seconds per test

### Memory Usage

- Test framework is lightweight
- Each test creates minimal objects
- Garbage collection between tests

### Parallel Execution

Currently tests run sequentially to ensure:
- Consistent output ordering
- Easier debugging
- No resource conflicts

## Best Practices

### 1. Test Independence

Each test must be completely independent:
- No shared state
- No file dependencies
- No network calls

### 2. Clear Assertions

```python
# Good: Specific error message
assert declaration >= 1, f"Bot with zero streak must declare at least 1, got {declaration}"

# Bad: Generic assertion
assert declaration >= 1
```

### 3. Descriptive Names

```python
# Good: Describes scenario and expectation
def test_zero_declaration_with_strong_combo_disposal():

# Bad: Vague name
def test_ai_bug_fix():
```

### 4. Document Context

Always include:
- Bug description
- Root cause
- Fix approach
- Test rationale

### 5. Verify Fix Works

Before creating regression test:
1. Confirm bug exists in old code
2. Apply fix
3. Verify bug is resolved
4. Create test to prevent regression

## Integration with CI/CD

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run regression tests if AI files changed
if git diff --cached --name-only | grep -q "backend/engine/ai"; then
    echo "Running AI regression tests..."
    cd tests/ai_regression
    python run_all_regression_tests.py
    if [ $? -ne 0 ]; then
        echo "AI regression tests failed! Commit aborted."
        exit 1
    fi
fi
```

### GitHub Actions

```yaml
name: AI Regression Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    - name: Run AI regression tests
      run: |
        cd tests/ai_regression
        python run_all_regression_tests.py
```

## Future Enhancements

### 1. Property-Based Testing

Generate random valid game states and verify AI invariants:
- Never plays pieces not in hand
- Always respects game rules
- Declaration within valid range

### 2. Performance Benchmarking

Track AI decision time across versions:
- Declaration: < 10ms
- Turn play: < 50ms
- Complex scenarios: < 100ms

### 3. Statistical Validation

Verify AI behavior distributions:
- Win rates by position
- Declaration accuracy
- Combo utilization rates

### 4. Visual Test Reports

Generate HTML reports showing:
- Test coverage maps
- Decision trees
- Performance trends