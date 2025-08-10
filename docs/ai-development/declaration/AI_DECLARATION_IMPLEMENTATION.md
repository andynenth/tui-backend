# AI Declaration Implementation Guide

## Overview

This document covers the technical implementation details of the AI declaration logic in Liap Tui, including current system analysis, bug findings, fixes implemented, and remaining TODOs.

## Current Implementation Analysis

### How The AI Declaration System Works

```python
# Simplified current logic in backend/engine/ai.py
score = count(strong_combos) + has_strong_opening + is_first_player
declare = clamp(score, 1, 7)
```

### Current Factors Considered
1. **Hand Strength**: Number of strong combinations (STRAIGHT, THREE_OF_A_KIND, etc.)
2. **Opening Power**: Has piece with 11+ points (GENERAL, ADVISOR)
3. **Position**: +1 if first player (starter bonus)
4. **Rule Compliance**: Avoid forbidden values (sum = 8, consecutive zeros)

### Current Factors NOT Considered
- Game score (winning/losing position)
- Round number (early/late game)
- Opponent patterns or modeling
- Previous round performance
- Risk/reward tradeoffs
- Previous declarations (field strength)
- Pile room constraints

## Major Bug Discovery

### Critical Pile Counting Bug

**Problem**: The AI was counting NUMBER of combinations instead of PILES they yield

```python
# OLD BUGGY LOGIC:
score = len(strong_combos)  # Just counted number of combos
# If hand has 1 STRAIGHT → score += 1
# But STRAIGHT actually yields 3 piles!
```

**Impact**: AI was systematically under-declaring by 2-5 piles

### The Fix (Already Implemented)

```python
# NEW CORRECT LOGIC (lines 63-74 in ai.py):
score = 0
for combo_type, pieces in strong_combos:
    if combo_type == "THREE_OF_A_KIND" or combo_type == "STRAIGHT":
        score += 3  # 3-piece play = 3 piles
    elif combo_type == "FOUR_OF_A_KIND" or combo_type == "EXTENDED_STRAIGHT":
        score += 4  # 4-piece play = 4 piles
    elif combo_type == "FIVE_OF_A_KIND" or combo_type == "EXTENDED_STRAIGHT_5":
        score += 5  # 5-piece play = 5 piles
    elif combo_type == "DOUBLE_STRAIGHT":
        score += 6  # 6-piece play = 6 piles
```

## Implementation Status

### ✅ Fixed Issues

1. **Pile-Aware Counting** (FIXED)
   - Now correctly counts piles based on combination size
   - THREE_OF_A_KIND → 3 piles (not 1)
   - FOUR_OF_A_KIND → 4 piles (not 1)
   - etc.

2. **Opener Detection** (FIXED)
   ```python
   # Old: Only GENERAL or 13+ points
   # New (lines 54-57):
   has_strong_opening = any(
       p.point >= 11 for p in hand  # Includes all ADVISOR pieces
   )
   ```

### ⚠️ Known Issues

1. **Overlapping Combinations**
   - Current logic counts all possible combinations even if they share pieces
   - Example: 4 SOLDIERs generates multiple THREE_OF_A_KIND combos
   - This causes over-counting since you can't use the same piece twice
   - **Impact**: Minor - may slightly over-declare in edge cases

2. **Declaration Range Bug** (TODO - Line 89)
   ```python
   # Current: Limits to [1,7]
   score = min(max(score, 1), 7)  # Clamp score to range [1, 7]
   
   # Should be: Allow [0,8] per game rules
   # (though game constraints will prevent some values)
   ```

## TODO List

### 1. Remove Starter Bonus ❌
**File**: `backend/engine/ai.py`  
**Location**: Around line 81
```python
# DELETE THESE LINES:
# First player advantage (control to play combos)
if is_first_player:
    score += 1
```
**Reason**: User decided to keep AI simple - no position bonuses

### 2. Fix Declaration Range Bug ❌
**File**: `backend/engine/ai.py`  
**Location**: Line 89
```python
# Current:
score = min(max(score, 1), 7)  # Wrong range!

# Change to:
score = min(max(score, 0), 8)  # Allow full range
```
**Note**: Game rules will still apply constraints (sum ≠ 8, etc.)

### 3. Consider Advanced Features (Optional)
Based on user preference for simplicity, these are NOT being implemented:
- ❌ Pile room calculation
- ❌ Field strength assessment  
- ❌ Previous declaration reading
- ❌ Opponent modeling
- ❌ Game state awareness
- ❌ Score-aware declaration (near victory, desperation mode)
- ❌ Round number awareness (early/late game)
- ❌ Memory/learning from previous rounds
- ❌ Pattern recognition of opponents
- ❌ Multiplier awareness (redeal scenarios)
- ❌ Confidence adjustments
- ❌ Randomness for variety

Note: These features were explored in detail but rejected to keep the AI simple and predictable.

## Testing Requirements

After implementing the TODO changes:

1. **Verify Pure Hand Evaluation**
   - Same hand should always produce same declaration
   - No variation based on position or previous declarations

2. **Check Declaration Range**
   - Bots should be able to declare 0 (weak hands)
   - Bots should be able to declare 8 (maximum combos)
   - Game rules (sum ≠ 8) still apply

3. **Test Starter Independence**
   - First player shouldn't get +1 bonus
   - Declaration based purely on hand strength

## Code Structure Reference

### Key Functions in `backend/engine/ai.py`

1. **`choose_declare()`** (lines 26-142)
   - Main declaration logic
   - Takes hand, position, previous declarations
   - Returns declaration value (0-8)

2. **`find_all_valid_combos()`** (lines 12-20)
   - Finds all valid combinations in hand
   - Returns list of (play_type, pieces)

3. **`choose_best_play()`** (lines 158-193)
   - Selects best play for a turn
   - Not related to declaration logic

## Debug Output

The AI includes verbose debug output (lines 92-115) showing:
- Position and starter status
- Previous declarations
- Hand composition
- Found combinations with pile counts
- Opener detection
- Final declaration choice

This is invaluable for understanding AI decisions during testing.