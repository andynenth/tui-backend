# Phase Transition Testing Guide

## Overview
This guide explains how to use unit tests to catch phase transition errors like the "Invalid transition: PREPARATION → DECLARATION" bug.

## Test Files

### 1. `test_phase_transition_errors.py`
Quick tests that catch common transition errors:
- Validates transition rules in state machine
- Would have caught our PREPARATION → DECLARATION bug
- Runs in < 1 second

### 2. `test_round_start_phase.py`
Comprehensive tests for ROUND_START phase:
- Tests all transition scenarios
- Validates phase data and timing
- Tests edge cases (redeals, disconnections)

### 3. `test_round_start_bot_integration.py`
Integration tests with bot manager:
- Ensures bots don't act during wrong phases
- Tests bot behavior during transitions
- Catches race conditions

## Running Tests

### Quick Validation (Recommended for frequent use)
```bash
cd backend
python run_phase_tests.py --quick
```

### Full Test Suite
```bash
cd backend
python run_phase_tests.py
```

### Specific Test
```bash
cd backend
pytest tests/test_phase_transition_errors.py -v
```

## When to Run Tests

1. **Before Commits**: Use the pre-commit hook
   ```bash
   cp backend/hooks/pre-commit-phase-check.sh .git/hooks/pre-commit
   chmod +x .git/hooks/pre-commit
   ```

2. **After Phase Changes**: Any modifications to:
   - State machine states
   - Phase transitions
   - Bot manager
   - Game flow

3. **In CI/CD**: Automatically via GitHub Actions

## Writing New Phase Tests

### Example: Testing a New Phase
```python
@pytest.mark.asyncio
async def test_new_phase_transitions(self):
    """Test transitions for NEW_PHASE"""
    game = Game([Player("Test")])
    sm = GameStateMachine(game)
    
    # Check allowed transitions
    assert GamePhase.NEXT_PHASE in sm._valid_transitions[GamePhase.NEW_PHASE]
    assert GamePhase.INVALID_PHASE not in sm._valid_transitions[GamePhase.NEW_PHASE]
    
    # Test actual transition
    await sm._transition_to(GamePhase.NEW_PHASE)
    assert sm.current_phase == GamePhase.NEW_PHASE
```

### Key Testing Patterns

1. **Transition Validation**
   ```python
   # Would catch invalid transitions at test time
   assert GamePhase.DECLARATION not in sm._valid_transitions[GamePhase.PREPARATION]
   ```

2. **State Consistency**
   ```python
   # Ensure state data is preserved
   phase_data = sm.get_phase_data()
   assert phase_data.get("expected_field") is not None
   ```

3. **Bot Behavior**
   ```python
   # Ensure bots don't act prematurely
   with patch.object(bot_handler, '_bot_declare') as mock:
       await bot_handler.handle_event("phase_change", data)
       mock.assert_not_called()
   ```

## Benefits

1. **Catch Bugs Early**: Tests fail immediately when transitions are wrong
2. **Prevent Regressions**: CI/CD catches issues before merge
3. **Document Behavior**: Tests serve as documentation
4. **Fast Feedback**: Quick tests run in seconds

## Common Errors Caught

1. **Invalid Transitions**
   - Direct PREPARATION → DECLARATION (our bug)
   - Skipping required phases
   - Backward transitions

2. **Bot Timing Issues**
   - Bots acting during wrong phase
   - Race conditions
   - Duplicate actions

3. **State Corruption**
   - Missing phase data
   - Incorrect starter determination
   - Lost game state

## Debugging Failed Tests

1. **Check Transition Map**
   ```python
   print(sm._valid_transitions)
   ```

2. **Trace Phase Flow**
   ```python
   print(f"Current: {sm.current_phase}")
   print(f"Allowed: {sm._valid_transitions[sm.current_phase]}")
   ```

3. **Verify State Data**
   ```python
   print(f"Phase data: {sm.get_phase_data()}")
   ```

## Best Practices

1. **Test After Every Phase Change**: Run quick validation
2. **Add Tests for New Phases**: Don't wait for bugs
3. **Test Edge Cases**: Disconnections, timeouts, concurrent actions
4. **Use Mocks**: Isolate components for unit tests
5. **Run in CI/CD**: Catch issues before production