# Test Organization Summary

## Overview
Reorganized 35 test files from the root directory into the tests/ folder structure on 2025-08-10.

## Test Structure

### tests/ai_declaration/ (18 files + 8 moved)
- **Purpose**: AI declaration logic testing
- **New files moved**:
  - Declaration v2 implementation tests
  - Forbidden sum handling tests
  - Field strength tests
  - Edge cases for forbidden values
  - Fit function tests

### tests/ai_turn_play/ (2 files + 2 moved)
- **Purpose**: AI turn play strategy testing
- **New files moved**:
  - `test_starter_improvement.py` - Starter strategy improvements
  - `test_pile_count_timing.py` - Pile counting timing logic

### tests/opener_timing/ (8 files - new directory)
- **Purpose**: Opener detection and timing logic
- **Files**: All opener-related tests including single opener scenarios

### tests/overcapture/ (2 files - new directory)
- **Purpose**: Overcapture avoidance strategy testing
- **Files**:
  - `test_overcapture_avoidance.py`
  - `test_overcapture_with_new_strategy.py`

### tests/hand_evaluation/ (6 files - new directory)
- **Purpose**: Hand evaluation and combo detection
- **Files**:
  - AI hand evaluation consistency tests
  - Phase 4 hand evaluation
  - Combo detection tests
  - Pair detection tests
  - Test case comparison utilities

### tests/integration/ (1 file + 2 moved)
- **Purpose**: Full game flow integration tests
- **New files moved**:
  - `test_round_recreations.py`
  - `test_round_recreations_with_resolution.py`

### tests/edge_cases/ (5 files - new directory)
- **Purpose**: Specific bug fixes and edge case scenarios
- **Files**:
  - Bot scenario tests
  - Execution plan overlap tests
  - Debug tests for specific issues

### tests/unit/ (1 file)
- **Purpose**: Unit tests for specific components
- Existing unit tests preserved

## Benefits

1. **Clear test categories** - Tests grouped by functionality
2. **Easy test discovery** - Find related tests quickly
3. **Better organization** - No test files in root directory
4. **Scalable structure** - Easy to add new test categories
5. **Maintains CI/CD** - Test discovery still works with organized structure

## Running Tests

```bash
# Run all tests
pytest tests/

# Run specific category
pytest tests/ai_declaration/
pytest tests/opener_timing/
pytest tests/overcapture/

# Run specific test file
pytest tests/integration/test_round_recreations.py
```
