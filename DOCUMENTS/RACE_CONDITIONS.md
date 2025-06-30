# Race Conditions Analysis (commit 8ca1ca8)

**Date**: 2025-06-30  
**Branch**: event-driven  
**Analysis Target**: Timer-based race conditions in polling architecture

## 🚨 Critical Race Condition Patterns

### 1. Polling vs Timer Completion Race

**Location**: ScoringState transition logic  
**Evidence**: Lines 550-571 in log.txt

```
🔍 SCORING_TRANSITION_DEBUG: Checking transition conditions:
  📊 scores_calculated: True
  ⏰ display_delay_complete: False  ← POLLING EVERY 100ms
  🏁 game_complete: False
🔍 SCORING_TRANSITION_DEBUG: Not ready - display delay not complete
... (repeated ~15 times) ...
⏰ SCORING_DELAY_DEBUG: 7-second delay complete - setting display_delay_complete = True  ← TIMER COMPLETES
🔍 SCORING_TRANSITION_DEBUG: Checking transition conditions:
  📊 scores_calculated: True  
  ⏰ display_delay_complete: True  ← NEXT POLL DETECTS CHANGE
  🏁 game_complete: False
🔍 SCORING_TRANSITION_DEBUG: Ready to transition to PREPARATION
```

**Problem**: 
- Polling loop checks every 100ms
- Timer sets flag asynchronously  
- **Up to 100ms delay** between timer completion and state transition
- **Race condition**: What if multiple timers complete simultaneously?

### 2. Multiple Concurrent Timers Race

**Identified Timers**:
1. **Main Polling**: `asyncio.sleep(0.1)` - every 100ms
2. **Turn Display**: `asyncio.sleep(7.0)` - turn completion delay  
3. **Scoring Display**: `asyncio.sleep(7.0)` - scoring display delay

**Race Scenario**:
```
Time 0: Turn completes → 7s timer starts
Time 6: Scoring starts → 7s timer starts  
Time 7: Turn timer completes → tries to start next turn
Time 13: Scoring timer completes → tries to start next round
```

**Conflict**: Both timers trying to change state simultaneously

### 3. Action Processing vs Polling Race

**Location**: Bot action processing  
**Evidence**: Lines 72-151 in log.txt

```
🔍 ACTION_QUEUE_DEBUG: Dequeued action: play_pieces from Bot 2
🔍 ACTION_QUEUE_DEBUG: Dequeued action: play_pieces from Bot 2  ← DUPLICATE ACTION
🔍 STATE_MACHINE_DEBUG: Processing 2 actions  ← PROCESSING CONCURRENTLY
...
🔍 STATE_MACHINE_DEBUG: Processing action: play_pieces from Bot 2
Not Bot 2's turn - expected None  ← RACE: State changed between actions
Invalid action: GameAction(player_name='Bot 2', ...)
❌ STATE_MACHINE_DEBUG: Action rejected: play_pieces from Bot 2
```

**Problem**:
- Actions queued faster than polling can process
- State changes between action validation and execution
- **Duplicate actions** processed due to bot race conditions

### 4. State Transition vs Cleanup Race

**Location**: Turn completion processing  
**Evidence**: Lines 153-169 in log.txt

```
🔄 STATE_MACHINE_DEBUG: Attempting transition from GamePhase.TURN to GamePhase.SCORING
🚪 STATE_MACHINE_DEBUG: Exiting current state: <TurnState>
🏁 TURN_COMPLETION_DEBUG: Starting turn completion processing  ← CLEANUP RUNNING
...
🏁 TURN_COMPLETION_DEBUG: Removing 1 pieces from Andy  ← MODIFYING GAME STATE
🏁 TURN_COMPLETION_DEBUG: Removing 1 pieces from Bot 2
...
🎯 STATE_MACHINE_DEBUG: Phase updated: GamePhase.TURN -> GamePhase.SCORING
🎯 STATE_MACHINE_DEBUG: Entering new state: <ScoringState>
```

**Problem**:
- State cleanup happens during transition
- New state can read inconsistent game state
- **Race condition**: Cleanup vs new state initialization

## 🔄 Async Task Lifecycle Issues

### 1. Detached Timer Tasks

**Code Pattern Found**:
```python
# In scoring_state.py:93
asyncio.create_task(self._start_display_delay())
```

**Issues**:
- Task created but no reference stored
- **No cleanup** when state transitions
- Timer can complete after state already changed
- **Memory leak**: Orphaned tasks

### 2. Overlapping State Phases

**Sequence Identified**:
```
1. TurnState: Turn completes → starts 7s timer
2. TurnState: Transitions to ScoringState  
3. ScoringState: Starts its own 7s timer
4. TurnState timer: Still running in background
5. Both timers: Can complete and try to change state
```

**Result**: Conflicting state change attempts

### 3. Bot Manager Race Conditions

**Evidence**: Lines 70-71, 142-143 in log.txt
```
🔔 BOT_MANAGER_DEBUG: Received event 'action_accepted' for room unknown  ← WRONG ROOM
❌ BOT_MANAGER_DEBUG: Room unknown not found in active games: []
```

**Problem**:
- Bot manager events processed asynchronously
- State machine room_id not properly set
- **Lost events** due to timing issues

## 📊 Timing Analysis

### Polling Frequency Impact
- **Main Loop**: 10 polls/second (100ms interval)
- **State Checks**: `check_transition_conditions()` called 10x/second
- **Timer Resolution**: Up to 100ms delay for timer detection
- **Wasted Cycles**: Continuous checking even when no changes

### Timer Overlap Windows
```
Turn Timer:    |-------- 7s --------|
Scoring Timer:      |-------- 7s --------|
Overlap:            |-- ~1s conflict --|
```

**Risk Window**: ~1 second where both timers active

### Action Queue Backlog
```
Bot Action Rate: ~2 actions/second
Processing Rate: 10 checks/second  
Queue Buildup: Possible during rapid bot play
```

## 🎯 Critical Fix Requirements

### 1. Eliminate Polling Loop
**Current**: Continuous `while` loop with `asyncio.sleep(0.1)`  
**Target**: Event-driven processing only

### 2. Remove Timer Dependencies  
**Current**: State logic waits for `asyncio.sleep()` completion  
**Target**: Immediate state transitions, display delays separate

### 3. Proper Async Task Management
**Current**: Detached `asyncio.create_task()` calls  
**Target**: Managed task lifecycle with cleanup

### 4. Sequential State Processing
**Current**: Concurrent action processing causing races  
**Target**: Serialized state changes with proper locking

## 🚨 Identified Race Condition Types

### Type 1: Timer vs Polling Race
- **Frequency**: Every state transition with display delay
- **Impact**: Up to 100ms delay in state changes
- **Fix**: Remove polling, use immediate event triggers

### Type 2: Multiple Timer Race  
- **Frequency**: When phases overlap (turn→scoring)
- **Impact**: Conflicting state change attempts
- **Fix**: Cancel previous timers on state transition

### Type 3: Action Processing Race
- **Frequency**: During rapid bot play
- **Impact**: Invalid actions, duplicate processing
- **Fix**: Serialize action processing

### Type 4: State Cleanup Race
- **Frequency**: Every state transition  
- **Impact**: Inconsistent game state
- **Fix**: Atomic state transitions

## 🔧 Immediate Actions Required

1. **Document all async task creation points**
2. **Map state transition dependencies** 
3. **Identify proper event triggers for each transition**
4. **Design async task cleanup patterns**

---

**Next Steps**:
1. ✅ Phase 1.2 - Document race conditions
2. ⏳ Phase 1.3 - Analyze current event flow  
3. ⏳ Phase 2.1 - Define event triggers