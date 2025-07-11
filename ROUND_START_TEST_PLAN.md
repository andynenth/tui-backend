# Round Start Feature Test Plan

## Test Scenarios

### 1. Round 1 - Red General Test
- **Setup**: Start a new game with 4 players
- **Expected**: 
  - After cards are dealt in PREPARATION phase, system identifies player with GENERAL_RED
  - ROUND_START phase displays for 5 seconds showing:
    - "Round 1"
    - Player name who has GENERAL_RED
    - "has the General Red piece"
  - Auto-transitions to DECLARATION phase

### 2. Round 2+ - Previous Winner Test  
- **Setup**: Complete round 1 and start round 2
- **Expected**:
  - ROUND_START phase shows:
    - "Round 2"
    - Name of player who won the last turn of round 1
    - "won the last turn"
  - Auto-transitions to DECLARATION phase

### 3. Redeal Acceptance Test
- **Setup**: Player with weak hand accepts redeal
- **Expected**:
  - After redeal in PREPARATION phase
  - ROUND_START phase shows:
    - Current round number
    - Player who accepted redeal
    - "accepted the redeal"

### 4. Timer Functionality Test
- **Expected**:
  - FooterTimer counts down from 5 to 0
  - Shows "Starting in X"
  - Phase auto-advances exactly when timer hits 0

### 5. CSS Animation Test
- **Expected**:
  - fadeIn animation on main content
  - slideDown animation on round section
  - scaleIn animation on round number (delayed)
  - Proper styling with rs- prefixed classes

### 6. Backend State Sync Test
- **Expected**:
  - `current_starter` properly set in phase_data
  - `starter_reason` correctly identifies why player is starter
  - All clients receive same starter information

## Backend Debug Commands

```python
# Check current phase
print(f"Current phase: {game.phase}")

# Check phase data
print(f"Phase data: {game.state_machine.current_state.phase_data}")

# Check starter reason
print(f"Starter: {game.current_starter}, Reason: {game.starter_reason}")
```

## Frontend Debug Commands

```javascript
// In browser console
const gameService = window.gameService;
console.log('Current phase:', gameService.getState().phase);
console.log('Current starter:', gameService.getState().currentStarter);
console.log('Starter reason:', gameService.getState().starterReason);
```

## Visual Verification Checklist

- [ ] Round number displays large and centered
- [ ] Starter name is clearly visible
- [ ] Reason text uses appropriate color based on reason type
- [ ] Timer shows at bottom and counts down smoothly
- [ ] Background has subtle radial gradient effect
- [ ] All text is readable and properly spaced
- [ ] Responsive adjustments work on smaller screens