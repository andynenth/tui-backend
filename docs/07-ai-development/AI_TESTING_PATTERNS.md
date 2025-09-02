# AI Testing Patterns Guide

## Overview

The AI testing framework provides comprehensive tools for validating AI behavior, ensuring consistency, and preventing regressions. The system uses a modular approach with reusable components and specific test scenarios.

## Architecture

```
┌─────────────────────┐
│ Test Orchestration  │
│ run_all_regression  │
└─────────┬───────────┘
          │
    ┌─────▼─────────┐
    │ Test Modules  │
    ├───────────────┤
    │ • Combo tests │
    │ • Decision    │
    │ • Regression  │
    └─────┬─────────┘
          │
    ┌─────▼──────────────┐
    │ Decision Framework  │
    │ AIDecisionTester   │
    └─────┬──────────────┘
          │
    ┌─────▼─────────┐
    │ Game Engine   │
    │ Integration   │
    └───────────────┘
```

## Core Components

### 1. AI Decision Framework (`tests/ai_regression/ai_decision_framework.py`)

Reusable testing framework for AI decisions.

#### Key Features

```python
class AIDecisionTester:
    """Reusable tester for AI decision-making scenarios"""
    
    def create_hand_from_specs(self, piece_specs: List[Tuple[str, int]]) -> List[Piece]:
        """Create hands from specifications"""
        
    def create_context(self, bot_name: str, hand: List[Piece], ...) -> TurnPlayContext:
        """Create game contexts for testing"""
        
    def analyze_decision(self, context: TurnPlayContext) -> Dict:
        """Analyze AI decisions with detailed results"""
```

#### Creating Test Hands

```python
# Using piece specifications
tester = AIDecisionTester()
hand = tester.create_hand_from_specs([
    ("ADVISOR_RED", 2),      # 2 red advisors
    ("SOLDIER_BLACK", 3),    # 3 black soldiers
    ("ELEPHANT_BLACK", 1)    # 1 black elephant
])
```

#### Creating Test Contexts

```python
context = tester.create_context(
    bot_name="TestBot",
    hand=hand,
    declared=5,           # Bot declared 5 piles
    captured=2,           # Already captured 2 piles
    required_pieces=3,    # Must play 3 pieces
    turn_number=2,
    is_starter=False,
    player_states={
        "Player1": {"captured": 3, "declared": 4},
        "Player2": {"captured": 0, "declared": 2}
    }
)
```

### 2. Regression Test Suite

Located in `tests/ai_regression/`, each test file targets specific AI behaviors.

#### Test Categories

1. **Combo Tests**
   - `test_never_win_combo.py` - Never-win combo avoidance
   - `test_combo_preservation_fix.py` - Combo preservation logic
   - `test_combo_rank_priority.py` - Combo ranking decisions

2. **Decision Tests**
   - `test_opener_assignment_fix.py` - Opener piece assignment
   - `test_smart_opener_assignment.py` - Strategic opener use
   - `test_urgency_random_opener.py` - Urgency-based decisions

3. **Bug Fix Validations**
   - `test_object_comparison_fix.py` - Object comparison bugs
   - `test_zero_streak_fix.py` - Zero declaration streaks

### 3. Test Execution

#### Running All Tests

```bash
# Run complete regression suite
python tests/ai_regression/run_all_regression_tests.py

# Output:
# AI REGRESSION TEST SUITE
# Date: 2025-09-02 10:30:00
# ============================================================
# Found 8 test files:
# ✅ test_combo_preservation_fix.py
# ✅ test_combo_rank_priority.py
# ...
```

#### Running Individual Tests

```bash
# Run specific test
python tests/ai_regression/test_never_win_combo.py

# Run with pytest for more details
pytest tests/ai_regression/test_never_win_combo.py -v
```

## Testing Patterns

### 1. Never-Win Combo Testing

Tests that AI avoids combinations that can never win.

```python
def test_never_win_detection():
    """Test the never-win combo detection function"""
    
    # All-BLACK straight (never wins)
    black_straight = [
        Piece("CANNON_BLACK"),   # 3 points
        Piece("HORSE_BLACK"),    # 5 points
        Piece("CHARIOT_BLACK")   # 7 points
    ]
    assert is_never_win_combo("STRAIGHT", black_straight)
    
    # Mixed color straight (can win)
    mixed_straight = [
        Piece("CANNON_RED"),     # 4 points
        Piece("HORSE_BLACK"),    # 5 points
        Piece("CHARIOT_RED")     # 8 points
    ]
    assert not is_never_win_combo("STRAIGHT", mixed_straight)
```

### 2. Decision Validation Testing

Tests that validate AI makes correct strategic decisions.

```python
def test_responder_strategy():
    """Test responder decision making"""
    
    # Create scenario
    context = create_context(
        required_pieces=3,      # Must match starter
        is_starter=False,       # As responder
        captured=1,
        declared=4
    )
    
    # Get AI decision
    chosen = execute_responder_strategy(hand, context)
    
    # Validate decision
    assert len(chosen) == 3, "Must match required pieces"
    assert not is_never_win_combo(get_play_type(chosen), chosen)
```

### 3. Edge Case Testing

Tests for boundary conditions and special cases.

```python
def test_fallback_to_never_win():
    """Test fallback when only never-win combos available"""
    
    # Hand with ONLY never-win options
    hand = [
        Piece("CANNON_BLACK"),
        Piece("HORSE_BLACK"),
        Piece("CHARIOT_BLACK")
    ]
    
    context = create_context(required_pieces=3)
    chosen = choose_strategic_play(hand, context)
    
    # Should play the never-win combo when no choice
    assert len(chosen) == 3
    assert is_never_win_combo("STRAIGHT", chosen)
```

### 4. Performance Testing

Tests that validate AI performance characteristics.

```python
def test_decision_performance():
    """Test AI decision speed"""
    import time
    
    # Complex hand
    hand = create_large_hand(20)  # 20 pieces
    context = create_complex_context()
    
    start = time.time()
    decision = choose_strategic_play(hand, context)
    duration = time.time() - start
    
    assert duration < 0.1, f"Decision too slow: {duration}s"
```

## Test Data Patterns

### 1. Hand Creation Patterns

```python
# Pattern 1: Specific combo testing
combo_test_hand = [
    # Target combo
    Piece("ADVISOR_RED"), Piece("ADVISOR_RED"),
    # Alternatives
    Piece("CANNON_RED"), Piece("HORSE_RED"), Piece("CHARIOT_RED"),
    # Fillers
    Piece("SOLDIER_BLACK"), Piece("SOLDIER_RED")
]

# Pattern 2: Edge case testing
edge_case_hand = [
    # All same value
    Piece("CANNON_BLACK"), Piece("CANNON_BLACK"), 
    Piece("CANNON_RED"), Piece("CANNON_RED")
]

# Pattern 3: Comprehensive testing
full_test_hand = create_hand_from_specs([
    ("GENERAL_RED", 1),      # Highest value
    ("ADVISOR_RED", 2),      # Pairs
    ("ELEPHANT_BLACK", 2),   # Different pairs
    ("CHARIOT_RED", 1),      # Singles
    ("HORSE_BLACK", 1),
    ("CANNON_RED", 1),
    ("SOLDIER_BLACK", 2)     # Lowest value
])
```

### 2. Context Creation Patterns

```python
# Pattern 1: Urgency testing
high_urgency_context = create_context(
    declared=6,
    captured=1,    # Need 5 more
    turn_number=7  # Late game
)

# Pattern 2: Overcapture testing
overcapture_risk_context = create_context(
    declared=3,
    captured=2,    # Need only 1 more
    required_pieces=3  # Risk of winning 3
)

# Pattern 3: Complex game state
complex_context = create_context(
    player_states={
        "Bot1": {"captured": 4, "declared": 5},
        "Bot2": {"captured": 0, "declared": 0},  # Weak player
        "Bot3": {"captured": 7, "declared": 7},  # At target
        "Bot4": {"captured": 2, "declared": 6}
    }
)
```

## Writing New Tests

### Test Structure Template

```python
#!/usr/bin/env python3
"""Test [specific behavior being tested]

Tests:
1. [First test scenario]
2. [Second test scenario]
3. [Edge cases]
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.engine.piece import Piece
from backend.engine.ai_turn_strategy import [needed imports]
from tests.ai_regression.ai_decision_framework import AIDecisionTester

def test_main_behavior():
    """Test the primary behavior"""
    print("TEST 1: [Test Name]")
    print("=" * 60)
    
    # Setup
    tester = AIDecisionTester()
    hand = tester.create_hand_from_specs([...])
    context = tester.create_context(...)
    
    # Execute
    result = [function_under_test](hand, context)
    
    # Validate
    assert [condition], "[Error message]"
    print("✅ [Success message]")

def test_edge_cases():
    """Test edge cases and boundaries"""
    # Test implementation

if __name__ == "__main__":
    test_main_behavior()
    test_edge_cases()
    print("\n✅ All tests passed!")
```

### Best Practices

1. **Descriptive Names**: Use clear test names that describe what's being tested
2. **Isolated Tests**: Each test should be independent
3. **Clear Assertions**: Include meaningful error messages
4. **Visual Feedback**: Use ✅ and ❌ for clear results
5. **Documentation**: Comment complex test scenarios

## Continuous Integration

### GitHub Actions Integration

```yaml
- name: Run AI Regression Tests
  run: |
    cd ${{ github.workspace }}
    python tests/ai_regression/run_all_regression_tests.py
  timeout-minutes: 5
```

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Running AI regression tests..."
python tests/ai_regression/run_all_regression_tests.py
if [ $? -ne 0 ]; then
    echo "AI regression tests failed. Commit aborted."
    exit 1
fi
```

## Debugging Failed Tests

### 1. Enable Verbose Output

```python
# In test file
def analyze_decision(context, verbose=True):
    if verbose:
        print(f"Hand: {[str(p) for p in context.my_hand]}")
        print(f"Context: {context}")
        print(f"Decision: {result}")
```

### 2. Use AI Logger

```python
# Enable detailed logging
from backend.services.ai_logger import AILogger

ai_logger = AILogger(log_level='detailed')
result = choose_strategic_play(hand, context, ai_logger=ai_logger)
# Check logs/ai_debug/ for details
```

### 3. Reproduce in Debug Mode

```bash
# Create minimal reproduction
python backend/ai_debug_simple.py --games 1 --log-level detailed
```

## Common Test Scenarios

1. **Combo Preservation**: Test AI preserves strong combos
2. **Urgency Response**: Test appropriate urgency reactions
3. **Overcapture Avoidance**: Test pile management
4. **Edge Value Handling**: Test boundary conditions
5. **Performance Validation**: Test decision speed
6. **Regression Prevention**: Test fixed bugs don't reappear

## Future Enhancements

1. **Property-Based Testing**: Random scenario generation
2. **Mutation Testing**: Verify test effectiveness
3. **Visual Test Reports**: Graphical test results
4. **Benchmark Suite**: Performance regression detection
5. **AI vs AI Testing**: Strategy effectiveness validation