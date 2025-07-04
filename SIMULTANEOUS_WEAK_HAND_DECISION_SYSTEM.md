# Simultaneous Weak Hand Decision System

## Table of Contents
1. [Current System Analysis](#current-system-analysis)
2. [Problem Identification](#problem-identification)
3. [New System Design](#new-system-design)
4. [Implementation Plan](#implementation-plan)
5. [Risk Prevention Solutions](#risk-prevention-solutions)
6. [Testing Scenarios](#testing-scenarios)
7. [Migration Strategy](#migration-strategy)

## Current System Analysis

### Sequential Decision Flow
The current implementation uses a sequential decision process where weak hand players make redeal decisions one at a time:

```python
# Current state variables in PreparationState
self.current_weak_player: Optional[str] = None  # Single player deciding
self.pending_weak_players: List[str] = []       # Queue of players waiting
self.redeal_decisions: Dict[str, bool] = {}     # Decisions made so far
```

### Current Flow Example
```
Players: ["Andy", "Bot 2", "Bot 3", "Bot 4"]
Weak hands detected: ["Andy", "Bot 3"]

Step 1: Andy decides (others wait)
  - If Andy accepts → immediate redeal for everyone
  - If Andy declines → Bot 3's turn to decide

Step 2: Bot 3 decides (only if Andy declined)
  - If Bot 3 accepts → immediate redeal for everyone
  - If Bot 3 declines → continue with current hands
```

### Problems with Current System
1. **Slow gameplay**: Players must wait for each decision sequentially
2. **Information advantage**: Later players know earlier decisions
3. **First-accepter bias**: First player to accept triggers immediate redeal
4. **Poor UX**: Non-deciding players stuck in waiting state

## Problem Identification

### Log Analysis Results
From the analyzed log file, we identified:

1. **Missing Enterprise Broadcasting**
   ```python
   # Line 396-400 in preparation_state.py
   async def _notify_weak_hands(self) -> None:
       """Notify about weak hands found"""
       pass  # ❌ Empty implementation
   ```

2. **Bot Manager Triggered for Humans**
   ```
   🔧 PREP_STATE_DEBUG: Triggering bot manager for player: Andy
   🔄 BOT_HANDLER_DEBUG: Handling redeal decision needed
   ```

3. **Infinite Loop**
   ```
   🔍 PREP_STATE_DEBUG: Waiting for more redeal decisions (0/1)
   # Repeats indefinitely because human player UI never triggered
   ```

### Root Causes
1. Frontend never receives weak hand data to show redeal UI
2. Bot manager incorrectly triggered for human players
3. No timeout mechanism for stuck decisions

## New System Design

### Simultaneous Decision Architecture
All weak hand players make decisions at the same time, with the game proceeding once all decisions are collected.

### New State Variables
```python
# Proposed state variables in PreparationState
self.weak_players_awaiting: Set[str] = set()    # All players who need to decide
self.redeal_decisions: Dict[str, bool] = {}     # player_name -> accept/decline
self.decision_start_time: Optional[float] = None
self.decision_timeout: float = 30.0              # 30 second timeout
self._decision_lock = asyncio.Lock()             # Prevent race conditions
```

### Game Flow Examples

#### Setup
```
Players: ["Andy", "Bot 2", "Bot 3", "Bot 4"]
Weak hands detected: ["Andy", "Bot 3"]
All weak players decide simultaneously
```

#### Case 1: Multiple Accept
```
Andy: Accept ✅
Bot 3: Accept ✅

Result: Redeal with Andy as starter (first in play order)
```

#### Case 2: Mixed Decisions
```
Andy: Decline ❌
Bot 3: Accept ✅

Result: Redeal with Bot 3 as starter
```

#### Case 3: All Decline
```
Andy: Decline ❌
Bot 3: Decline ❌

Result: Continue with current hands, normal starter determination
```

### Starter Determination Logic
```python
def _get_first_accepter_by_play_order(self) -> Optional[str]:
    """Get first player in play order who accepted redeal"""
    game = self.state_machine.game
    play_order = game.get_player_order_from(game.current_player or game.players[0].name)
    
    for player in play_order:
        player_name = player.name if hasattr(player, 'name') else str(player)
        if self.redeal_decisions.get(player_name) == True:
            return player_name
    return None
```

## Implementation Plan

### Phase 1: Backend State Management

#### 1.1 Update PreparationState Initialization
```python
def __init__(self, state_machine):
    super().__init__(state_machine)
    # ... existing code ...
    
    # Remove old variables
    # self.current_weak_player: Optional[str] = None
    # self.pending_weak_players: List[str] = []
    
    # Add new variables
    self.weak_players_awaiting: Set[str] = set()
    self.decision_start_time: Optional[float] = None
    self.decision_timeout: float = 30.0
    self._decision_lock = asyncio.Lock()
    self._processing_decisions: bool = False
```

#### 1.2 Implement Enterprise Broadcasting
```python
async def _notify_weak_hands(self) -> None:
    """Notify about weak hands found using enterprise architecture"""
    game = self.state_machine.game
    
    # Prepare data for frontend
    weak_hand_data = {
        'weak_players': list(self.weak_players),
        'weak_players_awaiting': list(self.weak_players_awaiting),
        'decisions_received': len(self.redeal_decisions),
        'decisions_needed': len(self.weak_players),
        'redeal_multiplier': getattr(game, 'redeal_multiplier', 1),
        'simultaneous_mode': True,
        'decision_timeout': self.decision_timeout
    }
    
    # Use enterprise broadcasting
    await self.update_phase_data(
        weak_hand_data,
        f"Weak hands detected: {list(self.weak_players)} - awaiting simultaneous decisions"
    )
```

#### 1.3 Unified Decision Handler
```python
async def _handle_redeal_decision(self, action: GameAction) -> Dict[str, Any]:
    """Handle redeal decision with race condition prevention"""
    async with self._decision_lock:
        # Prevent double processing
        if self._processing_decisions:
            return {"success": False, "error": "Processing in progress"}
        
        player_name = action.player_name
        accept = action.payload.get("accept", False)
        
        # Validate player
        if player_name not in self.weak_players:
            return {"success": False, "error": "Not a weak player"}
        
        if player_name in self.redeal_decisions:
            return {"success": False, "error": "Already decided"}
        
        # Record decision
        self.redeal_decisions[player_name] = accept
        self.weak_players_awaiting.discard(player_name)
        
        # Check if all decided
        if self._all_weak_decisions_received():
            self._processing_decisions = True
            try:
                result = await self._process_all_decisions()
            finally:
                self._processing_decisions = False
            return result
    
    # Broadcast update (outside lock)
    await self._broadcast_decision_update(player_name, accept)
    return {
        "success": True,
        "decisions_received": len(self.redeal_decisions),
        "decisions_needed": len(self.weak_players)
    }
```

#### 1.4 Process All Decisions
```python
async def _process_all_decisions(self) -> Dict[str, Any]:
    """Process all collected decisions"""
    first_accepter = self._get_first_accepter_by_play_order()
    
    if first_accepter:
        # Execute redeal
        self.redeal_requester = first_accepter
        game = self.state_machine.game
        
        # Update game state
        old_multiplier = game.redeal_multiplier
        game.redeal_multiplier = old_multiplier + 1
        game.current_player = first_accepter
        game.round_starter = first_accepter
        
        self.logger.info(f"♻️ Redeal accepted by {first_accepter} - new starter")
        self.logger.info(f"📈 Multiplier: {old_multiplier}x → {game.redeal_multiplier}x")
        
        # Reset for new deal
        self.weak_players.clear()
        self.redeal_decisions.clear()
        self.weak_players_awaiting.clear()
        self.decision_start_time = None
        
        # Execute redeal
        await self._deal_cards()
        
        return {
            "success": True,
            "redeal": True,
            "new_starter": first_accepter,
            "multiplier": game.redeal_multiplier
        }
    else:
        # All declined - determine starter normally
        self.logger.info("✅ All weak players declined - proceeding with current hands")
        
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

### Phase 2: Bot Manager Updates

#### 2.1 Fix Bot Trigger Logic
```python
async def _trigger_bot_redeal_decisions(self) -> None:
    """Trigger bot manager only for bot weak players"""
    from ...bot_manager import BotManager
    bot_manager = BotManager()
    room_id = getattr(self.state_machine, 'room_id', 'unknown')
    
    # Collect all bot weak players
    game = self.state_machine.game
    bot_weak_players = []
    
    for player_name in self.weak_players:
        player = next((p for p in game.players if p.name == player_name), None)
        if player and getattr(player, 'is_bot', False):
            bot_weak_players.append(player_name)
            print(f"🤖 PREP_STATE_DEBUG: Bot weak player found: {player_name}")
        else:
            print(f"👤 PREP_STATE_DEBUG: Human weak player: {player_name} - waiting for UI")
    
    # Only trigger if there are bot weak players
    if bot_weak_players:
        await bot_manager.handle_game_event(room_id, "simultaneous_redeal_decisions", {
            "bot_weak_players": bot_weak_players,
            "weak_players": list(self.weak_players)
        })
```

#### 2.2 Bot Manager Simultaneous Handler
```python
# In bot_manager.py
async def handle_event(self, event: str, data: dict):
    """Process game events and trigger bot actions"""
    # ... existing code ...
    
    elif event == "simultaneous_redeal_decisions":
        await self._handle_simultaneous_redeal_decisions(data)

async def _handle_simultaneous_redeal_decisions(self, data: dict):
    """Handle multiple bot redeal decisions with realistic timing"""
    bot_weak_players = data.get("bot_weak_players", [])
    
    # Create staggered delays for natural feel
    bot_tasks = []
    for i, bot_name in enumerate(bot_weak_players):
        # Vary delay: 1-3 seconds base + 0.5s per position
        delay = random.uniform(1.0, 3.0) + (i * 0.5)
        
        task = asyncio.create_task(
            self._delayed_bot_redeal_decision(bot_name, delay)
        )
        bot_tasks.append(task)
    
    # Don't wait - let them decide asynchronously
    asyncio.gather(*bot_tasks, return_exceptions=True)

async def _delayed_bot_redeal_decision(self, bot_name: str, delay: float):
    """Make bot redeal decision after realistic delay"""
    await asyncio.sleep(delay)
    
    # Smart decision logic
    decline_probability = self._calculate_redeal_decline_probability(bot_name)
    should_decline = random.random() < decline_probability
    
    # Send decision
    action = GameAction(
        player_name=bot_name,
        action_type=ActionType.REDEAL_RESPONSE,
        payload={"accept": not should_decline},
        is_bot=True
    )
    
    await self.state_machine.handle_action(action)
```

### Phase 3: Frontend Integration

#### 3.1 Update PreparationUI Props
```javascript
// Add to PreparationUI.propTypes
simultaneousMode: PropTypes.bool,
weakPlayersAwaiting: PropTypes.arrayOf(PropTypes.string),
decisionsReceived: PropTypes.number,
decisionsNeeded: PropTypes.number,
```

#### 3.2 Add Progress Indicator
```jsx
{/* Decision Progress Indicator */}
{simultaneousMode && weakPlayers.length > 0 && (
  <div className="mb-6 bg-blue-900/20 rounded-lg p-4">
    <div className="text-center mb-3">
      <div className="text-sm text-blue-200">
        Redeal Decisions: {decisionsReceived}/{decisionsNeeded}
      </div>
    </div>
    
    <div className="flex justify-center gap-2">
      {weakPlayers.map(player => {
        const hasDecided = !weakPlayersAwaiting.includes(player);
        return (
          <div key={player} className={`
            px-4 py-2 rounded-lg text-sm font-medium
            ${hasDecided 
              ? 'bg-green-600 text-white' 
              : 'bg-yellow-600 text-yellow-100'}
          `}>
            {player} {hasDecided ? '✓' : '⏳'}
          </div>
        );
      })}
    </div>
  </div>
)}
```

#### 3.3 Update Decision UI
```jsx
{/* Show buttons to ALL weak players simultaneously */}
{isMyDecision && simultaneousMode && (
  <div className="text-center">
    <p className="text-blue-100 mb-6">
      You have a weak hand. Do you want to request a redeal?
    </p>
    <p className="text-sm text-blue-200 mb-4">
      {decisionsReceived} of {decisionsNeeded} players have decided
    </p>
    {/* Existing buttons */}
  </div>
)}
```

## Risk Prevention Solutions

### 1. Race Condition Prevention

#### Asyncio Lock Implementation
```python
# Prevents multiple decisions being processed simultaneously
async with self._decision_lock:
    # Critical section - only one thread at a time
    if player_name in self.redeal_decisions:
        return {"success": False, "error": "Already decided"}
    
    self.redeal_decisions[player_name] = accept
    # ... rest of processing
```

#### Double-Click Protection
```python
# Flag to prevent re-processing during final decision handling
if self._processing_decisions:
    return {"success": False, "error": "Processing in progress"}
```

### 2. Network Timeout Handling

#### Multi-Layer Timeout System
```python
async def _monitor_decision_timeout(self) -> None:
    """Monitor and handle decision timeouts"""
    while not self._all_weak_decisions_received():
        await asyncio.sleep(1.0)
        
        if not self.weak_players:  # Phase changed
            return
            
        elapsed = time.time() - self.decision_start_time
        
        # Warning at 20 seconds
        if elapsed > 20 and not self.warning_sent:
            await self.update_phase_data({
                'timeout_warning': True,
                'seconds_remaining': 10
            }, "10 seconds remaining for redeal decisions")
            self.warning_sent = True
        
        # Force timeout at 30 seconds
        if elapsed > self.decision_timeout:
            await self._force_timeout_decisions()
            return

async def _force_timeout_decisions(self) -> None:
    """Auto-decline for all pending decisions"""
    async with self._decision_lock:
        for player_name in list(self.weak_players_awaiting):
            if player_name not in self.redeal_decisions:
                self.redeal_decisions[player_name] = False
                self.logger.info(f"⏱️ Auto-declined for {player_name} (timeout)")
        
        await self._process_all_decisions()
```

### 3. Bot Timing Variation

#### Natural Bot Behavior
```python
def _calculate_redeal_decline_probability(self, bot_name: str) -> float:
    """Smart bot decision making"""
    game = self._get_game_state()
    base_probability = 0.7  # 70% decline by default
    
    # Adjust based on game state
    if game.redeal_multiplier >= 3:
        base_probability = 0.9  # Very likely to decline at high multipliers
    elif game.round_number == 1:
        base_probability = 0.5  # More aggressive in first round
    elif game.redeal_multiplier == 1:
        base_probability = 0.6  # Slightly more likely to accept first redeal
    
    # Add personality variation
    if "Bot 1" in bot_name:
        base_probability += 0.1  # Bot 1 is more conservative
    elif "Bot 4" in bot_name:
        base_probability -= 0.1  # Bot 4 is more aggressive
    
    return max(0.1, min(0.9, base_probability))  # Clamp between 0.1 and 0.9
```

### 4. State Consistency Enforcement

#### Enterprise Architecture Only
```python
# NEVER do direct state mutations:
# self.weak_players = set()  # ❌ WRONG

# ALWAYS use enterprise methods:
await self.update_phase_data({
    'weak_players': list(self.weak_players),
    'decisions_received': len(self.redeal_decisions)
}, "Updated weak player state")  # ✅ CORRECT
```

#### State Validation
```python
async def _validate_state_consistency(self) -> bool:
    """Ensure internal state is consistent"""
    # All decisions must be from weak players
    for player in self.redeal_decisions.keys():
        if player not in self.weak_players:
            self.logger.error(f"Invalid decision from non-weak player: {player}")
            return False
    
    # All awaiting players must be weak players
    if not self.weak_players_awaiting.issubset(self.weak_players):
        self.logger.error("Awaiting players not subset of weak players")
        return False
    
    # Decisions + awaiting should equal weak players
    decided = set(self.redeal_decisions.keys())
    if decided | self.weak_players_awaiting != self.weak_players:
        self.logger.error("Decision tracking inconsistent")
        return False
    
    return True
```

## Testing Scenarios

### Test Case 1: Two Human Weak Players
```
Setup: Andy and Bot 2 have weak hands
Expected:
- Both see decision buttons immediately
- Progress shows "0/2 decisions"
- Each decision updates progress
- Game proceeds after both decide
```

### Test Case 2: Mixed Human/Bot Weak Players
```
Setup: Andy (human) and Bot 3 have weak hands
Expected:
- Andy sees buttons immediately
- Bot 3 decides after 1-3 second delay
- Progress updates as each decides
- Proper starter determination
```

### Test Case 3: Timeout Scenario
```
Setup: Andy has weak hand, doesn't decide
Expected:
- Warning at 20 seconds
- Auto-decline at 30 seconds
- Game continues normally
```

### Test Case 4: Rapid Decisions
```
Setup: Multiple weak players click rapidly
Expected:
- Lock prevents race conditions
- All decisions recorded correctly
- No duplicate processing
```

### Test Case 5: Network Disconnection
```
Setup: Player disconnects during decision phase
Expected:
- Timeout handles missing decision
- Game continues after timeout
- Reconnecting player sees result
```

## Detailed Task Breakdown

### Backend Tasks - PreparationState

#### Task Group 1: State Variable Updates
- [ ] **Task 1.1**: Comment out `self.current_weak_player: Optional[str] = None` in `__init__`
- [ ] **Task 1.2**: Comment out `self.pending_weak_players: List[str] = []` in `__init__`
- [ ] **Task 1.3**: Add `self.weak_players_awaiting: Set[str] = set()` in `__init__`
- [ ] **Task 1.4**: Add `self.decision_start_time: Optional[float] = None` in `__init__`
- [ ] **Task 1.5**: Add `self.decision_timeout: float = 30.0` in `__init__`
- [ ] **Task 1.6**: Add `self._decision_lock = asyncio.Lock()` in `__init__`
- [ ] **Task 1.7**: Add `self._processing_decisions: bool = False` in `__init__`
- [ ] **Task 1.8**: Add `self.warning_sent: bool = False` in `__init__`
- [ ] **Task 1.9**: Add `import asyncio` at top of file
- [ ] **Task 1.10**: Add `import time` at top of file

#### Task Group 2: Helper Method Creation
- [ ] **Task 2.1**: Create `_all_weak_decisions_received(self) -> bool` method
  - Check if `set(self.redeal_decisions.keys()) == self.weak_players`
- [ ] **Task 2.2**: Create `_get_first_accepter_by_play_order(self) -> Optional[str]` method
  - Get play order using `game.get_player_order_from()`
  - Iterate through play order
  - Return first player where `self.redeal_decisions.get(player_name) == True`
- [ ] **Task 2.3**: Create `_count_acceptances(self) -> int` method
  - Return `sum(1 for decision in self.redeal_decisions.values() if decision)`
- [ ] **Task 2.4**: Create `_validate_state_consistency(self) -> bool` method
  - Check all decisions are from weak players
  - Check awaiting players are subset of weak players
  - Check decided + awaiting equals weak players

#### Task Group 3: Update _notify_weak_hands Method
- [ ] **Task 3.1**: Remove `pass` statement from `_notify_weak_hands`
- [ ] **Task 3.2**: Add `game = self.state_machine.game` to get game reference
- [ ] **Task 3.3**: Create weak_hand_data dictionary with:
  - `'weak_players': list(self.weak_players)`
  - `'weak_players_awaiting': list(self.weak_players_awaiting)`
  - `'decisions_received': len(self.redeal_decisions)`
  - `'decisions_needed': len(self.weak_players)`
  - `'redeal_multiplier': getattr(game, 'redeal_multiplier', 1)`
  - `'simultaneous_mode': True`
  - `'decision_timeout': self.decision_timeout`
- [ ] **Task 3.4**: Add `await self.update_phase_data(weak_hand_data, reason)` call

#### Task Group 4: Create _broadcast_decision_update Method
- [ ] **Task 4.1**: Create method signature `async def _broadcast_decision_update(self, player_name: str, accepted: bool) -> None:`
- [ ] **Task 4.2**: Create update data dictionary with:
  - `'player_decided': player_name`
  - `'decision': 'accept' if accepted else 'decline'`
  - `'decisions_received': len(self.redeal_decisions)`
  - `'decisions_needed': len(self.weak_players)`
  - `'weak_players_awaiting': list(self.weak_players_awaiting)`
  - `'all_decided': self._all_weak_decisions_received()`
- [ ] **Task 4.3**: Add `await self.update_phase_data(update_data, reason)` call

#### Task Group 5: Refactor _deal_cards Method
- [ ] **Task 5.1**: Find lines 142-164 (weak player handling section)
- [ ] **Task 5.2**: Remove lines setting `self.current_weak_player`
- [ ] **Task 5.3**: Remove lines creating `self.pending_weak_players` queue
- [ ] **Task 5.4**: Add `self.weak_players_awaiting = self.weak_players.copy()`
- [ ] **Task 5.5**: Add `self.decision_start_time = time.time()`
- [ ] **Task 5.6**: Add `self.warning_sent = False`
- [ ] **Task 5.7**: Update `await self._notify_weak_hands()` call to `await self._notify_all_weak_players()`
- [ ] **Task 5.8**: Create `asyncio.create_task(self._monitor_decision_timeout())` after notification

#### Task Group 6: Update _trigger_bot_redeal_decisions Method
- [ ] **Task 6.1**: Remove current logic that triggers for single player
- [ ] **Task 6.2**: Add loop to collect all bot weak players:
  ```python
  bot_weak_players = []
  for player_name in self.weak_players:
      player = next((p for p in game.players if p.name == player_name), None)
      if player and getattr(player, 'is_bot', False):
          bot_weak_players.append(player_name)
  ```
- [ ] **Task 6.3**: Add check `if bot_weak_players:` before triggering
- [ ] **Task 6.4**: Change event name to "simultaneous_redeal_decisions"
- [ ] **Task 6.5**: Update event data to include `"bot_weak_players": bot_weak_players`

#### Task Group 7: Create Unified Decision Handler
- [ ] **Task 7.1**: Remove current `_handle_redeal_accept` method
- [ ] **Task 7.2**: Remove current `_handle_redeal_decline` method
- [ ] **Task 7.3**: Create new `_handle_redeal_decision` method signature
- [ ] **Task 7.4**: Add `async with self._decision_lock:` context manager
- [ ] **Task 7.5**: Add check for `self._processing_decisions` flag
- [ ] **Task 7.6**: Extract `player_name` and `accept` from action
- [ ] **Task 7.7**: Validate player is in `self.weak_players`
- [ ] **Task 7.8**: Check player not already in `self.redeal_decisions`
- [ ] **Task 7.9**: Record decision: `self.redeal_decisions[player_name] = accept`
- [ ] **Task 7.10**: Remove player from awaiting: `self.weak_players_awaiting.discard(player_name)`
- [ ] **Task 7.11**: Check if all decided with `_all_weak_decisions_received()`
- [ ] **Task 7.12**: If all decided, set `self._processing_decisions = True`
- [ ] **Task 7.13**: Call `await self._process_all_decisions()` if all decided
- [ ] **Task 7.14**: Call `await self._broadcast_decision_update()` outside lock

#### Task Group 8: Create _process_all_decisions Method
- [ ] **Task 8.1**: Create method signature
- [ ] **Task 8.2**: Call `first_accepter = self._get_first_accepter_by_play_order()`
- [ ] **Task 8.3**: Add if/else for accepter found vs all declined
- [ ] **Task 8.4**: If accepter found:
  - Set `self.redeal_requester = first_accepter`
  - Get game reference
  - Increment `game.redeal_multiplier`
  - Set `game.current_player = first_accepter`
  - Set `game.round_starter = first_accepter`
  - Clear all weak player state
  - Call `await self._deal_cards()`
- [ ] **Task 8.5**: If all declined:
  - Call `starter = self._determine_starter()`
  - Set `game.current_player = starter`
  - Set `game.round_starter = starter`
- [ ] **Task 8.6**: Return appropriate result dictionary

#### Task Group 9: Create Timeout Monitor
- [ ] **Task 9.1**: Create `_monitor_decision_timeout` method
- [ ] **Task 9.2**: Add while loop checking `not self._all_weak_decisions_received()`
- [ ] **Task 9.3**: Add `await asyncio.sleep(1.0)` in loop
- [ ] **Task 9.4**: Check if phase changed: `if not self.weak_players: return`
- [ ] **Task 9.5**: Calculate elapsed time
- [ ] **Task 9.6**: Add warning at 20 seconds
- [ ] **Task 9.7**: Force timeout at 30 seconds
- [ ] **Task 9.8**: Create `_force_timeout_decisions` method
- [ ] **Task 9.9**: In force timeout, auto-decline all pending decisions
- [ ] **Task 9.10**: Call `_process_all_decisions` after forcing

#### Task Group 10: Update _validate_action Method
- [ ] **Task 10.1**: Update REDEAL_REQUEST validation to check `player_name in self.weak_players`
- [ ] **Task 10.2**: Remove check for `current_weak_player`
- [ ] **Task 10.3**: Check player not already in `self.redeal_decisions`

#### Task Group 11: Update _process_action Method
- [ ] **Task 11.1**: Change REDEAL_REQUEST to call `_handle_redeal_decision`
- [ ] **Task 11.2**: Change REDEAL_RESPONSE to call `_handle_redeal_decision`
- [ ] **Task 11.3**: Remove distinction between accept/decline

#### Task Group 12: Update check_transition_conditions Method
- [ ] **Task 12.1**: Remove check for `len(self.redeal_decisions) == len(self.weak_players)`
- [ ] **Task 12.2**: Replace with `if self._all_weak_decisions_received():`
- [ ] **Task 12.3**: Ensure timeout is checked in each cycle

### Backend Tasks - Bot Manager

#### Task Group 13: Add Simultaneous Decision Handler
- [ ] **Task 13.1**: In `handle_event` method, add case for "simultaneous_redeal_decisions"
- [ ] **Task 13.2**: Create `_handle_simultaneous_redeal_decisions` method
- [ ] **Task 13.3**: Extract `bot_weak_players` from event data
- [ ] **Task 13.4**: Create empty `bot_tasks` list
- [ ] **Task 13.5**: Loop through each bot weak player
- [ ] **Task 13.6**: Calculate delay: `random.uniform(1.0, 3.0) + (i * 0.5)`
- [ ] **Task 13.7**: Create task: `asyncio.create_task(self._delayed_bot_redeal_decision(bot_name, delay))`
- [ ] **Task 13.8**: Append task to bot_tasks
- [ ] **Task 13.9**: Use `asyncio.gather(*bot_tasks, return_exceptions=True)`

#### Task Group 14: Create Delayed Bot Decision Method
- [ ] **Task 14.1**: Create `_delayed_bot_redeal_decision` method
- [ ] **Task 14.2**: Add `await asyncio.sleep(delay)`
- [ ] **Task 14.3**: Create `_calculate_redeal_decline_probability` method
- [ ] **Task 14.4**: Add game state checks (multiplier, round number)
- [ ] **Task 14.5**: Add bot personality variations
- [ ] **Task 14.6**: Generate random decision based on probability
- [ ] **Task 14.7**: Create GameAction with decision
- [ ] **Task 14.8**: Call `await self.state_machine.handle_action(action)`

### Frontend Tasks

#### Task Group 15: Update PreparationUI Props
- [ ] **Task 15.1**: Add to propTypes: `simultaneousMode: PropTypes.bool`
- [ ] **Task 15.2**: Add to propTypes: `weakPlayersAwaiting: PropTypes.arrayOf(PropTypes.string)`
- [ ] **Task 15.3**: Add to propTypes: `decisionsReceived: PropTypes.number`
- [ ] **Task 15.4**: Add to propTypes: `decisionsNeeded: PropTypes.number`
- [ ] **Task 15.5**: Add defaults for new props

#### Task Group 16: Add Progress Indicator UI
- [ ] **Task 16.1**: Find location after weak hands info section (around line 156)
- [ ] **Task 16.2**: Add conditional check: `{simultaneousMode && weakPlayers.length > 0 && (`
- [ ] **Task 16.3**: Create container div with styling
- [ ] **Task 16.4**: Add text showing "Decisions: X/Y"
- [ ] **Task 16.5**: Create flex container for player status
- [ ] **Task 16.6**: Map through weakPlayers array
- [ ] **Task 16.7**: Check if player in weakPlayersAwaiting
- [ ] **Task 16.8**: Apply different styling for decided vs awaiting
- [ ] **Task 16.9**: Add checkmark or hourglass icon

#### Task Group 17: Update Decision Button Display
- [ ] **Task 17.1**: Find current `isMyDecision` check (line 166)
- [ ] **Task 17.2**: Add `&& simultaneousMode` to condition
- [ ] **Task 17.3**: Update waiting text to show multiple players
- [ ] **Task 17.4**: Add progress info to decision UI

#### Task Group 18: Update GameService Event Handlers
- [ ] **Task 18.1**: Find phase_change handler for preparation phase
- [ ] **Task 18.2**: Check for `data.simultaneous_mode`
- [ ] **Task 18.3**: Extract new fields from phase data
- [ ] **Task 18.4**: Pass new props to PreparationUI
- [ ] **Task 18.5**: Handle decision update events

### Testing Tasks

#### Task Group 19: Unit Tests
- [ ] **Task 19.1**: Test `_all_weak_decisions_received` with various states
- [ ] **Task 19.2**: Test `_get_first_accepter_by_play_order` with different orders
- [ ] **Task 19.3**: Test lock prevents concurrent decision processing
- [ ] **Task 19.4**: Test timeout triggers after 30 seconds
- [ ] **Task 19.5**: Test warning sent at 20 seconds

#### Task Group 20: Integration Tests
- [ ] **Task 20.1**: Test 2 human weak players scenario
- [ ] **Task 20.2**: Test mixed human/bot weak players
- [ ] **Task 20.3**: Test all decline scenario
- [ ] **Task 20.4**: Test network disconnection during decisions
- [ ] **Task 20.5**: Test rapid clicking doesn't cause issues

#### Task Group 21: Frontend Tests
- [ ] **Task 21.1**: Test progress indicator updates correctly
- [ ] **Task 21.2**: Test buttons shown to all weak players
- [ ] **Task 21.3**: Test non-weak players see waiting UI
- [ ] **Task 21.4**: Test decision updates received and displayed

## Migration Strategy

### Phase 1: Backend Implementation
1. Implement new preparation_state.py changes
2. Update bot_manager.py for simultaneous handling
3. Test with bots only

### Phase 2: Frontend Updates
1. Update PreparationUI component
2. Update GameService event handlers
3. Test UI with mock data

### Phase 3: Integration Testing
1. Test full flow with mixed players
2. Verify all edge cases
3. Load test with concurrent decisions

### Phase 4: Deployment
1. Feature flag for gradual rollout
2. Monitor for race conditions
3. Gather player feedback

### Rollback Plan
Keep sequential system code available behind feature flag for quick rollback if issues arise.

## Summary

This new simultaneous weak hand decision system provides:
- **Better UX**: All players engaged simultaneously
- **Faster gameplay**: No sequential waiting
- **Fair decisions**: No information advantage
- **Robust handling**: Timeouts, race prevention, state consistency

The implementation maintains enterprise architecture patterns while solving the core issues identified in the current system.