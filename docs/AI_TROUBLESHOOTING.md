# AI Troubleshooting Guide

## Overview

This guide provides comprehensive troubleshooting procedures for AI-related issues in Liap Tui. It covers common bugs, diagnostic techniques, and fix strategies based on our extensive bug fix history.

## Quick Troubleshooting Flowchart

```
AI Behaving Incorrectly?
├─> Declaration Issues?
│   ├─> Declaring 0 with strong hand → Check opener threshold calculation
│   ├─> Violating zero streak rule → Check forbidden value logic
│   └─> Wrong declaration value → Check play list calculation
├─> Turn Play Issues?
│   ├─> Not disposing high pieces → Check disposal priority logic
│   ├─> Playing wrong combo → Check combo rank vs points
│   └─> Preserving wrong pieces → Check opener assignment
└─> Object Comparison Issues?
    ├─> Pieces not found → Check object vs kind comparison
    └─> Wrong piece selected → Check equality operators
```

## Common AI Bugs and Solutions

### 1. Zero Declaration with Strong Hand

**Symptoms**:
- Bot declares 0 despite having 2-3 openers (11+ point pieces)
- Occurs even when pile room available

**Root Cause**:
- Declaration calculation indented incorrectly
- Dynamic opener threshold too restrictive

**Diagnosis**:
```python
# Check declaration calculation location
# Should be OUTSIDE final room adjustment block
if pile_room <= 2:
    # Room adjustments
    pass
# Declaration MUST be here, not inside the if block
declaration = len(play_list)
```

**Fix**:
1. Ensure declaration calculation happens for all paths
2. Use fixed opener threshold of 11 points
3. Remove dynamic threshold based on pile room

**Test**:
```bash
python test_zero_declaration_strong_hand.py
```

### 2. Combo Preservation When Declaring Zero

**Symptoms**:
- Bot preserves pairs/combos despite declaring 0
- High-value pieces kept instead of disposed

**Root Cause**:
- Combos assigned to plan regardless of target_remaining
- Preservation logic not checking declaration value

**Diagnosis**:
```python
# Check combo assignment logic
if target_remaining > 0:  # This check was missing
    # Assign combos
else:
    # Don't preserve combos when declaring 0
```

**Fix**:
Only preserve combos if target_remaining > 0

**Test**:
```bash
python tests/ai_regression/test_combo_preservation_fix.py
```

### 3. Wrong Priority in Critical Urgency

**Symptoms**:
- Bot plays high single instead of combo when urgent
- Loses to lower-ranked combos

**Root Cause**:
- Critical urgency maximized points instead of combo rank
- Missing combo types in COMBO_TYPE_RANK

**Diagnosis**:
```python
# Check COMBO_TYPE_RANK completeness
COMBO_TYPE_RANK = {
    "SINGLE": 0,
    "PAIR": 1,
    "STRAIGHT": 2,
    # ... ensure all types listed
}

# Check urgency logic
if urgency == "critical":
    # Should prioritize by rank, not points
    sorted(combos, key=lambda x: COMBO_TYPE_RANK[x[0]], reverse=True)
```

**Fix**:
1. Add missing combo types to rank map
2. Sort by rank first, then points

**Test**:
```bash
python tests/ai_regression/test_combo_rank_priority.py
```

### 4. Object Comparison Failures

**Symptoms**:
- Disposal strategy finds no burden pieces
- Wrong pieces selected for play
- "Piece not in hand" errors

**Root Cause**:
- Using object identity (`in`) instead of value equality
- Different Piece objects for same logical piece

**Diagnosis**:
```python
# WRONG: Object comparison
burden_in_hand = [p for p in plan.burden_pieces if p in context.my_hand]

# RIGHT: Value comparison by kind
plan_burden_kinds = {p.kind for p in plan.burden_pieces}
burden_in_hand = [p for p in context.my_hand if p.kind in plan_burden_kinds]
```

**Fix**:
Compare pieces by `.kind` attribute, not object identity

**Test**:
```bash
python tests/ai_regression/test_object_comparison_fix.py
```

### 5. Zero Streak Rule Violations

**Symptoms**:
- Bot declares 0 despite must_declare_nonzero=True
- Game stuck with repeated zero declarations

**Root Cause**:
- Early returns bypass forbidden value checking
- `rebuild_play_list_avoiding_forbidden` returns empty

**Diagnosis**:
```python
# Check for early returns
if pile_room == 0:
    return 0  # WRONG: Bypasses forbidden check
    
# Should be:
if pile_room == 0:
    declaration = 0  # Set but continue
    
# Later...
if must_declare_nonzero and declaration == 0:
    declaration = 1  # Force non-zero
```

**Fix**:
Replace early returns with declaration assignment

**Test**:
```bash
python tests/ai_regression/test_zero_streak_fix.py
```

## Diagnostic Tools and Techniques

### 1. AI Debug Mode

Run games with detailed AI logging:

```bash
python ai_debug_simple.py --games 10 --speed fast --log-level detailed
```

Output includes:
- Hand composition
- Declaration reasoning
- Play selection logic
- Pile counting

### 2. Enable Verbose Mode

Most AI functions accept verbose parameter:

```python
declaration = choose_declare(
    hand=hand,
    is_first_player=False,
    position_in_order=2,
    previous_declarations=[3, 2],
    must_declare_nonzero=False,
    verbose=True  # Enables detailed output
)
```

### 3. Decision Framework Testing

Use the AIDecisionTester for isolated testing:

```python
from tests.ai_regression.ai_decision_framework import AIDecisionTester

tester = AIDecisionTester()
context = tester.create_context(
    bot_name="Test Bot",
    hand=test_hand,
    declared=3,
    captured=1,
    required_pieces=2
)
result = tester.analyze_decision(context)
```

### 4. Execution Tracing

Add strategic logging to trace execution:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# In AI code:
logger.debug(f"Declaration calculation: pile_room={pile_room}, play_list={len(play_list)}")
logger.debug(f"Forbidden check: must_declare_nonzero={must_declare_nonzero}, declaration={declaration}")
```

## Step-by-Step Debugging Process

### Step 1: Reproduce the Issue

1. Create minimal test case
2. Document exact game state
3. Record expected vs actual behavior

```python
# Example reproduction script
from backend.engine.piece import Piece
from backend.engine.ai import choose_declare

# Exact hand that shows bug
hand = [
    Piece("GENERAL_RED"),    # 14 pts
    Piece("ADVISOR_RED"),    # 12 pts
    Piece("ELEPHANT_BLACK"), # 9 pts
    # ... rest of hand
]

# Exact game conditions
result = choose_declare(
    hand=hand,
    is_first_player=False,
    position_in_order=2,
    previous_declarations=[3, 3],  # Specific scenario
    must_declare_nonzero=True,
    verbose=True
)

print(f"Expected: >= 1, Got: {result}")
```

### Step 2: Isolate the Problem

1. Identify which function has the bug
2. Add logging before/after suspicious code
3. Check intermediate values

```python
# Add debugging output
print(f"DEBUG: Before forbidden check - declaration={declaration}")
print(f"DEBUG: Forbidden values={forbidden_values}")
print(f"DEBUG: Must declare nonzero={must_declare_nonzero}")
```

### Step 3: Trace Root Cause

Common root causes:
- Logic errors (wrong conditions)
- Ordering issues (operations in wrong sequence)
- Type issues (object vs value comparison)
- Edge cases (boundary conditions)

### Step 4: Develop Fix

1. Make minimal change to fix issue
2. Preserve all other functionality
3. Add comments explaining fix

```python
# FIX: Only preserve combos if we have targets
# Previous code assigned combos regardless of declaration
if target_remaining > 0:  # Added this condition
    viable_combos = self._filter_viable_combos(all_combos)
```

### Step 5: Verify Fix

1. Run original failing test - should pass
2. Run all regression tests - should pass
3. Run integration tests - should pass

```bash
# Run specific test
python test_reproduction.py

# Run all regression tests
cd tests/ai_regression
python run_all_regression_tests.py

# Run integration test
python ai_debug_simple.py --games 100
```

### Step 6: Create Regression Test

1. Create test file in `tests/ai_regression/`
2. Document bug and fix
3. Add to `run_all_regression_tests.py`
4. Update `FIX_HISTORY.md`

## Common Patterns to Check

### Declaration Patterns

1. **Opener Counting**:
```python
# Check opener threshold
opener_threshold = 11  # Should be fixed at 11
openers = [p for p in hand if p.point >= opener_threshold]
```

2. **Forbidden Values**:
```python
# Check forbidden value handling
forbidden_values = []
if must_declare_nonzero:
    forbidden_values.append(0)
if is_last_player and current_sum + X == 8:
    forbidden_values.append(X)
```

3. **Play List Building**:
```python
# Ensure all paths set declaration
declaration = len(play_list)  # Must be outside conditionals
```

### Turn Play Patterns

1. **Combo Priority**:
```python
# Rank > Points
sorted_combos = sorted(combos, 
    key=lambda x: (COMBO_TYPE_RANK[x[0]], sum(p.point for p in x[1])),
    reverse=True
)
```

2. **Disposal Priority**:
```python
# When at target or declaring 0
priority = [
    burden_pieces,      # Lowest value non-strategic
    reserve_pieces,     # Mid-value singles
    opener_singles,     # High-value singles
    combo_pieces       # Only if necessary
]
```

3. **Object Comparison**:
```python
# Always compare by kind
hand_kinds = {p.kind for p in hand}
matching = [p for p in pieces if p.kind in hand_kinds]
```

## Performance Analysis

### AI Decision Timing

Expected performance:
- Declaration: < 10ms
- Simple turn play: < 20ms
- Complex turn play: < 50ms
- Full game simulation: < 500ms

### Memory Usage

- Hand analysis: ~1KB
- Combo generation: ~5KB
- Decision context: ~2KB
- Total per decision: < 10KB

### Optimization Opportunities

1. Cache combo calculations
2. Precompute piece thresholds
3. Use piece kind indexing
4. Minimize object creation

## Integration Testing

### Test Scenarios

1. **Full Game Simulation**:
```bash
python ai_debug_simple.py --games 1000 --detect-bugs
```

2. **Specific Scenarios**:
```python
# Test all bots declare 0
# Test weak hand redeals
# Test perfect declarations
# Test comeback victories
```

3. **Edge Cases**:
- All players same declaration
- No valid plays available
- Multiple forbidden values
- Extreme piece distributions

### Validation Metrics

Track across many games:
- Declaration accuracy
- Win rate by position
- Average game length
- Rule violation count

## Bug Prevention Strategies

### Code Review Checklist

- [ ] All paths set return value
- [ ] Object comparisons use .kind
- [ ] Forbidden values checked last
- [ ] Combo rank prioritized correctly
- [ ] Edge cases handled
- [ ] Verbose logging available

### Testing Requirements

Before committing AI changes:
1. Run all regression tests
2. Run 1000 game simulation
3. Check for rule violations
4. Verify performance metrics

### Documentation Standards

For each bug fix:
1. Document in FIX_HISTORY.md
2. Create regression test
3. Update relevant comments
4. Add to troubleshooting guide

## Quick Reference

### Common Commands

```bash
# Run specific regression test
python tests/ai_regression/test_[name].py

# Run all regression tests
cd tests/ai_regression && python run_all_regression_tests.py

# Debug specific scenario
python ai_debug_simple.py --log-level detailed

# Analyze AI patterns
python analyze_ai_logs.py logs/ai_debug/game_*.json
```

### Key Files

- `backend/engine/ai.py` - Declaration logic
- `backend/engine/ai_turn_strategy.py` - Turn play logic
- `tests/ai_regression/` - All regression tests
- `tests/ai_regression/FIX_HISTORY.md` - Complete fix history

### Debug Flags

- `verbose=True` - Enable detailed output
- `--log-level detailed` - Maximum logging
- `--detect-bugs` - Enable validation
- `--speed slow` - Easier to follow

## Conclusion

Effective AI troubleshooting requires:
1. Systematic reproduction
2. Evidence-based analysis
3. Minimal fixes
4. Comprehensive testing
5. Regression prevention

Always remember: "No assumptions allowed" - verify everything with actual execution.