# Redeal Event-Based Implementation Plan

## Executive Summary

This document analyzes the current interaction patterns between bots/humans and the backend for declaration, turn play, and redeal decision phases. Based on this analysis, it provides a clear implementation plan to standardize the redeal decision flow to use event-based patterns consistent with other game phases.

## Current Implementation Analysis

### 1. Declaration Phase (Event-Driven)

**Flow:**
```
Human/Bot declares → State updates current_declarer → Enterprise broadcasts → Bot manager responds → Next bot declares
```

**Key Characteristics:**
- **Strictly sequential**: One player at a time
- **Event-driven chain**: Each declaration triggers the next
- **No polling**: Direct state → event → action flow
- **State tracking**: `current_declarer` in phase data
- **Bot timing**: 0.5-1.5s delay before declaration

**Code Flow (declaration_state.py):**
```python
async def _handle_declaration(self, action: GameAction):
    # Update state
    await self.update_phase_data({
        'current_declarer': next_declarer
    })
    # Enterprise broadcasts automatically
    # Bot manager receives phase_change event
    # Next bot declares if applicable
```

### 2. Turn Play Phase (Event-Driven)

**Flow:**
```
Human/Bot plays → State updates current_player → Enterprise broadcasts → Bot manager responds → Next bot plays
```

**Key Characteristics:**
- **Identical to declaration**: Same sequential pattern
- **Event-driven chain**: Each play triggers the next
- **No polling**: Direct state → event → action flow
- **State tracking**: `current_player` in phase data
- **Bot timing**: 0.5-1.5s delay before playing

**Code Flow (turn_state.py):**
```python
async def _handle_play_pieces(self, action: GameAction):
    # Update state
    await self.update_phase_data({
        'current_player': next_player
    })
    # Enterprise broadcasts automatically
    # Bot manager receives phase_change event
    # Next bot plays if applicable
```

### 3. Redeal Decision Phase (Polling-Based)

**Flow:**
```
Weak hands detected → Notify all weak players → Bot manager handles bots → State polls for completion
```

**Key Characteristics:**
- **Simultaneous conceptually**: Multiple players decide at once
- **Polling for completion**: State machine checks every 0.5s
- **Batch notification**: All weak players notified together
- **No inherent order**: Unlike declaration/turn
- **Bot timing**: Sequential processing with 0.5-1.5s delays

**Code Flow (preparation_state.py):**
```python
async def _handle_redeal_decision(self, action: GameAction):
    # Record decision
    self.redeal_decisions[player_name] = accept
    
    # Check if all decided (but don't transition)
    if self._all_weak_decisions_received():
        result = await self._process_all_decisions()
        
# Separate polling in check_transition_conditions():
if self._all_weak_decisions_received():
    return GamePhase.DECLARATION
```

## Key Differences

| Aspect | Declaration/Turn | Redeal |
|--------|-----------------|--------|
| **Trigger Pattern** | Each action triggers next | Batch notification, then wait |
| **Completion Check** | Natural (last player) | Polling every 0.5s |
| **State Transition** | Immediate when done | Delayed by polling interval |
| **Player Order** | Strict sequence | No order (simultaneous) |
| **State Updates** | current_declarer/player | weak_players_awaiting set |

## Implementation Plan: Event-Based Redeal

### Goal
Convert redeal decisions from polling-based to event-driven, matching declaration/turn patterns while preserving the "simultaneous decision" nature.

### Design Principles

1. **Immediate Transition**: When all decisions received, transition immediately (no polling delay)
2. **Preserve Simultaneous Nature**: Multiple players can still decide in any order
3. **Maintain Bot Timing**: Keep 0.5-1.5s delays for realistic behavior
4. **Enterprise Architecture**: Use existing automatic broadcasting

### Implementation Steps

#### Step 1: Update Bot Manager Event Handling

**File:** `backend/engine/bot_manager.py`

The bot manager needs to handle redeal decisions in an event-driven way, similar to declarations and turn plays.

```python
async def handle_event(self, event: str, data: dict):
    # ... existing code ...
    
    # REMOVE or MODIFY:
    elif event == "simultaneous_redeal_decisions":
        # This batch processing approach doesn't fit event-driven pattern
        await self._handle_simultaneous_redeal_decisions(data)
    
    # ADD NEW:
    elif event == "phase_change" and data.get("phase") == "preparation":
        # Handle redeal decisions similar to declaration/turn
        phase_data = data.get("phase_data", {})
        if phase_data.get("weak_players_awaiting"):
            await self._handle_redeal_decision_phase(data)
```

Add new method for event-driven redeal handling:

```python
async def _handle_redeal_decision_phase(self, data: dict):
    """Handle bot redeal decisions in event-driven manner"""
    phase_data = data.get("phase_data", {})
    weak_players_awaiting = phase_data.get("weak_players_awaiting", [])
    redeal_decisions = phase_data.get("redeal_decisions", {})
    
    # Find next bot that needs to decide
    game_state = self._get_game_state()
    for player_name in weak_players_awaiting:
        player = next((p for p in game_state.players if p.name == player_name), None)
        if player and player.is_bot:
            # Bot decides with delay
            delay = random.uniform(0.5, 1.5)
            await asyncio.sleep(delay)
            await self._bot_redeal_decision(player)
            break  # Only process one bot at a time
```

#### Step 2: Modify `_handle_redeal_decision()` to Trigger Transition

**File:** `backend/engine/state_machine/states/preparation_state.py`

```python
async def _handle_redeal_decision(self, action: GameAction) -> Dict[str, Any]:
    async with self._decision_lock:
        # ... existing decision recording logic ...
        
        # Check if all decided
        if self._all_weak_decisions_received():
            self._processing_decisions = True
            try:
                result = await self._process_all_decisions()
                
                # NEW: Check if ready to transition
                if not self.weak_players:  # No new weak hands after redeal
                    # Directly trigger transition instead of waiting for poll
                    await self.state_machine._transition_to(GamePhase.DECLARATION)
                    
                return result
            finally:
                self._processing_decisions = False
    
    # ... existing broadcast logic ...
```

#### Step 3: Simplify `check_transition_conditions()`

**File:** `backend/engine/state_machine/states/preparation_state.py`

```python
async def check_transition_conditions(self) -> Optional[GamePhase]:
    # Only check initial conditions, not redeal decisions
    if not self.initial_deal_complete:
        return None
    
    # Immediate transition if no weak players
    if not self.weak_players:
        return GamePhase.DECLARATION
    
    # Redeal decisions now handled directly in _handle_redeal_decision
    # No polling needed here
    return None
```

#### Step 4: Update `_process_all_decisions()` for Direct Transition

**File:** `backend/engine/state_machine/states/preparation_state.py`

```python
async def _process_all_decisions(self) -> Dict[str, Any]:
    first_accepter = self._get_first_accepter_by_play_order()
    
    if first_accepter:
        # ... existing redeal logic ...
        
        # Execute redeal
        await self._deal_cards()
        
        # Check result
        if self.weak_players:
            # New weak hands - stay in preparation
            return {
                "success": True,
                "redeal": True,
                "new_weak_hands": True
            }
        else:
            # No weak hands - will transition via _handle_redeal_decision
            return {
                "success": True,
                "redeal": True,
                "complete": True
            }
    else:
        # All declined - will transition via _handle_redeal_decision
        starter = self._determine_starter()
        game = self.state_machine.game
        game.current_player = starter
        game.round_starter = starter
        
        return {
            "success": True,
            "redeal": False,
            "starter": starter
        }
```

#### Step 5: Remove Batch Notification System

**File:** `backend/engine/state_machine/states/preparation_state.py`

Remove or modify `_trigger_bot_redeal_decisions()` since we'll use event-driven approach:

```python
# Remove the batch notification call from _deal_cards():
# await self._trigger_bot_redeal_decisions()

# Instead, ensure phase data includes weak_players_awaiting for bot manager
await self.update_phase_data({
    'weak_players': list(self.weak_players),
    'weak_players_awaiting': list(self.weak_players_awaiting),
    # ... other data
})
```

### Testing Plan

1. **Single Bot Weak Hand**: Verify immediate transition after bot decides
2. **Multiple Bots Weak**: Verify transition after last bot decides
3. **Human + Bot Mix**: Verify transition after all decide (any order)
4. **Race Condition**: Two decisions arriving simultaneously
5. **Timeout Scenario**: Verify timeout still forces decisions

### Benefits of Event-Based Approach

1. **Consistency**: All phases use same event-driven pattern
2. **Performance**: No 0.5s polling delay after last decision
3. **Simplicity**: Remove polling logic from transition checks
4. **Maintainability**: Single pattern for all game phases

### Migration Risks & Mitigation

| Risk | Mitigation |
|------|------------|
| Race conditions | Use existing `_decision_lock` |
| Double transitions | Check current phase before transition |
| Timeout handling | Keep timeout monitor task unchanged |
| State corruption | Transaction-like pattern in `_process_all_decisions` |

### Rollback Plan

If issues arise, revert by:
1. Remove direct transition from `_handle_redeal_decision`
2. Restore polling logic in `check_transition_conditions`
3. No data migration needed - only behavior change

## Conclusion

Converting redeal decisions to event-based flow will:
- Standardize all game phases to use consistent patterns
- Improve responsiveness (no polling delay)
- Simplify the codebase
- Maintain all existing game mechanics

The implementation preserves the "simultaneous decision" nature while adopting the proven event-driven pattern from declaration and turn phases.