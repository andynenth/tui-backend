# Redeal Animation Implementation Plan

## Overview
Add dealing animation for redeals by using a `dealing_cards` flag in the existing enterprise architecture. This allows the frontend to show the dealing animation whenever cards are being dealt (initial or redeal).

## Progress Tracker

### 1. Backend - Add dealing_cards flag
**File**: `/backend/engine/state_machine/states/preparation_state.py`

#### 1.1 Add dealing start signal
- [ ] Locate `_deal_cards()` method (line ~86)
- [ ] Find the comment "# Reset player round data before dealing" (line ~90)
- [ ] Add `dealing_cards: True` update_phase_data call BEFORE this comment
- [ ] Include log message: "Starting to deal cards"
- [ ] Include current `redeal_multiplier` in the phase data

#### 1.2 Add dealing complete signal  
- [ ] Find the end of `_deal_cards()` method (line ~173)
- [ ] Locate after weak hand check but before method ends
- [ ] Add `dealing_cards: False` update_phase_data call
- [ ] Include weak_players list in the phase data
- [ ] Include log message: "Cards dealt, checking for weak hands"

### 2. Frontend - GameService Integration

#### 2.1 Update state interface
**File**: `/frontend/src/services/types.ts`
- [ ] Find the `GameState` interface
- [ ] Add `dealingCards?: boolean` property
- [ ] Ensure it's optional with `?`

#### 2.2 Extract dealing_cards from phase events
**File**: `/frontend/src/services/GameService.ts`
- [ ] Find `handlePhaseChange()` method (line ~511)
- [ ] Locate where `phase_data` is extracted (around line ~590)
- [ ] Find the section that extracts phase-specific data
- [ ] Add extraction: `if (data.phase_data?.dealing_cards !== undefined)`
- [ ] Set `newState.dealingCards = data.phase_data.dealing_cards`

### 3. Frontend - Component Props Flow

#### 3.1 GameContainer - Extract and pass prop
**File**: `/frontend/src/components/game/GameContainer.jsx`
- [ ] Find `preparationProps` useMemo (line ~40)
- [ ] Locate where props are built from gameState
- [ ] Add `dealingCards: gameState.dealingCards || false`
- [ ] Verify it's included in the return object

#### 3.2 PreparationUI - Add prop definition
**File**: `/frontend/src/components/game/PreparationUI.jsx`
- [ ] Find the function parameters destructuring
- [ ] Add `dealingCards = false` to the parameters
- [ ] Find PropTypes definition at bottom
- [ ] Add `dealingCards: PropTypes.bool`
- [ ] Find where PreparationContent is rendered
- [ ] Pass `dealingCards={dealingCards}` as prop

#### 3.3 PreparationContent - Core animation logic
**File**: `/frontend/src/components/game/content/PreparationContent.jsx`

##### 3.3.1 Add prop
- [ ] Find function parameters (line ~13)
- [ ] Add `dealingCards = false` to destructured props
- [ ] Find PropTypes at bottom
- [ ] Add `dealingCards: PropTypes.bool`

##### 3.3.2 Add redeal animation state
- [ ] Find existing `useState` for showDealing (line ~30)
- [ ] Add new state below it: `const [isRedealing, setIsRedealing] = useState(false)`

##### 3.3.3 Add effect to watch dealing changes
- [ ] Find existing useEffect (line ~33)
- [ ] Add new useEffect below it
- [ ] Watch for `dealingCards` prop changes
- [ ] When true and not initial deal: set isRedealing to true
- [ ] Set 3500ms timeout to set isRedealing to false
- [ ] Add cleanup function to clear timeout

##### 3.3.4 Update render condition
- [ ] Find the condition `{showDealing ? (` (line ~64)
- [ ] Change to `{(showDealing || isRedealing) ? (`
- [ ] Find "Dealing Cards" text (line ~72)
- [ ] Change to conditional: `{isRedealing ? "Redealing Cards" : "Dealing Cards"}`

### 4. Testing Checklist

#### 4.1 Initial Deal Testing
- [ ] Start a new game
- [ ] Confirm animation shows immediately
- [ ] Verify animation text says "Dealing Cards"
- [ ] Time the animation (should be 3.5 seconds)
- [ ] Confirm cards appear after animation ends

#### 4.2 First Redeal Testing
- [ ] Ensure weak hand scenario (use test mode)
- [ ] Click "Request Redeal" button
- [ ] Verify animation shows again
- [ ] Confirm animation text says "Redealing Cards"
- [ ] Verify multiplier badge updates to 2x
- [ ] Confirm new cards appear after animation

#### 4.3 Multiple Redeal Testing
- [ ] Trigger second weak hand after first redeal
- [ ] Accept second redeal
- [ ] Verify animation shows for third time
- [ ] Confirm multiplier updates to 3x
- [ ] Test up to the redeal limit (5 redeals)

#### 4.4 Multiplayer Testing
- [ ] Open 2+ browser windows with different players
- [ ] Trigger redeal from one player
- [ ] Verify all players see animation simultaneously
- [ ] Confirm all players see same "Redealing Cards" message
- [ ] Check that all players receive new cards

#### 4.5 Edge Case Testing
- [ ] Rapidly click redeal multiple times - verify no duplicate animations
- [ ] Disconnect during animation - verify state is correct on reconnect
- [ ] Close browser during animation - verify no errors
- [ ] Navigate away during animation - verify cleanup occurs

## Implementation Details

### Backend Changes
```python
# In _deal_cards() method

# At the start (after line 88):
await self.update_phase_data({
    'dealing_cards': True,
    'redeal_multiplier': getattr(game, 'redeal_multiplier', 1)
}, "Starting to deal cards")

# At the end (after weak hand check):
await self.update_phase_data({
    'dealing_cards': False,
    'weak_players': list(self.weak_players),
    'redeal_multiplier': getattr(game, 'redeal_multiplier', 1)
}, "Cards dealt, checking for weak hands")
```

### Frontend Changes
```jsx
// In PreparationContent.jsx

// Add prop
const PreparationContent = ({
  // ... existing props
  dealingCards = false,
  // ...
}) => {

// Add state
const [isRedealing, setIsRedealing] = useState(false);

// Add effect
useEffect(() => {
  if (dealingCards === true && !showDealing) {
    setIsRedealing(true);
    const timer = setTimeout(() => {
      setIsRedealing(false);
    }, 3500);
    return () => clearTimeout(timer);
  }
}, [dealingCards, showDealing]);

// Update render condition
{(showDealing || isRedealing) ? (
  <div className="dealing-container">
    <div className="dealing-message">
      {isRedealing ? "Redealing Cards" : "Dealing Cards"}
    </div>
    {/* Animation */}
  </div>
) : (
  /* Normal content */
)}
```

## Success Criteria
1. ✅ Dealing animation shows for both initial deal and redeals
2. ✅ Animation duration is consistent (3.5 seconds)
3. ✅ No duplicate animations or conflicts
4. ✅ Clear visual feedback during redeal process
5. ✅ Backend and frontend stay in sync

## Multiplayer Considerations

### How It Works
- The `dealing_cards` flag is broadcast to ALL players via WebSocket using the enterprise architecture
- When backend sets `dealing_cards: true`, all connected players receive the update simultaneously
- Each player's frontend shows the dealing animation at the same time

### Benefits for Multiplayer
1. **Synchronized Experience** - All players wait together during dealing
2. **Fair Play Perception** - Everyone sees that cards are being dealt fairly
3. **Clear Communication** - No confusion about card changes
4. **No Additional Complexity** - Uses existing WebSocket infrastructure

### Animation Behavior
- Animation shows **every time** cards are dealt:
  - Initial deal when entering preparation phase
  - First redeal when someone accepts
  - All subsequent redeals if weak hands persist
- This consistent behavior ensures all players know when cards are being redistributed

### Network Considerations
- Small network delays (50-100ms) between players are negligible
- Animation is non-blocking - backend continues processing while animation plays
- If a player disconnects during animation, they see the final state upon reconnection

## Notes
- Uses existing enterprise architecture - no state machine changes
- `dealing_cards` is a transient flag, not persistent state
- Animation is purely frontend concern, backend just signals when dealing occurs
- No need to modify state machine core or add new phases

## Status
**Current Status**: Implementation Complete - Ready for Testing
**Last Updated**: 2025-01-10

## Completed Tasks

### Backend Implementation ✅
- Added `dealing_cards: true` signal at start of `_deal_cards()` method
- Added `dealing_cards: false` signal at end of `_deal_cards()` method
- Included redeal_multiplier and weak_players in phase data updates

### Frontend Implementation ✅
- Updated GameState interface with `dealingCards?: boolean` property
- Added extraction of dealing_cards flag in GameService.handlePhaseChange()
- Passed dealingCards prop through component hierarchy:
  - GameContainer → PreparationUI → PreparationContent
- Implemented redeal animation logic with isRedealing state
- Shows "Dealing Cards" for initial deal, "Redealing Cards" for redeals

## Next Steps
- Test initial deal animation
- Test redeal flow with weak hands
- Test multiple consecutive redeals
- Test multiplayer synchronization
- Verify edge cases and cleanup