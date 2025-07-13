# Turn Selection Text Implementation

## Overview
This document tracks the implementation of dynamic text feedback for piece selection in the Turn phase of Liap Tui game.

## Feature Requirements

### Design Decisions
Based on our discussion, the text will change dynamically based on:
1. Player role (Starter vs Follower)
2. Number of pieces selected
3. Validity of the selection

### Text Specifications

#### Starter Player
**Default (no pieces selected):**
```
"As starter, your play must be valid"
```

**With 2+ pieces selected:**
```
"✓ Valid [Play Type]"
```
Example: "✓ Valid Pair", "✓ Valid Straight"

#### Follower Player
**Default (no/wrong count selected):**
```
"Must play exactly X piece(s)"
```

**With exact count selected (2+ pieces):**
- Valid play:
  ```
  "✓ Your [Play Type] can compete this turn"
  ```
- Invalid play:
  ```
  "⚠️ Not a [Play Type] - play to forfeit turn"
  ```

**With exact count selected (1 piece):**
```
"✓ Ready to play"
```

### Formatting Rules
- Play types use Title Case (e.g., "Pair" not "PAIR")
- Optional bold for play type emphasis
- ✓ symbol for valid selections
- ⚠️ symbol for warnings

## Implementation Plan

### Step 1: Update gameValidation.js ✅
- [x] Add `getPlayType(pieces)` function
- [x] Fix validation to match pieces by value (not name+color)
- [x] Return proper play type names

### Step 2: Update TurnContent.jsx ✅
- [x] Import gameValidation utilities
- [x] Add state for tracking validation result
- [x] Update turn-selection-count rendering logic
- [x] Add conditional text based on selection

### Step 3: Testing ✅
- [x] Test starter player text variations
- [x] Test follower player with valid plays
- [x] Test follower player with invalid plays
- [x] Test single piece selection
- [x] Test edge cases (0 pieces, > required pieces)

## Code Changes Needed

### 1. gameValidation.js additions:
```javascript
export function getPlayType(pieces) {
  if (!pieces || pieces.length === 0) return null;
  if (pieces.length === 1) return null; // Don't show type for single
  
  // Check for pairs (by value)
  if (pieces.length === 2 && isPair(pieces)) return "Pair";
  
  // Check for straights
  if (isStraight(pieces)) return "Straight";
  
  // Check for X of a kind
  if (isThreeOfAKind(pieces)) return "Three of a Kind";
  if (isFourOfAKind(pieces)) return "Four of a Kind";
  if (isFiveOfAKind(pieces)) return "Five of a Kind";
  
  // Extended patterns
  if (isExtendedStraight(pieces)) return "Extended Straight";
  if (isDoubleStraight(pieces)) return "Double Straight";
  
  return null; // Invalid combination
}
```

### 2. TurnContent.jsx modifications:
- Import: `import { getPlayType } from '../../../utils/gameValidation';`
- Update the turn-selection-count div content logic

## Progress Tracking

### Completed ✅
- [x] File organization - moved gameValidation.js to src/utils
- [x] Design finalized with all text variations
- [x] Created this tracking document

### In Progress 🔄
- [x] Implementation of text display logic ✅

### Not Started ⬜
- [x] Testing and validation ✅
- [ ] Final integration testing

## Testing Checklist

### Starter Player Tests
- [x] No selection shows "As starter, your play must be valid" ✅
- [x] 1 piece selected shows default text ✅
- [x] 2 matching pieces shows "✓ Valid Pair" ✅
- [x] 3 in straight shows "✓ Valid Straight" ✅
- [x] Invalid 2+ selection shows default text ✅

### Follower Player Tests
- [x] Wrong count shows "Must play exactly X piece(s)" ✅
- [x] Exact count (1 piece) shows "✓ Ready to play" ✅
- [x] Valid pair shows "✓ Your Pair can compete this turn" ✅
- [x] Invalid 2 pieces shows "⚠️ Not a Pair - play to forfeit turn" ✅
- [x] Valid straight shows "✓ Your Straight can compete this turn" ✅

## Notes
- Backend already validates plays, frontend just provides feedback
- Invalid plays are allowed for followers (auto-lose)
- Play type detection should match backend rules
- Consider adding CSS classes for different states (valid/invalid/warning)

## Next Steps
1. Implement getPlayType function
2. Update TurnContent component
3. Test all scenarios
4. Polish visual styling if needed