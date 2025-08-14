# Dead Code Analysis Report: backend/engine/ai.py (UPDATED)

## Executive Summary
After fixing the bug where `choose_declare()` was calling the old `choose_declare_strategic()` instead of `choose_declare_strategic_v2()`, the dead code situation has reversed. The old strategic system is now dead code, while the V2 system is active.

## Active Code (Now Used in Production)

### Main V2 Declaration System
1. **`choose_declare()`** (Lines 1281-1301) - Entry point, calls V2
2. **`choose_declare_strategic_v2()`** (Lines 1039-1275) - Main V2 logic
3. **`calculate_pile_room()`** (Lines 92-143) - Used by V2
4. **`get_piece_threshold()`** (Lines 383-408) - Used by V2
5. **`get_individual_strong_pieces()`** (Lines 410-437) - Used by V2
6. **`remove_pieces_from_hand()`** (Lines 365-380) - Used by V2 and others
7. **`find_and_select_strong_combos_iteratively()`** (Lines 779-837) - Used by V2
8. **`fit_plays_to_pile_room()`** (Lines 439-485) - Used by V2
9. **`rebuild_play_list_avoiding_forbidden()`** (Lines 843-1033) - Used by V2

### Functions Used by V2's Helper Functions
10. **`find_all_valid_combos()`** (Lines 323-331) - Used by iterative combo finder
11. **`is_strong_combo()`** (Lines 338-362) - Used by iterative combo finder

### Turn Play Functions (Still Active)
12. **`choose_best_play()`** (Lines 1318-1354) - Basic turn play logic
13. **`choose_strategic_play_safe()`** (Lines 1359-1398) - Safe wrapper for turn play

### Functions Used in Other Files
14. **`assess_field_strength()`** (Lines 146-164) - Used in ai_turn_strategy.py

## Dead Code Identified

### 1. **Old Strategic Declaration System** (Lines 490-773)
- **Function**: `choose_declare_strategic()`
- **Status**: DEAD CODE - No longer called after bug fix
- **Evidence**: Only called from tests, not from production code
- **Lines**: 490-773 (283 lines)

### 2. **Functions Only Used by Old Strategic System**

#### `is_combo_viable_simplified()` (Lines 214-243)
- **Status**: DEAD CODE - Only used by old strategic
- **Evidence**: Only called from `choose_declare_strategic`
- **Lines**: 214-243 (30 lines)

#### `is_starter_preferred_combo()` (Lines 50-72)
- **Status**: DEAD CODE - Only used by old strategic
- **Evidence**: Only called from `choose_declare_strategic`
- **Lines**: 50-72 (23 lines)

### 3. **Completely Orphaned Functions (Never Called)**

#### `DeclarationContext` (Lines 78-87)
- **Status**: DEAD CODE - Never used
- **Evidence**: Only referenced in dead `filter_viable_combos`
- **Lines**: 78-87 (10 lines)

#### `filter_viable_combos()` (Lines 245-317)
- **Status**: DEAD CODE - Never called
- **Evidence**: Defined but no calls found in any backend code
- **Lines**: 245-317 (73 lines)

#### `evaluate_opener_reliability()` (Lines 194-212)
- **Status**: DEAD CODE - Never called
- **Evidence**: Defined but no calls found
- **Lines**: 194-212 (19 lines)

#### `analyze_opponent_patterns()` (Lines 166-191)
- **Status**: DEAD CODE - Never called
- **Evidence**: Defined but no calls found
- **Lines**: 166-191 (26 lines)

#### `pieces_exist_in_hand()` (Lines 1309-1312)
- **Status**: DEAD CODE - Never called
- **Evidence**: Defined but no calls found
- **Lines**: 1309-1312 (4 lines)

### 4. **Unused Constants**

#### `STARTER_PREFERRED_COMBOS` (Lines 11-18)
- **Status**: DEAD CODE - Only used by dead function
- **Evidence**: Only used in `is_starter_preferred_combo`
- **Lines**: 11-18 (8 lines)

## Total Dead Code Count
- **Old Strategic System**: 283 lines
- **Functions only used by old system**: 53 lines  
- **Completely orphaned functions**: 132 lines
- **Unused constants**: 8 lines
- **Total Dead Code**: ~476 lines out of 1399 total lines (34% of the file)

## Verification Commands Used

```bash
# Check if function is called
grep "function_name(" backend/engine/ai.py

# Check across all backend files
grep -r "function_name" backend/ --include="*.py"

# List all function definitions
grep -E "^def [a-zA-Z_]+\(" backend/engine/ai.py
```

## Recommendations

### 1. **Remove Old Strategic System**
The old `choose_declare_strategic()` and its exclusive dependencies should be removed:
- `choose_declare_strategic()` function
- `is_combo_viable_simplified()`
- `is_starter_preferred_combo()`
- `STARTER_PREFERRED_COMBOS` constant

### 2. **Remove Orphaned Functions**
These functions are never called and should be removed:
- `DeclarationContext` dataclass
- `filter_viable_combos()`
- `evaluate_opener_reliability()`
- `analyze_opponent_patterns()`
- `pieces_exist_in_hand()`

### 3. **Keep Active Functions**
These functions are used by the V2 system or other parts:
- All V2 functions and their helpers
- `assess_field_strength()` (used in ai_turn_strategy.py)
- Turn play functions

## Impact Analysis

### Benefits of Removing Dead Code:
1. **Reduce file size**: From 1399 to ~923 lines (34% reduction)
2. **Improve clarity**: No confusion between old and new strategies
3. **Easier maintenance**: Less code to understand and maintain
4. **Cleaner tests**: Can remove tests for old strategic system

### Risk Assessment:
- **LOW RISK**: Dead code is clearly isolated
- V2 system is now properly connected and functional
- Turn play functions remain intact

## Test File Cleanup Needed

After removing dead code, these test files referencing the old system can be removed:
```bash
grep -r "choose_declare_strategic[^_v2]" tests/ --include="*.py" | grep -v "choose_declare_strategic_v2"
```

## Conclusion

The code cleanup is now more focused. After fixing the V2 connection bug, we have 34% dead code (down from the incorrect 57% estimate). The old strategic system and several orphaned helper functions can be safely removed to improve code maintainability.