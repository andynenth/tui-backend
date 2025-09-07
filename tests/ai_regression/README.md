# AI Regression Test Suite

This directory contains regression tests for AI decision-making fixes. Each test file documents a specific bug that was fixed and ensures the fix continues to work.

## Test Organization

- `test_combo_preservation_fix.py` - Bot 3 ADVISOR_RED preservation bug (fixed by target_remaining check)
- `test_combo_rank_priority.py` - Bot 2 THREE_OF_A_KIND vs high singles (fixed by rank-first selection)
- `conftest.py` - Shared test fixtures and utilities
- `run_all_regression_tests.py` - Run all regression tests

## Running Tests

```bash
# Run all regression tests
python tests/ai_regression/run_all_regression_tests.py

# Run specific test
python tests/ai_regression/test_combo_rank_priority.py
```

## Adding New Tests

When fixing a new AI bug:
1. Create a test file: `test_<bug_description>.py`
2. Document the bug, fix, and expected behavior
3. Add test scenarios that reproduce the original bug
4. Verify the test fails without the fix and passes with it
5. Add to regression suite
