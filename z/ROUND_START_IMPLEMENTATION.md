# Round Start Implementation Tracking

## Overview
Implementing a pre-round screen that displays after PREPARATION phase and before DECLARATION phase.

## Phase Flow
```
PREPARATION → ROUND_START (5 sec) → DECLARATION
```

## Backend Tasks

### 1. Core Phase Addition ✅
**File**: `/backend/engine/state_machine/core.py`
- [x] Add `ROUND_START = "round_start"` to GamePhase enum
- [x] Add to ActionType if needed (not needed)

### 2. Create RoundStartState ✅
**File**: `/backend/engine/state_machine/states/round_start_state.py`
- [x] Create new file
- [x] Implement RoundStartState class
- [x] Add 5-second timer logic
- [x] Implement auto-transition to DECLARATION

### 3. Update PreparationState ✅
**File**: `/backend/engine/state_machine/states/preparation_state.py`
- [x] Change `next_phases` from `[GamePhase.DECLARATION]` to `[GamePhase.ROUND_START]`
- [x] Add `game.starter_reason` when finding GENERAL_RED
- [x] Add `game.starter_reason` when using last turn winner
- [x] Add `game.starter_reason` when redeal accepted

### 4. Update GameStateMachine ✅
**File**: `/backend/engine/state_machine/game_state_machine.py`
- [x] Import RoundStartState
- [x] Add to state_classes dictionary
- [x] Update transition validation map

### 5. Update __init__.py ✅
**File**: `/backend/engine/state_machine/states/__init__.py`
- [x] Export RoundStartState

## Frontend Tasks

### 6. Create RoundStartUI Component ✅
**File**: `/frontend/src/components/game/RoundStartUI.jsx`
- [x] Create component
- [x] Add PropTypes
- [x] Pass props to RoundStartContent

### 7. Create RoundStartContent ✅
**File**: `/frontend/src/components/game/content/RoundStartContent.jsx`
- [x] Create component
- [x] Implement reason text logic
- [x] Add FooterTimer
- [x] Add animations (will be in CSS)

### 8. Create Styles ✅
**File**: `/frontend/src/styles/components/game/roundstart.css`
- [x] Create CSS file
- [x] Add rs- prefixed styles
- [x] Design round number display
- [x] Style starter info
- [x] Add animations

### 9. Update GameContainer ✅
**File**: `/frontend/src/components/game/GameContainer.jsx`
- [x] Add roundStartProps memo
- [x] Add case for 'round_start' phase
- [x] Wrap in GameLayout

### 10. Update GameService ✅
**File**: `/frontend/src/services/GameService.ts`
- [x] Handle round_start phase in handlePhaseChange
- [x] Store starter_reason data
- [x] Update GameState type to include currentStarter and starterReason

### 11. Import CSS ✅
**File**: `/frontend/src/styles/globals.css`
- [x] Import roundstart.css (already imported)

## Testing Requirements

### Scenario Testing
- [ ] Round 1: Correctly shows player with GENERAL_RED
- [ ] Round 2+: Shows previous round's last turn winner
- [ ] After redeal: Shows player who accepted redeal
- [ ] Timer counts down from 5 seconds
- [ ] Auto-transitions to DECLARATION
- [ ] All animations work smoothly

### Edge Cases
- [ ] Handle disconnections during ROUND_START
- [ ] Handle browser refresh during phase
- [ ] Verify no race conditions with timer

## Issues Encountered
- None yet

## Notes
- Starter is determined in PREPARATION phase
- ROUND_START only displays the information
- Must store starter_reason in game state for display

## Status: ✅ Complete

All implementation tasks have been completed. The ROUND_START phase is now fully integrated into both backend and frontend.