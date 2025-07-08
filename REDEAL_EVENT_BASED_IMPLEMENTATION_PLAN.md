# Redeal Event-Based Implementation Plan (Revised)

## Executive Summary

This document provides a detailed plan to convert the redeal decision system from polling-based to event-based, following the enterprise architecture patterns established in declaration and turn phases. After completing the bot manager cleanup, we have a clear understanding of how to implement this consistently.

## Current State vs Target State

### Current State (Polling-Based)
```
Weak hands detected → Batch notify all → Bots process sequentially → Poll every 0.5s for completion
```
- Uses direct events: `"weak_hands_found"`, `"redeal_decision_needed"`, `"simultaneous_redeal_decisions"`
- Bot manager has separate handlers for each event
- State machine polls `check_transition_conditions()` every 0.5s

### Target State (Event-Based)
```
Weak hands detected → Update phase data → Each decision triggers next → Immediate transition when done
```
- Uses ONLY `"phase_change"` events via enterprise architecture
- All handling goes through: `handle_event` → `_handle_enterprise_phase_change` → `_handle_redeal_decision_phase`
- Same pattern as declaration and turn phases
- No polling - direct transition when all decisions received

## Implementation Tasks

### Phase 1: Bot Manager Integration

#### Task 1.1: Remove Legacy Event Handlers
**File:** `backend/engine/bot_manager.py`
- [ ] In `handle_event()` method, remove these handlers:
  - `"weak_hands_found"` handler (line ~198-199)
  - `"redeal_decision_needed"` handler (line ~200-202)
  - `"simultaneous_redeal_decisions"` handler (line ~203-205)
- [ ] These will be replaced by enterprise phase_change handling

#### Task 1.2: Add Preparation Phase to Enterprise Handler
**File:** `backend/engine/bot_manager.py`
- [ ] In `_handle_enterprise_phase_change()`, add new section after turn handling:
```python
elif phase == "preparation":
    # Handle redeal decisions through phase data
    weak_players_awaiting = phase_data.get("weak_players_awaiting", set())
    if weak_players_awaiting:
        await self._handle_redeal_decision_phase(phase_data)
```
- [ ] This integrates preparation into the enterprise pattern
- [ ] Note: ALL phases go through handle_event → _handle_enterprise_phase_change

#### Task 1.3: Create New Redeal Handler Method
**File:** `backend/engine/bot_manager.py`
- [ ] Create `_handle_redeal_decision_phase()` method
- [ ] Follow exact pattern from `_handle_turn_play_phase()`:
  - Get phase data
  - Find first bot that hasn't decided
  - Apply 0.5-1.5s delay
  - Call `_bot_redeal_decision()`
  - Process only one bot at a time

#### Task 1.4: Remove Old Handler Methods
**File:** `backend/engine/bot_manager.py`
- [ ] Delete these entire methods (they use old patterns):
  - `_handle_weak_hands()` 
  - `_handle_redeal_decision()`
  - `_handle_simultaneous_redeal_decisions()`
- [ ] These are replaced by the new `_handle_redeal_decision_phase()` method

### Phase 2: State Machine Updates

#### Task 2.1: Add Direct Transition Logic
**File:** `backend/engine/state_machine/states/preparation_state.py`
- [ ] In `_handle_redeal_decision()`, after recording decision
- [ ] Inside the `if self._all_weak_decisions_received()` block
- [ ] After `result = await self._process_all_decisions()`
- [ ] Add check: if no weak players remain, call `await self.state_machine._transition_to(GamePhase.DECLARATION)`

#### Task 2.2: Add Race Condition Protection
**File:** `backend/engine/state_machine/states/preparation_state.py`
- [ ] At start of `_handle_redeal_decision()`, inside `_decision_lock`
- [ ] Add phase check: `if self.state_machine.current_phase != GamePhase.PREPARATION: return error`
- [ ] This prevents late decisions after phase change

#### Task 2.3: Simplify Transition Checking
**File:** `backend/engine/state_machine/states/preparation_state.py`
- [ ] In `check_transition_conditions()`, remove the polling logic
- [ ] Remove the check for `self._all_weak_decisions_received()`
- [ ] Keep only: initial deal check and no weak players check
- [ ] Add comment explaining redeal decisions trigger transitions directly

### Phase 3: Phase Data Management

#### Task 3.1: Update Weak Hands Notification
**File:** `backend/engine/state_machine/states/preparation_state.py`
- [ ] In `_notify_weak_hands()`, ensure phase data includes:
  - `weak_players` list
  - `weak_players_awaiting` set
  - `redeal_decisions` dict
- [ ] This data drives the bot manager's decisions

#### Task 3.2: Update Decision Broadcasting
**File:** `backend/engine/state_machine/states/preparation_state.py`
- [ ] In `_broadcast_decision_update()`, ensure it updates:
  - `weak_players_awaiting` (remove decided player)
  - `redeal_decisions` (add new decision)
- [ ] Each update triggers enterprise phase_change event

#### Task 3.3: Remove Manual Bot Trigger
**File:** `backend/engine/state_machine/states/preparation_state.py`
- [ ] In `_deal_cards()`, locate `_trigger_bot_redeal_decisions()` call
- [ ] Remove this call - enterprise architecture handles it automatically
- [ ] Optionally remove the entire `_trigger_bot_redeal_decisions()` method if not used elsewhere

### Phase 4: Cleanup and Testing

#### Task 4.1: Remove Unused Code
- [ ] Search for any remaining references to `"simultaneous_redeal_decisions"` event
- [ ] Remove any unused imports related to batch processing
- [ ] Clean up any debug prints specific to polling

#### Task 4.2: Update Comments and Documentation
- [ ] Update method docstrings to reflect event-based approach
- [ ] Add comments explaining the enterprise pattern
- [ ] Update any inline comments that reference polling

#### Task 4.3: Create Test Scenarios
- [ ] Test 1: Single bot with weak hand (immediate decision and transition)
- [ ] Test 2: Multiple bots with weak hands (sequential decisions)
- [ ] Test 3: Mix of humans and bots (proper ordering)
- [ ] Test 4: All decline scenario (proper starter selection)
- [ ] Test 5: Redeal creates new weak hands (stay in preparation)

## Implementation Order

1. **Start with Bot Manager** (Tasks 1.1-1.4)
   - Remove old handlers first
   - Add new enterprise handler
   - Test that bots still receive notifications

2. **Update State Machine** (Tasks 2.1-2.3)
   - Add transition logic
   - Add safety checks
   - Simplify polling code

3. **Ensure Phase Data Flows** (Tasks 3.1-3.3)
   - Update broadcasting
   - Remove manual triggers
   - Verify data consistency

4. **Clean and Test** (Tasks 4.1-4.3)
   - Remove dead code
   - Update documentation
   - Run comprehensive tests

## Success Criteria

- [ ] No polling logs in preparation phase (no "Checking transition conditions" every 0.5s)
- [ ] Immediate transition after last redeal decision
- [ ] Bot delays remain at 0.5-1.5s per decision
- [ ] All existing game mechanics preserved
- [ ] Code follows enterprise architecture patterns

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Race condition on last decision | Use `_decision_lock` and phase check |
| Double transition | Check phase before transitioning |
| Bot doesn't get triggered | Ensure phase data updates include all needed fields |
| Timeout breaks | Keep timeout monitoring unchanged |

## Code Examples

### Example: New Bot Handler
```python
async def _handle_redeal_decision_phase(self, phase_data: dict):
    """Handle bot redeal decisions one at a time"""
    weak_players_awaiting = phase_data.get("weak_players_awaiting", set())
    redeal_decisions = phase_data.get("redeal_decisions", {})
    
    game_state = self._get_game_state()
    
    for player_name in weak_players_awaiting:
        if player_name in redeal_decisions:
            continue
            
        player = next((p for p in game_state.players if p.name == player_name), None)
        if player and player.is_bot:
            delay = random.uniform(0.5, 1.5)
            await asyncio.sleep(delay)
            await self._bot_redeal_decision(player)
            break  # One at a time
```

### Example: Direct Transition
```python
if self._all_weak_decisions_received():
    self._processing_decisions = True
    try:
        result = await self._process_all_decisions()
        
        # NEW: Direct transition
        if not self.weak_players:
            await self.state_machine._transition_to(GamePhase.DECLARATION)
        
        return result
    finally:
        self._processing_decisions = False
```

## Notes

- This implementation completes the migration to enterprise architecture
- All phases will use the same event-driven pattern
- No more polling anywhere in the game flow
- Maintains the "simultaneous" nature while processing sequentially