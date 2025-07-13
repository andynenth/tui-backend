# 🧾 Turn Phase Animation Enhancement Implementation Plan

## 📋 Executive Summary
This plan outlines the implementation of selective piece reveal animations based on the starter's declared play type. Currently, all pieces are revealed after all players submit their plays. The enhancement will modify this behavior to only reveal pieces that match the starter's play type.

## 🔍 Current State Analysis

### Data Flow
1. **Backend** sends play data including:
   - `playType` - The starter's declared type (e.g., "PAIR", "STRAIGHT", "THREE_OF_A_KIND")
   - `playerPieces` - Each player's played pieces
   - `currentTurnPlays` - Array of all plays in the current turn

2. **Frontend** receives and processes:
   - Turn UI gets data via `currentTurnPlays` prop
   - Turn Results gets data via `playerPlays` prop
   - Both phases receive the starter's `playType`

### Current Animation Behavior
- **Turn UI**: All pieces flip after 800ms when last player submits
- **Turn Results**: No flip animation - pieces shown immediately
- **Flip Trigger**: Based on player count, not play validity

### Validation Logic
- Backend only validates piece count matches starter's play
- Frontend shows warnings for mismatched types but allows play
- No actual prevention of type mismatches

## 🎯 Implementation Requirements

### 1. Play Type Matching Logic
Create a function to determine if a play matches the starter's type:

```javascript
// utils/playTypeMatching.js
export function doesPlayMatchStarterType(playerPieces, starterPlayType) {
  // Get the play type of the player's pieces
  const playerPlayType = getPlayType(playerPieces);
  
  // Special cases:
  // - SINGLE always matches (any single piece is valid)
  // - INVALID or UNKNOWN never match
  // - null/undefined never match
  
  return playerPlayType === starterPlayType;
}
```

### 2. Selective Reveal Logic
Modify flip animation to only reveal matching pieces:

```javascript
// In TurnContent.jsx
const determineWhichPiecesToReveal = () => {
  const piecesToReveal = new Set();
  
  Object.entries(playerPieces).forEach(([playerName, pieces]) => {
    // Always reveal starter's pieces
    if (playerName === lastWinner || playerName === currentTurnStarter) {
      pieces.forEach((_, idx) => {
        piecesToReveal.add(`${playerName}-${idx}`);
      });
      return;
    }
    
    // Check if player's play matches starter's type
    if (doesPlayMatchStarterType(pieces, playType)) {
      pieces.forEach((_, idx) => {
        piecesToReveal.add(`${playerName}-${idx}`);
      });
    }
  });
  
  return piecesToReveal;
};
```

### 3. Visual Design for Unrevealed Pieces
Unrevealed pieces should remain face-down with enhanced visual feedback:

```css
/* game-piece.css additions */
.game-piece--table:not(.flipped) {
  /* Keep existing back face design */
}

.game-piece--table.invalid-play:not(.flipped) {
  /* Add subtle visual indicator */
  opacity: 0.7;
  filter: grayscale(50%);
}

.game-piece--table.invalid-play:not(.flipped):hover {
  /* Allow manual reveal on hover */
  transform: rotateY(180deg);
  transition: transform 0.3s ease;
}
```

## 📝 Implementation Checklist

### Task 1: Add Flip Animation Keyframe ✅
- [x] Review existing animations in `_animations.css`
- [ ] Add new `pieceFlipSelective` keyframe with proper 3D rotation
- [ ] Add staggered delay calculations for dramatic effect

### Task 2: Create Play Type Matching Utility
- [ ] Create `utils/playTypeMatching.js`
- [ ] Implement `doesPlayMatchStarterType()` function
- [ ] Add unit tests for all play type combinations
- [ ] Handle edge cases (null, undefined, INVALID types)

### Task 3: Enhance TurnContent.jsx
- [ ] Modify flip detection logic to use selective reveal
- [ ] Add `determineWhichPiecesToReveal()` function
- [ ] Update flip animation trigger to use new logic
- [ ] Add visual indicators for invalid plays
- [ ] Implement staggered animation delays

### Task 4: Update GamePiece Component
- [ ] Add `invalidPlay` prop to GamePiece
- [ ] Add CSS classes for invalid play state
- [ ] Implement hover-to-reveal for unrevealed pieces
- [ ] Add smooth transition animations

### Task 5: Add Flip Animation to TurnResultsContent
- [ ] Add initial hidden state for all pieces
- [ ] Implement same selective reveal logic as Turn UI
- [ ] Add entrance animation with staggered delays
- [ ] Ensure consistency with Turn UI behavior

### Task 6: CSS Enhancements
- [ ] Add `.invalid-play` styling
- [ ] Implement hover effects for unrevealed pieces
- [ ] Add visual feedback for matching vs non-matching plays
- [ ] Ensure mobile-friendly interactions

### Task 7: Testing & Polish
- [ ] Test all play type combinations
- [ ] Verify animation timing and smoothness
- [ ] Test on different screen sizes
- [ ] Add accessibility considerations

## 🏗️ Affected Components & Files

### Components to Modify:
1. `/frontend/src/components/game/content/TurnContent.jsx`
2. `/frontend/src/components/game/content/TurnResultsContent.jsx`
3. `/frontend/src/components/game/shared/GamePiece.jsx`

### New Files to Create:
1. `/frontend/src/utils/playTypeMatching.js`

### Styles to Update:
1. `/frontend/src/styles/components/game/_animations.css`
2. `/frontend/src/styles/components/game/shared/game-piece.css`
3. `/frontend/src/styles/components/game/content/turn-content.css`
4. `/frontend/src/styles/components/game/content/turn-results.css`

## 🔄 Animation Flow

### Turn UI Phase:
1. All players submit their plays
2. 800ms delay begins
3. Determine which pieces match starter's type
4. Reveal matching pieces with staggered animation (50ms between players)
5. Non-matching pieces remain face-down
6. Users can hover to peek at unrevealed pieces

### Turn Results Phase:
1. Component mounts with all pieces hidden
2. 200ms initial delay
3. Replay the reveal animation from Turn UI
4. Same rules apply - only matching pieces auto-reveal
5. Display continues until timer expires

## ⚠️ Known Issues & Considerations

1. **Backend Validation**: Backend currently allows any piece combination if count matches. This enhancement is frontend-only.

2. **Play Type Detection**: Must handle edge cases where `getPlayType()` returns null or INVALID.

3. **User Experience**: Consider adding tooltips explaining why pieces weren't revealed.

4. **Performance**: With 4 players and up to 6 pieces each, ensure smooth animations.

5. **Accessibility**: Provide keyboard shortcuts to reveal all pieces for screen readers.

## 🎨 Visual Mockup

```
Before Last Play:
[Back] [Back] [Back]  <- Player 1 (played)
[Back] [Back]         <- Player 2 (played)
[Hand pieces...]      <- Player 3 (current)
[Empty]               <- Player 4 (waiting)

After Last Play (Starter played PAIR):
[♠K] [♠K]            <- Player 1 (PAIR - revealed)
[Back] [Back]         <- Player 2 (not matching - hidden)
[♥Q] [♥Q]            <- Player 3 (PAIR - revealed)
[Back] [Back] [Back]  <- Player 4 (THREE_OF_A_KIND - hidden)
```

## 📊 Success Criteria

1. Only pieces matching the starter's play type are automatically revealed
2. Non-matching pieces remain face-down but can be manually revealed
3. Animation is smooth and visually appealing
4. Turn Results phase has the same reveal behavior as Turn UI
5. Code is maintainable and well-documented
6. No regression in existing functionality

## 🚀 Next Steps

1. Review and approve this plan
2. Implement utility functions and tests
3. Update components incrementally
4. Test thoroughly with various play scenarios
5. Deploy and monitor for issues