# Current vs Desired Event Flow Analysis

**Date**: 2025-06-30  
**Branch**: event-driven  
**Analysis Target**: Event flow patterns in polling vs event-driven architecture

## 🔄 Current Event Flow (Polling-Based)

### User Action Flow
```
1. Frontend User Input
   ↓
2. WebSocket Message → Backend API
   ↓  
3. GameAction Created
   ↓
4. action_queue.add_action(action) → QUEUED
   ↓
5. **POLLING DELAY** (up to 100ms)
   ↓
6. _process_loop() → process_pending_actions()
   ↓
7. current_state.handle_action(action)
   ↓
8. State Logic Processing
   ↓
9. **POLLING DELAY** (up to 100ms) 
   ↓
10. check_transition_conditions() → POLLED
    ↓
11. State Transition (if conditions met)
    ↓
12. update_phase_data() → Auto-broadcast
    ↓
13. WebSocket → Frontend Update
```

**🔴 Current Problems:**
- **2x Polling Delays**: Up to 200ms total latency
- **Continuous Checking**: 10 polls/second even when idle
- **Timer Dependencies**: State transitions wait for asyncio.sleep()
- **Race Conditions**: Multiple paths to same state

### Bot Action Flow
```
1. Bot Manager Event (phase_change, player_played)
   ↓
2. Bot Decision Logic
   ↓
3. GameAction Queued → action_queue.add_action()
   ↓
4. **SAME POLLING DELAYS** as user actions
   ↓
5. Potential Race: Multiple bot actions queued faster than processing
```

### Timer-Based Flow
```
1. State Transition (e.g., Turn → Scoring)
   ↓
2. asyncio.create_task(timer_function) → DETACHED TASK
   ↓
3. asyncio.sleep(7.0) → 7 SECOND DELAY
   ↓
4. Set flag (e.g., display_delay_complete = True)
   ↓
5. **POLLING DELAY** (up to 100ms)
   ↓
6. check_transition_conditions() detects flag
   ↓
7. Next State Transition
```

**🔴 Timer Problems:**
- **Detached Tasks**: No cleanup on state exit
- **Race Conditions**: Multiple timers can overlap
- **State Logic Coupling**: Business logic depends on display timing

## 🎯 Desired Event Flow (Event-Driven)

### User Action Flow (Target)
```
1. Frontend User Input
   ↓
2. WebSocket Message → Backend API
   ↓
3. GameAction Created
   ↓
4. **IMMEDIATE** event_processor.handle_action(action)
   ↓
5. State Logic Processing
   ↓
6. **IMMEDIATE** trigger_transition_if_ready()
   ↓
7. State Transition (if conditions met)
   ↓
8. **IMMEDIATE** update_phase_data() → Auto-broadcast
   ↓
9. WebSocket → Frontend Update
```

**🟢 Target Benefits:**
- **Zero Polling Delays**: Immediate processing
- **Event-Driven**: Only processes when events occur
- **No Timer Dependencies**: Immediate state logic
- **Race-Free**: Serialized event processing

### Event-Driven State Transitions (Target)
```
1. Event Trigger (turn_complete, all_declared, etc.)
   ↓
2. **IMMEDIATE** validate_transition_conditions()
   ↓
3. **IMMEDIATE** state_transition()
   ↓
4. **IMMEDIATE** frontend_notification()
   ↓
5. **SEPARATE** display_timing (if needed for UI)
```

### Display vs Logic Separation (Target)
```
LOGIC FLOW (Immediate):
User Action → State Change → Frontend Update

DISPLAY FLOW (Parallel):
State Change → Display Phase → UI Timing → (No Logic Impact)
```

## 📊 Current Event Types Analysis

### Events Currently Processed
1. **User Actions**:
   - `play_pieces` - Player piece selection
   - `declare` - Declaration value
   - `redeal_request` - Weak hand redeal

2. **System Events**:  
   - `turn_complete` - All players played
   - `round_complete` - All hands empty
   - `game_complete` - Win condition met

3. **Bot Events**:
   - `phase_change` - State machine broadcasts
   - `player_played` - Trigger next bot
   - `action_accepted/rejected` - Bot validation

4. **Timer Events** (❌ PROBLEMATIC):
   - `display_delay_complete` - Timer flags
   - `auto_advance_timer` - Display timing

### Events Missing (Event-Driven Needs)
1. **Immediate Triggers**:
   - `all_players_declared` → Start turn immediately
   - `turn_winner_determined` → Start results immediately  
   - `scoring_calculated` → Start next round immediately

2. **State Entry/Exit**:
   - `state_entered` → Setup complete
   - `state_exiting` → Cleanup tasks
   - `transition_ready` → Immediate transition

## 🏗️ Event-Driven Architecture Design

### Core Components Needed

#### 1. Event Processor
```python
class EventProcessor:
    async def handle_event(self, event: GameEvent) -> None:
        # Immediate processing, no polling
        pass
    
    async def trigger_transition(self, trigger: str) -> None:
        # Immediate state change validation
        pass
```

#### 2. Event Types
```python
class GameEvent:
    event_type: str  # "user_action", "system_event", "state_trigger"
    trigger: str     # "turn_complete", "all_declared", etc.
    data: Dict[str, Any]
    immediate: bool  # True for logic events, False for display
```

#### 3. Transition Triggers
```python
class TransitionTrigger:
    source_state: GamePhase
    target_state: GamePhase  
    trigger_condition: str
    validator: Callable
```

### Event Flow Redesign

#### State Machine Core (Target)
```python
class GameStateMachine:
    async def handle_event(self, event: GameEvent) -> None:
        # NO POLLING LOOP
        result = await self.current_state.process_event(event)
        
        if result.triggers_transition:
            await self.trigger_transition(result.target_state, result.reason)
        
        # Auto-broadcast handled by enterprise architecture
```

#### State Classes (Target)
```python
class TurnState(GameState):
    async def process_event(self, event: GameEvent) -> EventResult:
        if event.trigger == "piece_played":
            # Process immediately
            result = await self._handle_play_pieces(event.data)
            
            # Check immediate transition conditions
            if self._all_players_played():
                return EventResult(
                    triggers_transition=True,
                    target_state=GamePhase.TURN_RESULTS,
                    reason="Turn completed"
                )
        
        return EventResult(triggers_transition=False)
```

## 🚨 Critical Changes Required

### 1. Remove Polling Loop
**Current**: `while self.is_running: ... await asyncio.sleep(0.1)`  
**Target**: Event-driven processor only

### 2. Eliminate Timer Dependencies  
**Current**: State logic waits for `display_delay_complete`  
**Target**: Immediate state transitions, separate display phases

### 3. Immediate Event Processing
**Current**: Queue → Poll → Process → Poll → Transition  
**Target**: Event → Process → Transition (immediate)

### 4. Managed Async Tasks
**Current**: `asyncio.create_task()` detached  
**Target**: Managed lifecycle with proper cleanup

## 📈 Performance Comparison

### Current (Polling):
- **CPU Usage**: Continuous background polling
- **Latency**: 100-200ms delays  
- **Memory**: Growing task references
- **Race Conditions**: High risk

### Target (Event-Driven):
- **CPU Usage**: Only when events occur
- **Latency**: <10ms immediate processing
- **Memory**: Cleaned up task lifecycle  
- **Race Conditions**: Eliminated via serialization

---

**Phase 1 Complete**: ✅ Architecture Analysis Done  
**Next Steps**: Begin Phase 2 - Event-Driven Design