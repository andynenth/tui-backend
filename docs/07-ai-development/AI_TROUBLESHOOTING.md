# AI Troubleshooting Guide

## Overview

This guide provides comprehensive troubleshooting strategies for AI-related issues in Liap Tui. It covers common bug patterns, diagnostic techniques, and proven fixes based on historical bug resolutions.

## Bug Detection System

### Automatic Bug Detection (`backend/services/ai_bug_detector.py`)

The system automatically detects common AI bugs during gameplay.

#### Bug Severity Levels

```python
class BugSeverity(Enum):
    LOW = "low"        # Minor suboptimal play
    MEDIUM = "medium"  # Clear mistakes
    HIGH = "high"      # Serious strategy flaws
    CRITICAL = "critical"  # Game-breaking bugs
```

#### Bug Report Structure

```python
@dataclass
class BugReport:
    bug_type: str           # Categorized bug identifier
    severity: BugSeverity   # Impact level
    player: str             # Affected bot
    phase: str              # Game phase (declaration/turn)
    description: str        # Human-readable description
    context: Dict           # Relevant game state
    suggested_fix: str      # Remediation advice
```

## Common Bug Patterns

### 1. Declaration Phase Bugs

#### Over-Aggressive Declaration
**Symptoms**: Bot declares high (6+) with weak hand  
**Detection**: 
```python
if final_declaration >= 6 and openers + combos < 3:
    # Bug detected
```
**Fix**: Validate hand strength before high declarations

#### Zero Declaration with Strong Hand
**Symptoms**: Bot declares 0 despite having openers  
**Detection**:
```python
if final_declaration == 0 and openers >= 2 and zero_streak < 2:
    # Bug detected
```
**Fix**: Check zero streak rule enforcement

#### Pile Room Violation
**Symptoms**: Declaration exceeds available pile room  
**Detection**:
```python
if final_declaration > pile_room:
    # Bug detected
```
**Fix**: Validate pile room calculation

### 2. Turn Play Bugs

#### Never-Win Combo Play
**Symptoms**: Bot plays combos that can never win  
**Examples**:
- All-BLACK straight (3+5+7 points minimum)
- SOLDIER_BLACK pairs (1+1=2 points minimum)

**Detection**:
```python
def is_never_win_combo(combo_type: str, pieces: List[Piece]) -> bool:
    if combo_type == "STRAIGHT":
        # Check if all pieces are BLACK (odd points)
        all_black = all(p.point % 2 == 1 for p in pieces)
        if all_black:
            points = sorted([p.point for p in pieces])
            if points[:3] == [3, 5, 7]:  # Minimum straight
                return True
```

**Fix**: Filter out never-win combos in responder strategy

#### Overcapture Risk
**Symptoms**: Bot wins too many piles exceeding declaration  
**Detection**: Monitor captured vs declared ratio  
**Fix**: Implement overcapture constraints

#### Wrong Piece Count
**Symptoms**: Bot plays wrong number of pieces  
**Detection**: Compare played vs required pieces  
**Fix**: Validate piece count before play

## Historical Bug Fixes

### Fix #1: Combo Preservation When Declaring 0
**Problem**: Bot preserved combos despite declaring 0  
**Root Cause**: AI assigned combos regardless of target_remaining  
**Solution**: Only preserve combos if target_remaining > 0  
**Test**: `test_combo_preservation_fix.py`

### Fix #2: Combo Rank Priority
**Problem**: Bot played high singles over lower-ranked combos  
**Root Cause**: Critical urgency maximized points not rank  
**Solution**: Prioritize combo rank over point value  
```python
# Sort by combo rank first, then points
combos.sort(key=lambda x: (
    -COMBO_TYPE_RANK.get(x[0], 0),  # Rank first
    -sum(p.point for p in x[1])      # Points second
))
```

### Fix #3: Opener Assignment Scaling
**Problem**: Fixed opener count regardless of declaration  
**Root Cause**: Hard-coded max 2 openers for 4+ declarations  
**Solution**: Scale openers with target_remaining  
```python
openers_needed = min(target_remaining, 4, len(all_openers))
```

### Fix #4: Smart Opener Assignment
**Problem**: Assigned openers without considering combos  
**Root Cause**: Independent opener and combo counting  
**Solution**: Count secured wins from combos first  
```python
# Count wins from non-opener combos
secured_wins = sum(1 for combo in combos if no_openers_in_combo)
openers_needed = max(0, target_remaining - secured_wins)
```

### Fix #5: Random Opener Play
**Problem**: Predictable opener selection  
**Root Cause**: Always selected max(openers)  
**Solution**: Random selection when urgency is low  
```python
if urgency == "low":
    chosen = [random.choice(openers)]
else:
    chosen = [max(openers, key=lambda p: p.point)]
```

### Fix #6: Object Comparison
**Problem**: Disposal strategy failed to find pieces  
**Root Cause**: Object identity vs equality comparison  
**Solution**: Compare by piece.kind not object  
```python
# OLD: if p in context.my_hand  # Object comparison
# NEW: if p.kind in hand_kinds  # Type comparison
```

### Fix #7: Zero Streak Rule
**Problem**: Bot declared 0 despite zero streak  
**Root Cause**: Early returns bypassed validation  
**Solution**: Centralize forbidden value checking

## Diagnostic Workflow

### 1. Enable Debug Logging

```bash
# Run with detailed AI logging
python backend/ai_debug_simple.py --games 1 --log-level detailed

# Check output in logs/ai_debug/
```

### 2. Analyze Decision Context

```python
# In AI logger output, look for:
{
    "type": "ai_decision",
    "phase": "declaration",
    "decision": 0,
    "reasoning": {
        "hand_strength": "weak",
        "combo_count": 0,
        "opener_count": 1,
        "pile_room": 2
    },
    "bugs": [
        {
            "bug_type": "zero_declaration_strong_hand",
            "severity": "medium"
        }
    ]
}
```

### 3. Reproduce in Test

```python
# Create minimal test case
def test_bug_reproduction():
    hand = create_hand_from_specs([
        ("ADVISOR_RED", 2),
        ("SOLDIER_BLACK", 3)
    ])
    
    context = create_context(
        declared=0,
        zero_streak=2,
        must_declare_nonzero=True
    )
    
    result = choose_declare(hand, context)
    assert result > 0, "Must declare non-zero with streak"
```

### 4. Validate Fix

```bash
# Run specific regression test
python tests/ai_regression/test_specific_bug.py

# Run full suite
python tests/ai_regression/run_all_regression_tests.py
```

## Quick Diagnosis Guide

### Declaration Issues

| Symptom | Check | Common Cause |
|---------|-------|--------------|
| Always declares 0 | Zero streak rule | Early return bypassing validation |
| Declares too high | Hand evaluation | Missing combo count |
| Exceeds pile room | Room calculation | GENERAL_RED logic |
| Inconsistent | Random factors | Urgency calculation |

### Turn Play Issues

| Symptom | Check | Common Cause |
|---------|-------|--------------|
| Plays weak combos | Never-win detection | Missing validation |
| Wrong piece count | Required pieces | Responder logic |
| Overcaptures | Constraints | Risk assessment |
| Disposes openers | Plan assignment | Object comparison |

## Prevention Strategies

### 1. Comprehensive Testing

```python
# Test all edge cases
test_scenarios = [
    "zero_declaration_with_streak",
    "high_declaration_weak_hand",
    "never_win_combo_avoidance",
    "overcapture_prevention",
    "opener_preservation"
]
```

### 2. Defensive Programming

```python
# Validate all inputs
assert target_remaining >= 0
assert len(hand) > 0
assert required_pieces is None or required_pieces > 0

# Handle edge cases explicitly
if pile_room == 0 and must_declare_nonzero:
    return 1  # Minimum valid declaration
```

### 3. Logging Best Practices

```python
# Log decision factors
logger.info(f"Declaration factors: {decision_factors}")
logger.info(f"Chosen play: {chosen} from {len(valid_plays)} options")

# Log when hitting edge cases
if len(valid_combos) == 0:
    logger.warning("No valid combos found, falling back to singles")
```

## Emergency Fixes

### Quick Patches

1. **Force Valid Declaration**
```python
if declaration == 0 and must_declare_nonzero:
    declaration = 1
```

2. **Prevent Never-Win**
```python
if is_never_win_combo(play_type, pieces):
    continue  # Skip this combo
```

3. **Cap Declaration**
```python
declaration = min(declaration, pile_room, 8)
```

### Rollback Procedure

1. Identify last working commit
2. Create hotfix branch
3. Apply minimal fix
4. Add regression test
5. Deploy with monitoring

## Monitoring and Alerts

### Key Metrics

- Bug detection rate per game
- Bug severity distribution
- Most common bug types
- Fix effectiveness rate

### Alert Thresholds

```python
if bugs_per_game > 5:
    alert("High bug rate detected")
    
if critical_bugs > 0:
    alert("Critical AI bug detected", urgent=True)
```

## Future Prevention

1. **Type Safety**: Use enums for game states
2. **Unit Tests**: Test each decision function
3. **Integration Tests**: Test full game scenarios
4. **Property Tests**: Random scenario generation
5. **Continuous Monitoring**: Track AI performance metrics