# Bot Takeover Grace Period Implementation Plan

## Current System Analysis

### How Disconnection Works (ws.py lines 108-113)
1. Human player disconnects
2. `is_connected` → False
3. `disconnect_time` → recorded
4. **`is_bot` → True (IMMEDIATE bot takeover)**
5. Bot starts making decisions right away

### How Reconnection Works (ws.py lines 753-801)
1. Player reconnects via `client_ready` event
2. System restores `is_bot` from `original_is_bot`
3. `is_connected` → True
4. `disconnect_time` → None
5. Bot control removed, human regains control

### Bot Manager Behavior
- Bot manager checks `is_bot` flag to decide if it should act
- Has delays for actions (0.1-1s) but NO grace period for takeover
- Acts immediately when `is_bot = True`

## Proposed Solution: 5-Second Grace Period

### Key Requirements
1. **Don't break reconnection** - Must preserve ability to reconnect and regain control
2. **Don't break bot logic** - Bot must still take over after grace period
3. **Handle edge cases** - Multiple disconnects, game state changes, etc.
4. **Clear feedback** - Players must know about grace period

### Implementation Approach

#### Option A: Deferred Bot Flag (RECOMMENDED)
- Keep `is_bot = False` during grace period
- Add new field `pending_bot_takeover` with timestamp
- Bot manager checks both conditions
- After 5s, set `is_bot = True`

**Pros:**
- Minimal changes to existing logic
- Clear separation of concerns
- Easy to test and debug

**Cons:**
- Need to update bot manager logic

#### Option B: Bot Flag with Grace Check
- Set `is_bot = True` immediately (current behavior)
- Add `bot_takeover_time` field
- Bot manager checks if grace period expired

**Pros:**
- Less change to disconnect logic
- Bot flag semantics unchanged

**Cons:**
- More complex bot manager logic
- Harder to reason about state

### Detailed Implementation Steps (Option A)

1. **Update Player Model** (`backend/engine/player.py`)
   ```python
   pending_bot_takeover: Optional[datetime] = None
   bot_takeover_scheduled: bool = False
   ```

2. **Modify Disconnect Handler** (`backend/api/routes/ws.py`)
   ```python
   # Instead of: player.is_bot = True
   # Do:
   player.pending_bot_takeover = datetime.now() + timedelta(seconds=5)
   player.bot_takeover_scheduled = True
   # Keep is_bot = False during grace period
   ```

3. **Add Grace Period Task** (`backend/api/routes/ws.py`)
   ```python
   # Schedule task to activate bot after 5 seconds
   asyncio.create_task(activate_bot_after_grace(room_id, player_name))
   ```

4. **Update Bot Manager** (`backend/engine/bot_manager.py`)
   ```python
   # Check if bot should act
   if player.is_bot or (player.bot_takeover_scheduled and 
                       datetime.now() >= player.pending_bot_takeover):
       # Bot can act
   ```

5. **Handle Reconnection** (`backend/api/routes/ws.py`)
   ```python
   # Clear pending takeover on reconnect
   player.pending_bot_takeover = None
   player.bot_takeover_scheduled = False
   ```

6. **Broadcast Grace Period Status**
   ```python
   "player_disconnected": {
       "grace_period_seconds": 5,
       "bot_takeover_at": timestamp
   }
   ```

### Test Plan

1. **Basic Grace Period Test**
   - Player disconnects
   - Verify bot doesn't act for 5 seconds
   - Verify bot acts after 5 seconds

2. **Reconnection During Grace Test**
   - Player disconnects
   - Player reconnects within 3 seconds
   - Verify bot never takes over
   - Verify player has full control

3. **Reconnection After Grace Test**
   - Player disconnects
   - Wait 6 seconds (bot takes over)
   - Player reconnects
   - Verify bot relinquishes control

4. **Multiple Disconnect Test**
   - Player disconnects/reconnects multiple times
   - Verify grace period resets properly
   - Verify no zombie bot tasks

5. **Game State Changes Test**
   - Player disconnects during their turn
   - Verify turn doesn't hang
   - Verify bot plays after grace period

6. **Edge Cases**
   - Room closure during grace period
   - Game end during grace period
   - Host migration during grace period

### Rollback Plan
If issues arise:
1. Remove grace period logic
2. Revert to immediate bot takeover
3. All changes are isolated and reversible

### Success Metrics
- No broken reconnections
- Bot takes over after exactly 5 seconds
- No hanging game states
- Clear player communication