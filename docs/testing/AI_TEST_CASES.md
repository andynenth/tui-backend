# AI Test Cases for Bot Takeover Bug

This document contains detailed test cases for verifying the bot takeover data collection system.

## Test Case Categories

### 1. Basic Functionality Tests
- Verify event collection is working
- Ensure all event types are captured
- Validate debug endpoints return data

### 2. Disconnection Scenarios
- Player disconnects during their turn
- Player disconnects during bot's turn
- Multiple players disconnect simultaneously

### 3. Reconnection Scenarios
- Reconnect within grace period
- Reconnect after bot takeover
- Failed reconnection attempts

### 4. Edge Cases
- Server restart during game
- Network timeout scenarios
- Concurrent disconnections

---

## Detailed Test Cases

### Test Case 1: Basic Disconnection During Player's Turn

**Objective**: Verify complete event flow when player disconnects during their turn

**Prerequisites**:
- Game in TURN phase
- It's the human player's turn
- Player has valid moves available

**Steps**:
1. Navigate to game and wait for player's turn
2. Close browser to simulate disconnection
3. Wait 6 seconds for grace period expiration
4. Verify events captured
5. Reconnect and verify control release

**Expected Events**:
```json
[
  {
    "event_type": "player_disconnected",
    "player_id": "TestPlayer",
    "game_context": {
      "current_phase": "TURN",
      "is_players_turn": true
    }
  },
  {
    "event_type": "bot_takeover_scheduled",
    "player_id": "TestPlayer",
    "grace_period_seconds": 5
  },
  {
    "event_type": "bot_takeover_activated",
    "player_id": "TestPlayer",
    "duration_waited": 5.0
  },
  {
    "event_type": "bot_action",
    "player_name": "TestPlayer",
    "action_type": "play",
    "is_bot": true
  }
]
```

**Verification Commands**:
```bash
# Check disconnection event
curl -s "http://localhost:5050/api/debug/events/$ROOM_ID?event_type=player_disconnected" | jq

# Verify bot takeover sequence
curl -s "http://localhost:5050/api/debug/connection-timeline/$ROOM_ID?player_name=TestPlayer" | jq
```

---

### Test Case 2: Reconnection Within Grace Period

**Objective**: Verify bot takeover cancellation when player reconnects quickly

**Prerequisites**:
- Player has disconnected
- Bot takeover scheduled but not activated

**Steps**:
1. Disconnect during player's turn
2. Wait 3 seconds (within 5-second grace period)
3. Reconnect to game
4. Verify bot takeover was cancelled
5. Make a move as human player

**Expected Events**:
```json
[
  {
    "event_type": "player_disconnected",
    "player_id": "TestPlayer"
  },
  {
    "event_type": "bot_takeover_scheduled",
    "player_id": "TestPlayer"
  },
  {
    "event_type": "player_reconnected",
    "player_id": "TestPlayer",
    "was_in_grace_period": true
  },
  {
    "event_type": "bot_takeover_cancelled",
    "player_id": "TestPlayer",
    "reason": "player_reconnected"
  },
  {
    "event_type": "human_action",
    "player_name": "TestPlayer",
    "is_bot": false
  }
]
```

---

### Test Case 3: Reconnection After Bot Takeover

**Objective**: Verify control release when player reconnects after bot activation

**Prerequisites**:
- Bot has taken control of player
- Game is still active

**Steps**:
1. Disconnect and wait for bot takeover (6+ seconds)
2. Let bot make at least one move
3. Reconnect to game
4. Verify control is released
5. Make a human move

**Expected Events**:
```json
[
  {
    "event_type": "bot_takeover_activated",
    "player_id": "TestPlayer"
  },
  {
    "event_type": "bot_action",
    "player_name": "TestPlayer",
    "is_bot": true
  },
  {
    "event_type": "player_reconnected",
    "player_id": "TestPlayer"
  },
  {
    "event_type": "bot_control_released",
    "player_id": "TestPlayer",
    "bot_actions_taken": 1
  },
  {
    "event_type": "human_action",
    "player_name": "TestPlayer",
    "is_bot": false
  }
]
```

---

### Test Case 4: Multiple Disconnect/Reconnect Cycles

**Objective**: Verify system handles repeated disconnections correctly

**Steps**:
1. Disconnect and wait for bot takeover
2. Reconnect and make human move
3. Disconnect again immediately
4. Wait for second bot takeover
5. Verify both cycles recorded correctly

**Verification**:
```bash
# Should show 2 complete cycles
curl -s "http://localhost:5050/api/debug/bot-control-analysis/$ROOM_ID" | jq '.player_analysis.TestPlayer'
```

---

### Test Case 5: Human Action During Bot Control

**Objective**: Verify human actions are blocked during bot control

**Prerequisites**:
- Bot has control of player
- Player attempts to reconnect and play

**Steps**:
1. Let bot take control
2. Reconnect but before control release
3. Attempt to make a move immediately
4. Verify action was blocked
5. Wait for control release
6. Retry move and verify success

**Expected Events**:
```json
[
  {
    "event_type": "action_blocked",
    "player_name": "TestPlayer",
    "reason": "bot_has_control",
    "attempted_action": "play"
  },
  {
    "event_type": "bot_control_released",
    "player_id": "TestPlayer"
  },
  {
    "event_type": "human_action",
    "player_name": "TestPlayer",
    "is_bot": false
  }
]
```

---

### Test Case 6: Connection Lost vs Disconnection

**Objective**: Differentiate between clean disconnect and connection loss

**Steps**:
1. Simulate network timeout (no close frame)
2. Verify CONNECTION_LOST event
3. Compare with clean disconnect event

**Expected Difference**:
- `connection_lost`: Network failure, no close frame
- `player_disconnected`: Clean WebSocket close

---

### Test Case 7: Server Restart During Game

**Objective**: Verify reconnection after server restart

**Steps**:
1. During active game, restart server
2. Player attempts to reconnect
3. Verify appropriate error events
4. Check game state recovery

**Expected Events**:
```json
[
  {
    "event_type": "player_reconnected_failed",
    "player_id": "TestPlayer",
    "reason": "room_not_found"
  }
]
```

---

## Test Execution Checklist

For each test case:

- [ ] Clear previous test data
- [ ] Start with fresh room
- [ ] Document room ID and player name
- [ ] Execute steps precisely
- [ ] Capture all events
- [ ] Verify expected vs actual
- [ ] Document any deviations
- [ ] Save logs for analysis

## Event Verification Matrix

| Event Type | Test Cases | Critical |
|------------|------------|----------|
| player_disconnected | 1,2,3,4,5,6 | ✅ |
| bot_takeover_scheduled | 1,2,3,4,5 | ✅ |
| bot_takeover_activated | 1,3,4,5 | ✅ |
| bot_takeover_cancelled | 2 | ✅ |
| player_reconnected | 2,3,4,5 | ✅ |
| bot_control_released | 3,4,5 | ✅ |
| human_action | 1,2,3,4,5 | ✅ |
| bot_action | 1,3,4,5 | ✅ |
| action_blocked | 5 | ✅ |
| connection_lost | 6 | ⚠️ |
| player_reconnected_failed | 7 | ⚠️ |

## Success Criteria

Each test case passes when:

1. **All expected events are captured** in correct order
2. **Event data contains required fields** with valid values
3. **Debug endpoints return consistent data**
4. **No errors in server logs** during test execution
5. **Game state remains playable** after test

## Failure Investigation

If a test fails:

1. **Check server logs** for errors or exceptions
2. **Query all events** for the room to see what was captured
3. **Verify WebSocket messages** in browser console
4. **Check debug endpoints** for additional context
5. **Review code changes** that might affect the test

## Automated Test Verification

Use this script to verify test results:

```bash
#!/bin/bash
ROOM_ID=$1
PLAYER_NAME=$2

echo "=== Test Verification for Room $ROOM_ID ==="

# Check key events
for event in player_disconnected bot_takeover_scheduled bot_takeover_activated; do
    COUNT=$(curl -s "http://localhost:5050/api/debug/events/$ROOM_ID?event_type=$event" | jq '.total_events')
    echo "$event: $COUNT events"
done

# Check timeline
echo -e "\n=== Connection Timeline ==="
curl -s "http://localhost:5050/api/debug/connection-timeline/$ROOM_ID?player_name=$PLAYER_NAME" | \
    jq '.timeline_events'

# Check bot analysis
echo -e "\n=== Bot Control Analysis ==="
curl -s "http://localhost:5050/api/debug/bot-control-analysis/$ROOM_ID" | \
    jq ".player_analysis.$PLAYER_NAME"
```

## Notes

- Grace period is hardcoded to 5 seconds
- Bot actions should be clearly distinguishable from human actions
- All timestamps should be consistent and sequential
- Event storage should be resilient to server issues
