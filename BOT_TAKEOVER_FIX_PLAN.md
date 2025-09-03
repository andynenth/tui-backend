# Bot Takeover Bug Fix Plan - Data Collection Focus

## Current Data Collection Gaps

### What We Have Now
- Only 3 event types stored: `game_started`, `hands_dealt`, `round_started`
- No connection tracking whatsoever
- No bot state changes recorded
- No way to know who controlled each action (human vs bot)
- Player activity monitor only tracks CURRENT connections (lost on restart)

### What We Need for Debugging
1. **Connection Lifecycle**: When did player disconnect/reconnect?
2. **Bot State Changes**: When did bot take over? When was control released?
3. **Action Attribution**: Who made each play - human or bot?
4. **Timing Information**: Grace period tracking, delays, race conditions
5. **Failed Operations**: Why didn't bot release control?
6. **System State**: What was the game state during transitions?

## Phase 1: Comprehensive Event Tracking

### 1.1 Define All Connection Events

**File**: `backend/models/semantic_events.py`  
**Add after line 26**:

```python
# Connection lifecycle events
PLAYER_DISCONNECTED = "player_disconnected"
PLAYER_RECONNECTED = "player_reconnected"
CONNECTION_LOST = "connection_lost"  # Network failure vs intentional disconnect

# Bot control events  
BOT_TAKEOVER_SCHEDULED = "bot_takeover_scheduled"
BOT_TAKEOVER_CANCELLED = "bot_takeover_cancelled"
BOT_TAKEOVER_ACTIVATED = "bot_takeover_activated"
BOT_CONTROL_RELEASED = "bot_control_released"
BOT_CONTROL_FAILED_RELEASE = "bot_control_failed_release"

# Action attribution events
HUMAN_ACTION = "human_action"
BOT_ACTION = "bot_action"
ACTION_BLOCKED = "action_blocked"  # When human tries to act but bot has control
```

**Add to STORE_AS_IS dictionary**:
```python
# All these MUST be stored for debugging
"player_disconnected": SemanticEventType.PLAYER_DISCONNECTED,
"player_reconnected": SemanticEventType.PLAYER_RECONNECTED,
"connection_lost": SemanticEventType.CONNECTION_LOST,
"bot_takeover_scheduled": SemanticEventType.BOT_TAKEOVER_SCHEDULED,
"bot_takeover_cancelled": SemanticEventType.BOT_TAKEOVER_CANCELLED,
"bot_takeover_activated": SemanticEventType.BOT_TAKEOVER_ACTIVATED,
"bot_control_released": SemanticEventType.BOT_CONTROL_RELEASED,
"bot_control_failed_release": SemanticEventType.BOT_CONTROL_FAILED_RELEASE,
"human_action": SemanticEventType.HUMAN_ACTION,
"bot_action": SemanticEventType.BOT_ACTION,
"action_blocked": SemanticEventType.ACTION_BLOCKED,
```

### 1.2 Track Disconnection with Full Context

**File**: `backend/api/routes/ws.py`  
**Replace simple disconnection tracking (after line 122) with**:

```python
# Store comprehensive disconnection data
from backend.shared_event_store import event_store

# Capture current game state
game_context = {
    "current_phase": room.game_state_machine.get_current_phase() if room.game_state_machine else None,
    "current_player": room.game_state_machine.get_phase_data().get("current_player") if room.game_state_machine else None,
    "round_number": room.game.round_number if room.game else None,
    "turn_number": room.game.turn_number if room.game else None,
    "is_players_turn": (room.game_state_machine.get_phase_data().get("current_player") == connection.player_name) if room.game_state_machine else False
}

await event_store.store_event(
    room_id,
    "player_disconnected",
    {
        "player_name": connection.player_name,
        "timestamp": player.disconnect_time,
        "was_bot": player.is_bot,
        "grace_period_seconds": 5,
        "bot_takeover_scheduled_at": player.pending_bot_takeover.isoformat(),
        "disconnect_reason": "websocket_close",  # vs timeout, error, etc
        "game_context": game_context,
        "connection_duration_seconds": time.time() - connection.connect_time if hasattr(connection, 'connect_time') else None
    },
    player_id=connection.player_name
)

# Also store bot takeover scheduled event
await event_store.store_event(
    room_id,
    "bot_takeover_scheduled",
    {
        "player_name": connection.player_name,
        "scheduled_for": player.pending_bot_takeover.isoformat(),
        "current_time": datetime.now().isoformat(),
        "delay_seconds": 5,
        "game_context": game_context
    },
    player_id=connection.player_name
)
```

### 1.3 Track Bot Takeover with Failure Detection

**File**: `backend/api/routes/ws.py`  
**In `activate_bot_after_grace` function, enhance tracking**:

```python
# Before activation, store detailed state
pre_activation_state = {
    "player_name": player_name,
    "was_connected": player.is_connected,
    "was_bot": player.is_bot,
    "bot_takeover_scheduled": player.bot_takeover_scheduled,
    "current_phase": room.game_state_machine.get_current_phase() if room.game_state_machine else None,
    "timestamp": time.time()
}

# Store activation attempt
await event_store.store_event(
    room_id,
    "bot_takeover_activated",
    {
        "player_name": player_name,
        "activation_time": time.time(),
        "scheduled_time": player.pending_bot_takeover.timestamp() if player.pending_bot_takeover else None,
        "delay_actual": time.time() - player.disconnect_time if player.disconnect_time else None,
        "pre_state": pre_activation_state,
        "reason": "disconnect_timeout_5s"
    },
    player_id=player_name
)

# After setting is_bot = True, verify it worked
if not player.is_bot:
    # CRITICAL: Bot activation failed!
    await event_store.store_event(
        room_id,
        "bot_control_failed_release",  # Reuse for activation failure
        {
            "player_name": player_name,
            "operation": "activation",
            "error": "is_bot flag not set",
            "state": {"is_bot": player.is_bot, "is_connected": player.is_connected}
        },
        player_id=player_name
    )
```

### 1.4 Track Reconnection with Success/Failure

**File**: `backend/api/routes/ws.py`  
**Enhanced reconnection tracking (line 760+)**:

```python
# Capture state BEFORE any changes
pre_reconnect_state = {
    "is_bot": player.is_bot,
    "is_connected": player.is_connected,
    "bot_takeover_scheduled": getattr(player, 'bot_takeover_scheduled', None),
    "pending_bot_takeover": getattr(player, 'pending_bot_takeover', None),
    "disconnect_time": getattr(player, 'disconnect_time', None)
}

# Store reconnection attempt
await event_store.store_event(
    room_id,
    "player_reconnected",
    {
        "player_name": player_name,
        "timestamp": time.time(),
        "pre_state": pre_reconnect_state,
        "time_disconnected_seconds": time.time() - player.disconnect_time if player.disconnect_time else None,
        "bot_was_active": player.is_bot,
        "reconnect_method": "websocket",
        "game_context": {
            "current_phase": room.game_state_machine.get_current_phase() if room.game_state_machine else None,
            "current_player": room.game_state_machine.get_phase_data().get("current_player") if room.game_state_machine else None,
        }
    },
    player_id=player_name
)

# Clear bot flags
player.is_bot = False
player.bot_takeover_scheduled = False
player.pending_bot_takeover = None

# Verify release worked
if player.is_bot:
    # CRITICAL: Failed to release bot control!
    await event_store.store_event(
        room_id,
        "bot_control_failed_release",
        {
            "player_name": player_name,
            "timestamp": time.time(),
            "error": "is_bot still True after clearing",
            "state": {
                "is_bot": player.is_bot,
                "bot_takeover_scheduled": player.bot_takeover_scheduled
            }
        },
        player_id=player_name
    )
else:
    # Success - store release event
    await event_store.store_event(
        room_id,
        "bot_control_released",
        {
            "player_name": player_name,
            "timestamp": time.time(),
            "method": "player_reconnection",
            "post_state": {
                "is_bot": player.is_bot,
                "is_connected": player.is_connected
            }
        },
        player_id=player_name
    )
```

## Phase 2: Action Attribution Tracking

### 2.1 Track Every Game Action

**File**: `backend/engine/state_machine/core.py` or appropriate action handlers  
**Add to action processing**:

```python
async def process_action(self, action: GameAction):
    # Determine who is controlling this action
    player = self.get_player(action.player_id)
    is_bot_controlled = getattr(player, 'is_bot', False)
    
    # Store action attribution
    await event_store.store_event(
        self.room_id,
        "bot_action" if is_bot_controlled else "human_action",
        {
            "player_name": action.player_id,
            "action_type": action.action_type.value,
            "is_bot": is_bot_controlled,
            "phase": self.current_phase,
            "turn_number": self.game.turn_number if self.game else None,
            "round_number": self.game.round_number if self.game else None,
            "timestamp": time.time(),
            "action_details": action.payload
        },
        player_id=action.player_id
    )
```

### 2.2 Track Blocked Actions

**File**: `backend/api/routes/ws.py`  
**When human tries to act but bot has control**:

```python
# In event handling, before processing player actions
if event_type in ["declare", "play", "accept_redeal", "decline_redeal"]:
    player = self.get_player(player_name)
    if player and player.is_bot:
        # Human trying to act while bot has control
        await event_store.store_event(
            room_id,
            "action_blocked",
            {
                "player_name": player_name,
                "action_attempted": event_type,
                "reason": "bot_has_control",
                "is_bot": True,
                "timestamp": time.time(),
                "payload": event_data
            },
            player_id=player_name
        )
        # Still send error to user
        await websocket.send_json({
            "event": "error",
            "data": {"message": "Bot is currently controlling your player"}
        })
        continue  # Don't process the action
```

## Phase 3: Enhanced Debug Endpoints

### 3.1 Connection Timeline Endpoint

**File**: `backend/api/routes/debug.py`  
**Add comprehensive connection timeline**:

```python
@router.get("/connection-timeline/{room_id}")
async def get_connection_timeline(
    room_id: str,
    player_name: Optional[str] = Query(None, description="Filter by player name")
):
    """
    Get detailed connection timeline showing all state transitions
    """
    try:
        # Get all relevant event types
        event_types = [
            "player_disconnected", "player_reconnected", "connection_lost",
            "bot_takeover_scheduled", "bot_takeover_cancelled", 
            "bot_takeover_activated", "bot_control_released",
            "bot_control_failed_release", "human_action", "bot_action",
            "action_blocked"
        ]
        
        all_events = []
        for event_type in event_types:
            events = await debug_db_service.get_events_by_type(room_id, event_type)
            all_events.extend(events)
        
        # Filter by player if specified
        if player_name:
            all_events = [e for e in all_events if e.player_id == player_name]
        
        # Sort by timestamp
        all_events.sort(key=lambda x: x.timestamp)
        
        # Build timeline with state tracking
        timeline = []
        player_states = {}  # Track each player's state
        
        for event in all_events:
            player = event.player_id
            
            # Update tracked state
            if event.event_type == "player_disconnected":
                player_states[player] = "disconnected"
            elif event.event_type == "bot_takeover_activated":
                player_states[player] = "bot_controlled"
            elif event.event_type == "player_reconnected":
                player_states[player] = "reconnecting"
            elif event.event_type == "bot_control_released":
                player_states[player] = "human_controlled"
            
            timeline.append({
                "timestamp": event.timestamp,
                "human_time": datetime.fromtimestamp(event.timestamp).isoformat(),
                "event_type": event.event_type,
                "player": player,
                "player_state": player_states.get(player, "unknown"),
                "details": event.payload,
                "sequence": event.sequence
            })
        
        # Add time gaps
        for i in range(1, len(timeline)):
            timeline[i]["seconds_since_previous"] = timeline[i]["timestamp"] - timeline[i-1]["timestamp"]
        
        # Identify issues
        issues = []
        for event in timeline:
            if event["event_type"] == "bot_control_failed_release":
                issues.append({
                    "severity": "CRITICAL",
                    "timestamp": event["timestamp"],
                    "issue": "Failed to release bot control",
                    "player": event["player"],
                    "details": event["details"]
                })
            elif event["event_type"] == "action_blocked":
                issues.append({
                    "severity": "HIGH", 
                    "timestamp": event["timestamp"],
                    "issue": "Human action blocked by bot",
                    "player": event["player"],
                    "details": event["details"]
                })
        
        return {
            "room_id": room_id,
            "timeline_events": len(timeline),
            "timeline": timeline,
            "issues_found": issues,
            "player_states": player_states
        }
        
    except Exception as e:
        logger.error(f"Error building connection timeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### 3.2 Bot Control Analysis Endpoint

**File**: `backend/api/routes/debug.py`  
**Add bot control analysis**:

```python
@router.get("/bot-control-analysis/{room_id}")
async def analyze_bot_control(room_id: str):
    """
    Analyze bot control patterns and issues
    """
    try:
        # Get all bot-related events
        bot_events = []
        for event_type in ["bot_takeover_scheduled", "bot_takeover_activated", 
                          "bot_control_released", "bot_control_failed_release",
                          "human_action", "bot_action", "action_blocked"]:
            events = await debug_db_service.get_events_by_type(room_id, event_type)
            bot_events.extend(events)
        
        bot_events.sort(key=lambda x: x.timestamp)
        
        # Analyze patterns
        players_analysis = {}
        
        for event in bot_events:
            player = event.player_id
            if player not in players_analysis:
                players_analysis[player] = {
                    "total_disconnects": 0,
                    "total_takeovers": 0,
                    "successful_releases": 0,
                    "failed_releases": 0,
                    "human_actions": 0,
                    "bot_actions": 0,
                    "blocked_actions": 0,
                    "takeover_events": []
                }
            
            analysis = players_analysis[player]
            
            if event.event_type == "player_disconnected":
                analysis["total_disconnects"] += 1
            elif event.event_type == "bot_takeover_activated":
                analysis["total_takeovers"] += 1
                analysis["takeover_events"].append({
                    "timestamp": event.timestamp,
                    "duration": None  # Will calculate
                })
            elif event.event_type == "bot_control_released":
                analysis["successful_releases"] += 1
                # Calculate takeover duration
                if analysis["takeover_events"]:
                    last_takeover = analysis["takeover_events"][-1]
                    last_takeover["duration"] = event.timestamp - last_takeover["timestamp"]
                    last_takeover["release_method"] = event.payload.get("method", "unknown")
            elif event.event_type == "bot_control_failed_release":
                analysis["failed_releases"] += 1
            elif event.event_type == "human_action":
                analysis["human_actions"] += 1
            elif event.event_type == "bot_action":
                analysis["bot_actions"] += 1
            elif event.event_type == "action_blocked":
                analysis["blocked_actions"] += 1
        
        # Calculate summary statistics
        summary = {
            "total_players": len(players_analysis),
            "total_disconnections": sum(p["total_disconnects"] for p in players_analysis.values()),
            "total_takeovers": sum(p["total_takeovers"] for p in players_analysis.values()),
            "total_failed_releases": sum(p["failed_releases"] for p in players_analysis.values()),
            "total_blocked_actions": sum(p["blocked_actions"] for p in players_analysis.values()),
            "average_takeover_duration": None
        }
        
        # Calculate average takeover duration
        all_durations = []
        for analysis in players_analysis.values():
            for takeover in analysis["takeover_events"]:
                if takeover.get("duration"):
                    all_durations.append(takeover["duration"])
        
        if all_durations:
            summary["average_takeover_duration"] = sum(all_durations) / len(all_durations)
        
        return {
            "room_id": room_id,
            "summary": summary,
            "player_analysis": players_analysis,
            "has_issues": summary["total_failed_releases"] > 0 or summary["total_blocked_actions"] > 0
        }
        
    except Exception as e:
        logger.error(f"Error analyzing bot control: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

## Phase 4: Real-time Monitoring

### 4.1 Add Heartbeat Tracking

**File**: `backend/api/routes/ws.py`  
**Track connection health**:

```python
# In websocket handler, add periodic heartbeat
async def heartbeat_task(websocket, room_id, player_name):
    """Send heartbeat to track connection health"""
    while True:
        try:
            await asyncio.sleep(30)  # Every 30 seconds
            await event_store.store_event(
                room_id,
                "connection_heartbeat",
                {
                    "player_name": player_name,
                    "timestamp": time.time(),
                    "websocket_id": websocket._ws_id
                },
                player_id=player_name
            )
        except Exception as e:
            logger.error(f"Heartbeat failed: {e}")
            break
```

## Comprehensive Data Collection Testing Plan

### Test Setup

```bash
# Terminal 1: Monitor database writes
watch -n 0.5 'sqlite3 /Users/nrw/python/tui-project/liap-tui/data/game_events.db "SELECT event_type, COUNT(*) FROM game_events_v2 WHERE room_id=\"TEST_ROOM\" GROUP BY event_type;"'

# Terminal 2: Backend logs for event storage
docker-compose logs -f backend | grep -E "EVENT|store_event|Store"

# Terminal 3: API testing terminal
export ROOM_ID=TEST_ROOM
```

### Test Case 1: Disconnection Event Collection

**Goal**: Verify all disconnection-related events are stored with correct data

**Steps**:
1. Create room, start game, play until your turn
2. Note the exact timestamp
3. Close browser tab to disconnect

**Verification**:
```bash
# Check player_disconnected event exists
curl http://localhost:5050/api/debug/events/$ROOM_ID?event_type=player_disconnected | jq '.events[0]'

# Verify it contains:
# - player_name
# - timestamp
# - was_bot (should be false)
# - grace_period_seconds (should be 5)
# - bot_takeover_scheduled_at
# - game_context (with current_phase, current_player, is_players_turn)
# - connection_duration_seconds

# Check bot_takeover_scheduled event
curl http://localhost:5050/api/debug/events/$ROOM_ID?event_type=bot_takeover_scheduled | jq '.events[0]'

# Verify it contains:
# - scheduled_for (should be 5 seconds after disconnect)
# - game_context
```

### Test Case 2: Bot Takeover Event Collection

**Goal**: Verify bot takeover events capture complete state

**Steps**:
1. After disconnection, wait exactly 6 seconds
2. Check database for new events

**Verification**:
```bash
# Check bot_takeover_activated event
curl http://localhost:5050/api/debug/events/$ROOM_ID?event_type=bot_takeover_activated | jq '.events[0]'

# Verify it contains:
# - activation_time
# - scheduled_time
# - delay_actual (should be ~5 seconds)
# - pre_state (with was_bot=false, bot_takeover_scheduled=true)
# - reason: "disconnect_timeout_5s"

# If bot makes a move, check bot_action event
curl http://localhost:5050/api/debug/events/$ROOM_ID?event_type=bot_action | jq '.events[0]'

# Verify it contains:
# - action_type (declare/play)
# - is_bot: true
# - phase, turn_number, round_number
# - action_details
```

### Test Case 3: Reconnection Event Collection

**Goal**: Verify reconnection captures before/after state

**Steps**:
1. Reconnect after bot has taken over
2. Immediately check events

**Verification**:
```bash
# Check player_reconnected event
curl http://localhost:5050/api/debug/events/$ROOM_ID?event_type=player_reconnected | jq '.events[0]'

# Verify it contains:
# - pre_state (with is_bot=true, bot_takeover_scheduled=false)
# - time_disconnected_seconds
# - bot_was_active: true
# - game_context

# Check bot_control_released event
curl http://localhost:5050/api/debug/events/$ROOM_ID?event_type=bot_control_released | jq '.events[0]'

# Verify it contains:
# - method: "player_reconnection"
# - post_state (with is_bot=false, is_connected=true)

# Or check for failure
curl http://localhost:5050/api/debug/events/$ROOM_ID?event_type=bot_control_failed_release | jq
```

### Test Case 4: Action Attribution

**Goal**: Verify every action is tagged with who made it

**Steps**:
1. Make several moves as human
2. Let bot take over and make moves
3. Reconnect and make more moves

**Verification**:
```bash
# Count human vs bot actions
curl http://localhost:5050/api/debug/events/$ROOM_ID | jq '.events[] | select(.event_type == "human_action" or .event_type == "bot_action") | {type: .event_type, player: .player_id, action: .payload.action_type}'

# Verify timeline shows clear attribution
curl http://localhost:5050/api/debug/connection-timeline/$ROOM_ID | jq '.timeline[] | select(.event_type | contains("action")) | {time: .human_time, type: .event_type, player: .player}'
```

### Test Case 5: Blocked Action Detection

**Goal**: Verify we capture when human tries to play during bot control

**Steps**:
1. After bot takeover, try to make a move BEFORE reconnecting
2. Check for blocked action event

**Verification**:
```bash
# Check action_blocked events
curl http://localhost:5050/api/debug/events/$ROOM_ID?event_type=action_blocked | jq '.events[]'

# Verify it contains:
# - action_attempted
# - reason: "bot_has_control"
# - is_bot: true
# - payload (what they tried to do)
```

### Test Case 6: Timeline Completeness

**Goal**: Verify timeline endpoint shows complete story

**Steps**:
1. After full disconnect/takeover/reconnect cycle
2. Check timeline

**Verification**:
```bash
# Get full timeline
curl http://localhost:5050/api/debug/connection-timeline/$ROOM_ID | jq '.timeline[] | {time: .seconds_since_previous, event: .event_type, state: .player_state}'

# Expected sequence:
# 1. player_disconnected (state: disconnected)
# 2. bot_takeover_scheduled (state: disconnected)
# 3. bot_takeover_activated after ~5s (state: bot_controlled)
# 4. bot_action events (state: bot_controlled)
# 5. player_reconnected (state: reconnecting)
# 6. bot_control_released (state: human_controlled)
# 7. human_action events (state: human_controlled)

# Check for any issues detected
curl http://localhost:5050/api/debug/connection-timeline/$ROOM_ID | jq '.issues_found[]'
```

### Test Case 7: Bot Control Analysis

**Goal**: Verify analysis endpoint calculates correct statistics

**Steps**:
1. Create multiple disconnect/reconnect cycles
2. Check analysis

**Verification**:
```bash
# Get bot control analysis
curl http://localhost:5050/api/debug/bot-control-analysis/$ROOM_ID | jq

# Verify summary contains:
# - total_disconnections
# - total_takeovers
# - total_failed_releases (should be 0)
# - average_takeover_duration (should be > 5 seconds)

# Check per-player analysis
curl http://localhost:5050/api/debug/bot-control-analysis/$ROOM_ID | jq '.player_analysis'
```

### Test Case 8: Data Persistence

**Goal**: Verify events survive server restart

**Steps**:
1. Create events through gameplay
2. Restart backend: `docker-compose restart backend`
3. Check events still exist

**Verification**:
```bash
# All events should still be present
curl http://localhost:5050/api/debug/events/$ROOM_ID | jq '.total_events'

# Timeline should be complete
curl http://localhost:5050/api/debug/connection-timeline/$ROOM_ID | jq '.timeline_events'
```

### Test Case 9: Edge Cases

**Test 9.1: Grace Period Cancellation**
```bash
# Disconnect and reconnect within 3 seconds
# Should see bot_takeover_cancelled event (if implemented)
```

**Test 9.2: Multiple Rapid Disconnects**
```bash
# Disconnect/reconnect 5 times rapidly
# Each cycle should have complete events
```

**Test 9.3: Concurrent Players**
```bash
# Have 2 human players disconnect at same time
# Verify events don't interfere with each other
```

### Data Collection Checklist

For each test case, verify:

- [ ] Event exists in database
- [ ] Event has correct event_type
- [ ] Event has player_id
- [ ] Event has timestamp
- [ ] Event has all required fields per specification
- [ ] Event payload is valid JSON
- [ ] Event sequence makes logical sense
- [ ] Debug endpoints can read the event
- [ ] Timeline shows event in correct order

### Automated Test Script

Create `test_data_collection.py`:
```python
import requests
import time
import json

def test_event_exists(room_id, event_type, timeout=10):
    """Poll for event to appear"""
    start = time.time()
    while time.time() - start < timeout:
        resp = requests.get(f"http://localhost:5050/api/debug/events/{room_id}?event_type={event_type}")
        events = resp.json()["events"]
        if events:
            return events[0]
        time.sleep(0.5)
    raise AssertionError(f"Event {event_type} not found within {timeout}s")

def verify_event_fields(event, required_fields):
    """Verify event has all required fields"""
    for field in required_fields:
        if field not in event["payload"]:
            raise AssertionError(f"Missing required field: {field}")
    print(f"✓ Event {event['event_type']} has all required fields")

# Run tests
room_id = "TEST_ROOM"

# Test disconnection event
print("Testing disconnection events...")
disconnect_event = test_event_exists(room_id, "player_disconnected")
verify_event_fields(disconnect_event, ["player_name", "timestamp", "was_bot", "grace_period_seconds", "game_context"])

# Test bot takeover
print("Waiting 6 seconds for bot takeover...")
time.sleep(6)
takeover_event = test_event_exists(room_id, "bot_takeover_activated")
verify_event_fields(takeover_event, ["activation_time", "pre_state", "reason"])

print("All data collection tests passed!")
```

## Success Criteria for Data Collection

1. **Complete Connection Lifecycle**: Can trace every state transition
2. **Action Attribution**: Know exactly who made each move
3. **Failure Detection**: Automatically detect when bot control fails
4. **Timing Analysis**: See exact delays and race conditions
5. **Pattern Recognition**: Identify common failure patterns
6. **Historical Analysis**: Debug issues that happened hours/days ago

## What This Gives Us

With this data collection, we can answer:
- "Why didn't the bot release control?" - Check for `bot_control_failed_release` events
- "When exactly did the player disconnect?" - See `player_disconnected` with timestamp
- "How long was the bot in control?" - Calculate from timeline
- "Did the human try to play while bot had control?" - Check `action_blocked` events
- "What was the game state during the issue?" - See game_context in events
- "Is this a pattern or one-time issue?" - Analyze across multiple rooms

## Critical Implementation Notes

1. **MUST store events synchronously** - Don't use fire-and-forget
2. **Include game context** - Always capture phase, current player, etc
3. **Use consistent player IDs** - Same ID across all events
4. **Timestamp everything** - Use time.time() for consistency
5. **Store failures** - Failed operations are most important for debugging

This plan prioritizes comprehensive data collection that will make debugging ANY future issue much easier, not just the bot takeover bug.