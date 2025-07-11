# Vertical Drop Animation Implementation Plan

## Objective
Implement a **Vertical Drop (Staggered) Animation** with fade-in effect for game pieces during dealing and redeal phases. Pieces should drop from above and fade in sequentially with an 80ms stagger delay between each piece, creating a cascading visual effect.

### Animation Specifications
- **Duration**: 350ms per piece
- **Stagger Delay**: 80ms between pieces
- **Effect**: Pieces start invisible 50px above, fade in while dropping
- **Trigger**: Automatically during initial deal and any redeal

## Current State Analysis

### Existing Components
- [x] `PieceTray` component supports `animateAppear` prop
- [x] `GamePiece` component supports `animationDelay` prop
- [x] `PreparationContent` shows dealing animation and uses PieceTray
- [x] CSS animation system exists in `_animations.css`

### Current Animation
- Pieces use `gentleBounce` animation when becoming selectable (turn phase)
- PieceTray in preparation phase has `animateAppear={true}` but uses default animation
- Animation delay is hardcoded to `index * 0.1` seconds

## Task Breakdown

### 1. CSS Implementation
- [✅] Add `.game-piece--dealing` variant class to `game-piece.css`
- [✅] Create `verticalDropStagger` keyframes animation
- [✅] Ensure animation starts with `opacity: 0` and ends with `opacity: 1`
- [✅] Set transform from `translateY(-50px)` to `translateY(0px)`

### 2. GamePiece Component Updates
- [✅] Add 'dealing' to variant PropTypes validation
- [✅] Update class name builder to handle 'dealing' variant (automatic via existing logic)
- [✅] Ensure animation delay prop works with new variant

### 3. PieceTray Component Enhancement
- [✅] Add `animationType` prop (values: 'bounce', 'verticalDrop')
- [✅] Add logic to pass correct variant to GamePiece based on animationType
- [✅] Update animation delay calculation for verticalDrop (80ms stagger)
- [✅] Maintain backward compatibility with existing usage

### 4. PreparationContent Integration
- [✅] Pass `animationType="verticalDrop"` to PieceTray
- [✅] Animation triggers on both initial deal and redeal (via animateAppear prop)
- [ ] Test that animation works correctly during redeal scenarios

### 5. Testing & Validation
- [ ] Test initial deal animation
- [ ] Test redeal animation trigger
- [ ] Verify 80ms stagger timing
- [ ] Ensure pieces remain visible after animation
- [ ] Test with different hand sizes (8 pieces)
- [ ] Verify no conflicts with turn phase animations

## Dependencies & Blockers

### Dependencies
1. **CSS Animation System**: Relies on existing animation infrastructure
2. **Component Props**: Requires prop drilling through PreparationUI → PreparationContent → PieceTray → GamePiece
3. **Dealing State**: Depends on `dealingCards` prop from backend

### Potential Blockers
1. **Animation Conflicts**: Need to ensure new animation doesn't interfere with existing `gentleBounce`
2. **Timing Synchronization**: Animation should complete within dealing phase (3.5s)
3. **State Management**: Must handle rapid redeal scenarios without animation glitches

## Implementation Notes

### Animation CSS Structure
```css
.game-piece--dealing {
  animation: verticalDropStagger 0.35s ease-out forwards;
  opacity: 0;
  transform: translateY(-50px);
}

@keyframes verticalDropStagger {
  0% {
    opacity: 0;
    transform: translateY(-50px);
  }
  20% {
    opacity: 0.5;
    transform: translateY(-30px);
  }
  60% {
    opacity: 1;
    transform: translateY(-10px);
  }
  100% {
    opacity: 1;
    transform: translateY(0px);
  }
}
```

### Component Flow
```
PreparationContent (tracks dealing state)
  └── PieceTray (animationType="verticalDrop")
      └── GamePiece (variant="dealing", animationDelay={index * 0.08})
```

## Progress Tracking

### Status Legend
- [ ] Not Started
- [🔄] In Progress
- [✅] Completed
- [❌] Blocked

### Timeline
- **Start Date**: [TBD]
- **Target Completion**: [TBD]
- **Actual Completion**: [TBD]

### Testing Checklist
- [ ] Animation displays correctly in Chrome
- [ ] Animation displays correctly in Firefox
- [ ] Animation displays correctly in Safari
- [ ] No console errors during animation
- [ ] Performance is smooth (60fps)
- [ ] Animation resets properly on redeal

## Notes & Updates
_Add implementation notes, decisions, and updates here as work progresses_

### Implementation Details
- **CSS**: Added `.game-piece--dealing` class with `verticalDropStagger` animation (350ms duration)
- **GamePiece**: Extended variant prop to accept 'dealing' value
- **PieceTray**: Added `animationType` prop with logic to switch between animation types
- **PreparationContent**: Set to use `animationType="verticalDrop"` for all dealing scenarios
- **Stagger Timing**: Set to 80ms between pieces (index * 0.08)

### Key Decisions
1. Used separate CSS class for dealing animation to avoid conflicts with turn phase animations
2. Made animation type configurable via prop for future flexibility
3. Kept backward compatibility - default animationType is 'bounce'

---

### Update Log
- **Created**: Initial plan document created
- **Implementation Complete**: All code changes implemented, ready for testing
- **Animation Timing Fix**: Added 2-second delay in backend when no weak hands found to allow animation to complete before phase transition
- **Redeal Animation Fix**: Added key prop with dealCount to force React to re-mount PieceTray and replay animation on redeal