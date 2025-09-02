# Room Cleanup Test Plan

## Test Objectives

Verify that:
1. Rooms with only disconnected players (in grace period) are properly cleaned up
2. Grace period functionality remains intact
3. No regression in existing room cleanup behavior

## Pre-Test Setup

1. **Enable Debug Logging**:
   - Room cleanup logs: `🧹 [ROOM_DEBUG]`
   - Grace period logs: `🕐 [GRACE_PERIOD]`
   - Player count logs: `👥 [ROOM_DEBUG]`

2. **Key Timings**:
   - Grace period: 5 seconds
   - Room cleanup check: Every 5 seconds
   - Room cleanup timeout: 60 seconds (default)

## Test Scenarios

### Test 1: Single Player Disconnect → Room Cleanup

**Steps**:
1. Create room with 1 human player
2. Start game (add 3 bots)
3. Human player disconnects
4. Wait and observe

**Expected Timeline**:
- T+0s: Player disconnects, grace period starts
- T+0s: Room marked for cleanup (0 active humans)
- T+5s: Bot takeover activates
- T+60s: Room cleaned up and deleted

**Verification**:
- Check logs for "0 active humans, 1 in grace period, 3 bots"
- Confirm "Room marked for cleanup"
- Verify room deletion after timeout

### Test 2: All Humans Disconnect → Room Cleanup

**Steps**:
1. Create room with 2 human players
2. Start game (add 2 bots)
3. Both humans disconnect (staggered)
4. Wait and observe

**Expected Timeline**:
- T+0s: First player disconnects
- T+0s: Room NOT marked (1 active human remains)
- T+10s: Second player disconnects
- T+10s: Room marked for cleanup (0 active humans)
- T+15s: Both players become bots
- T+70s: Room cleaned up

**Verification**:
- Room only marked after LAST human disconnects
- Grace periods work independently
- Room cleaned up after timeout

### Test 3: Reconnect Within Grace → No Cleanup

**Steps**:
1. Create room with 1 human player
2. Start game (add 3 bots)
3. Human disconnects
4. Human reconnects within 3 seconds
5. Continue playing

**Expected**:
- Room marked for cleanup on disconnect
- Cleanup cancelled on reconnect
- Game continues normally
- Room persists

**Verification**:
- Check "Cleanup cancelled" log
- Verify room not deleted
- Player regains control

### Test 4: Mixed Bot/Human Room

**Steps**:
1. Create room with 2 humans
2. Start game (add 2 bots)
3. One human leaves permanently
4. Remaining human disconnects/reconnects
5. Remaining human leaves

**Expected**:
- Room persists while any human active
- Grace period only for disconnected players
- Cleanup only after last human gone

### Test 5: Pre-Game Room Cleanup

**Steps**:
1. Create room with 1 human
2. Do NOT start game
3. Human leaves room
4. Observe cleanup

**Expected**:
- Immediate room deletion (no game state)
- No grace period (not in-game)

## Automated Test Script

```python
async def test_room_cleanup_with_grace_period():
    """Test that rooms are cleaned up when all players are in grace period"""
    
    # Create room and start game
    room_id = await create_test_room()
    await add_player(room_id, "TestPlayer")
    await add_bots(room_id, 3)
    await start_game(room_id)
    
    # Disconnect player
    await disconnect_player(room_id, "TestPlayer")
    
    # Check room state immediately
    room = await get_room(room_id)
    assert room.cleanup_scheduled == True
    assert room.has_any_human_players() == False
    
    # Wait for cleanup timeout
    await asyncio.sleep(65)
    
    # Verify room deleted
    room = await get_room(room_id)
    assert room is None
```

## Manual Test Checklist

- [ ] Single player disconnect → cleanup works
- [ ] Multiple player disconnect → cleanup after last
- [ ] Reconnect within grace → cleanup cancelled  
- [ ] Bot-only room → immediate cleanup
- [ ] Pre-game leave → immediate deletion
- [ ] Grace period timing accurate (5s)
- [ ] Cleanup timeout accurate (60s)
- [ ] No memory leaks or hanging rooms

## Success Criteria

1. All rooms with only grace-period players are cleaned up
2. Grace period functionality unchanged
3. No false positive cleanups
4. Performance acceptable (cleanup within 5s of eligibility)

## Regression Testing

Verify these still work:
- Normal game completion → room cleanup
- Host migration when host leaves
- Bot games continue during cleanup period
- Lobby updates when rooms cleaned up