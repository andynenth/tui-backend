# Piece Property Standardization - Task Tracking

## Objective
Standardize piece properties across the frontend to use `kind` (matching backend naming) instead of the current mix of `type`, `kind`, and `name`.

## Current State Analysis

### Backend (Python)
- Primary property: `kind` (e.g., "GENERAL_RED" - includes color)
- Derived property: `name` (e.g., "GENERAL" - piece type only)
- Value property: `point`

### Frontend (JavaScript/TypeScript)
Currently creates redundant properties:
- `type`: lowercase piece type (e.g., "general")
- `kind`: uppercase piece type (e.g., "GENERAL") 
- `name`: lowercase piece type (e.g., "general") - duplicate of `type`
- `value`: piece points
- `point`: piece points - duplicate of `value`
- `color`: separate color property (e.g., "red")

### Decision
Use `kind` for piece type (uppercase, e.g., "GENERAL") to align with backend's `piece.name` property.

## Files to Update

### 1. GameService.ts
**File**: `/frontend/src/services/GameService.ts`
**Lines**: 530-553
**Current Code**:
```javascript
return {
  type: piece.toLowerCase(),
  color: color.toLowerCase() as 'red' | 'black',
  value: parseInt(value),
  point: parseInt(value),
  kind: piece,
  name: piece.toLowerCase(),
  displayName: `${piece} ${color}`,
  originalIndex: index
};
```
**Change to**:
```javascript
return {
  kind: piece,  // Keep uppercase "GENERAL"
  color: color.toLowerCase() as 'red' | 'black',
  value: parseInt(value),
  displayName: `${piece} ${color}`,
  originalIndex: index
};
```
**Status**: ✅ Completed

### 2. GamePiece.jsx
**File**: `/frontend/src/components/game/shared/GamePiece.jsx`
**Line**: 89
**Current**: `type: PropTypes.string,`
**Change to**: `kind: PropTypes.string,`
**Status**: ✅ Completed

### 3. TurnContent.jsx
**File**: `/frontend/src/components/game/content/TurnContent.jsx`
**Changes needed**:
- Line 100: `${index}-${piece.type}-${piece.color}` → `${index}-${piece.kind}-${piece.color}`
- Line 273: Update getPlayType usage if needed
**Status**: ✅ Completed

### 4. PieceTray.jsx  
**File**: `/frontend/src/components/game/shared/PieceTray.jsx`
**Check for**: Any usage of `piece.type`
**Status**: ✅ Completed

### 5. gameValidation.js
**File**: `/frontend/src/utils/gameValidation.js`
**Changes needed**:
1. Remove `getPieceType` helper function (lines 62-68)
2. Update all functions to use `p.kind` instead of `getPieceType(p)`:
   - Line 85: `pieces.map(p => getPieceType(p))` → `pieces.map(p => p.kind)`
   - Line 102: `pieces.map(p => getPieceType(p))` → `pieces.map(p => p.kind)`
   - Line 126: `pieces.map(p => getPieceType(p))` → `pieces.map(p => p.kind)`
   - Line 144: `pieces.map(p => getPieceType(p))` → `pieces.map(p => p.kind)`
3. Update `getPieceValue` (lines 49-57):
   - Remove lines checking `piece.type` and `piece.name`
   - Keep only: `piece.value`, `piece.point` (for now), and `piece.kind`
**Status**: ✅ Completed

### 6. pieceMapping.js
**File**: `/frontend/src/utils/pieceMapping.js`
**Changes needed**:
1. Update `parsePiece` function (lines 42-78):
   - Line 48: Change `type: pieceData.kind` to `kind: pieceData.kind`
   - Line 54-56: Change check from `pieceData.type` to `pieceData.kind`
   - Line 65: Change return to use `kind` instead of `type`
   - Line 74: Change fallback to use `kind: 'UNKNOWN'`
2. Update `getPieceDisplay` function (lines 85-112):
   - Line 88-90: Change check from `piece.type` to `piece.kind`
   - Line 93: Change `${piece.type}_${piece.color}` to `${piece.kind}_${piece.color}`
   - Line 99-101: Change `PIECE_CHINESE_MAP[piece.type]` to `PIECE_CHINESE_MAP[piece.kind]`
   - Line 104: Change `piece.type.replace` to `piece.kind.replace`
   - Line 111: Change `piece.type.charAt(0)` to `piece.kind.charAt(0)`
**Status**: ✅ Completed

## Testing Plan

### 1. Unit Tests
- Test piece validation with new property names
- Test piece display functions

### 2. Manual Testing
- [ ] Verify piece selection in Turn phase works
- [ ] Verify turn-selection-count shows correct validation messages
- [ ] Verify straight detection works (the original issue)
- [ ] Verify pair detection works
- [ ] Verify all piece combinations are detected correctly
- [ ] Verify piece display shows correct Chinese characters
- [ ] Verify piece colors are applied correctly

### 3. Regression Testing
- [ ] Play through a full game round
- [ ] Check all phases display pieces correctly
- [ ] Verify no console errors about missing properties

## Rollback Plan
If issues arise, revert all changes and re-add the `getPieceType` helper to gameValidation.js as a temporary fix.

## Notes
- Keep `point` property temporarily in GameService.ts if other code depends on it
- The backend's `kind` includes color (e.g., "GENERAL_RED"), but frontend splits this
- Frontend `kind` will match backend's `name` property, not backend's `kind`