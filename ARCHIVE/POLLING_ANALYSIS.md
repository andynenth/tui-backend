# Polling Architecture Analysis (commit 8ca1ca8)

**Date**: 2025-06-30  
**Branch**: event-driven  
**Analysis Target**: Current polling-based state machine

## 🚨 Main Polling Loop Identified

### Location: `engine/state_machine/game_state_machine.py:93-119`

```python
async def _process_loop(self):
    """Main processing loop for queued actions"""
    print(f"🔍 STATE_MACHINE_DEBUG: Process loop started, is_running: {self.is_running}")
    loop_count = 0
    while self.is_running:  # ← CONTINUOUS POLLING LOOP
        try:
            loop_count += 1
            if loop_count % 50 == 0:  # Log every 5 seconds
                print(f"🔍 STATE_MACHINE_DEBUG: Process loop iteration {loop_count}")
            
            # Process any pending actions
            await self.process_pending_actions()
            
            # Check for phase transitions ← POLLING POINT
            if self.current_state:
                next_phase = await self.current_state.check_transition_conditions()  # ← POLLING CALL
                if next_phase:
                    await self._transition_to(next_phase)
            
            # Small delay to prevent busy waiting ← POLLING DELAY
            await asyncio.sleep(0.1)  # ← 100ms polling interval
            
        except Exception as e:
            print(f"❌ STATE_MACHINE_DEBUG: Error in process loop: {e}")
            logger.error(f"Error in process loop: {e}", exc_info=True)
```

**🔴 CRITICAL ISSUES:**
- **Continuous Loop**: Runs forever while `is_running=True`
- **Polling Every 100ms**: `asyncio.sleep(0.1)` creates 10 polls per second
- **CPU Waste**: Constant checking even when no state changes needed
- **Race Conditions**: Polling can conflict with action processing

## 📍 check_transition_conditions() Implementations

### 1. TurnState (`engine/state_machine/states/turn_state.py:101-112`)
```python
async def check_transition_conditions(self) -> Optional[GamePhase]:
    """Check if ready to transition to scoring phase"""
    game = self.state_machine.game
    
    # Check if all players have empty hands (main condition for scoring)
    if hasattr(game, 'players') and game.players:
        all_hands_empty = all(len(player.hand) == 0 for player in game.players)
        if all_hands_empty:
            self.logger.info("🏁 All hands empty - transitioning to scoring")
            return GamePhase.SCORING
    
    return None
```
**Issue**: Checked every 100ms instead of when turn completes

### 2. ScoringState (`engine/state_machine/states/scoring_state.py:160-182`)
```python
async def check_transition_conditions(self) -> Optional[GamePhase]:
    """Check if ready to transition to next phase"""
    if not self.scores_calculated:
        return None
    
    # Wait for display delay to complete (give users time to see scoring)
    if not self.display_delay_complete:  # ← TIMER DEPENDENCY
        return None
    
    if self.game_complete:
        return None
    
    return GamePhase.PREPARATION
```
**Issue**: Depends on timer flag `display_delay_complete` set by asyncio.sleep

### 3. PreparationState (`engine/state_machine/states/preparation_state.py`)
```python
async def check_transition_conditions(self) -> Optional[GamePhase]:
    """Check if ready to transition to Declaration phase"""
    # Transition when:
    # 1. Initial deal done AND no weak players, OR
    # 2. All weak players have made redeal decisions
    
    if not self.initial_deal_complete:
        return None
    
    if not self.weak_players:
        return GamePhase.DECLARATION
    
    # Check if all weak players made decisions
    if len(self.redeal_decisions) >= len(self.weak_players):
        return GamePhase.DECLARATION
    
    return None
```
**Issue**: Polled instead of triggered when decisions complete

### 4. DeclarationState (`engine/state_machine/states/declaration_state.py`)
```python
async def check_transition_conditions(self) -> Optional[GamePhase]:
    order = self.phase_data['declaration_order']
    declarations = self.phase_data['declarations']
    
    if len(declarations) >= len(order):
        return GamePhase.TURN
    return None
```
**Issue**: Checked every 100ms instead of when declaration made

## ⏰ asyncio.sleep() Usage Analysis

### 1. Main Polling Loop - `game_state_machine.py:113`
```python
await asyncio.sleep(0.1)  # Small delay to prevent busy waiting
```
**Purpose**: Polling interval  
**Issue**: Creates 10 polls per second unnecessarily

### 2. Turn Completion Delay - `turn_state.py:559`
```python
await asyncio.sleep(7.0)  # Auto-start next turn after 7 second delay
turn_started = await self.start_next_turn_if_needed()
```
**Purpose**: Give users time to see turn results  
**Issue**: State logic depends on timer, can cause race conditions

### 3. Scoring Display Delay - `scoring_state.py:365`
```python
await asyncio.sleep(7.0)  # 7 second delay for users to see scores
self.display_delay_complete = True
```
**Purpose**: Give users time to see scores  
**Issue**: State transition depends on timer completion

## 🔄 Event Flow Problems

### Current Flow (Polling-Based):
```
User Action → Action Queue → Polling Loop (100ms) → check_transition_conditions() → State Change
```

**Problems:**
- **Delay**: Up to 100ms delay before state change detected
- **Waste**: Continuous checking even when no changes
- **Race Conditions**: Timer-based delays can conflict

### Desired Flow (Event-Driven):
```
User Action → Immediate Event → Direct State Change → Frontend Notification
```

## 📊 Performance Impact

### Current Polling Cost:
- **Frequency**: 10 polls per second continuously
- **CPU Usage**: Constant background processing
- **Memory**: Growing loop counters and state checks
- **Latency**: Up to 100ms delay for state transitions

### Timer Conflicts:
- Multiple 7-second timers can run simultaneously
- Turn completion timer + Scoring display timer
- Race conditions when timers complete out of order

## 🎯 Conversion Requirements

### Phase 1 - Remove Polling Loop:
1. **Replace** continuous `while self.is_running` with event-driven processing
2. **Remove** `asyncio.sleep(0.1)` polling delay
3. **Replace** `check_transition_conditions()` polling with event triggers

### Phase 2 - Remove Timer Dependencies:
1. **Separate** display delays from state logic
2. **Convert** `display_delay_complete` flags to display-only phases
3. **Implement** immediate state transitions

### Phase 3 - Event-Driven Triggers:
1. **User Actions**: Immediate state change validation
2. **Turn Completion**: Direct transition to TURN_RESULTS
3. **Scoring Complete**: Direct transition to next round
4. **All Declarations**: Direct transition to TURN

## 🚨 Critical Anti-Patterns Found

1. **Polling Loop**: Continuous while loop with sleep
2. **Timer Dependencies**: State logic waiting for asyncio.sleep
3. **Delayed Transitions**: State changes not immediate
4. **Resource Waste**: Unnecessary continuous checking
5. **Race Conditions**: Multiple timers running concurrently

---

**Next Steps**: 
1. ✅ Complete Phase 1.1 - Document polling loops
2. ⏳ Phase 1.2 - Document race conditions  
3. ⏳ Phase 1.3 - Analyze current event flow