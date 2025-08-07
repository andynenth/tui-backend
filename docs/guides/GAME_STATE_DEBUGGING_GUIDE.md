# Game State Debugging Guide

## Quick Diagnosis Checklist

When a game appears "stuck" or bots seem to behave incorrectly:

### 1. Check Current Game State
```bash
curl -s http://localhost:5050/api/rooms/{ROOM_ID}/state | python -m json.tool
```

Look for:
- `phase`: Current game phase (if null, check state_source)
- `state_source`: "live" vs "reconstructed"
- `game_active`: Should be true for active games
- `round_number`: Current round
- Player hands and declarations

### 2. Check Recent Events
```bash
# Last 50 events
curl -s http://localhost:5050/api/rooms/{ROOM_ID}/events | python -m json.tool | tail -100

# Find who played recently
curl -s http://localhost:5050/api/rooms/{ROOM_ID}/events | python -m json.tool | grep -A5 "play_pieces" | grep "player_name" | tail -10
```

### 3. Check Turn Status
```bash
# Find current turn state
curl -s http://localhost:5050/api/rooms/{ROOM_ID}/events | python -m json.tool | grep -B10 -A10 "turn_plays"

# Check if turn completed
curl -s http://localhost:5050/api/rooms/{ROOM_ID}/events | python -m json.tool | grep "turn_complete"
```

### 4. Analyze Player Declarations
Look for declaration events to understand bot behavior:
```bash
curl -s http://localhost:5050/api/rooms/{ROOM_ID}/events | python -m json.tool | grep -B5 -A5 "declarations"
```

**Remember**: A bot that declares 0 MUST play weak pieces to avoid winning!

## Common "Non-Issues"

### "Bots only play weak pieces"
**Check**: Player declarations
- If a bot declared 0, they SHOULD play weak pieces
- Early in round, bots play conservatively
- This is strategic, not a bug

### "Game is stuck"
**Check**: Who hasn't played yet
```bash
# Use the diagnostic script
python diagnose_room.py {ROOM_ID}
```
Often the game is just waiting for a human player.

### "Phase is null"
**Check**: state_source field
- If "reconstructed", the live game might be disconnected
- Phase is managed by state machine, not game object
- This doesn't always indicate a broken game

## Key Architecture Points

1. **State Machine vs Game Object**
   - Phase is in state machine, not game.current_phase
   - State machine handles all phase transitions
   - Game object holds game data

2. **Event Flow**
   - All game actions go through WebSocket
   - State changes trigger automatic broadcasts
   - Bot manager responds to phase_change events

3. **Turn Completion**
   - All players must play
   - Turn resolves automatically when complete
   - Winner becomes next turn starter

## Diagnostic Script Usage

```bash
# Create and run diagnostic script
python diagnose_room.py {ROOM_ID}
```

This will show:
- Current phase and round
- Who needs to play
- Turn order and status
- Potential issues

## When It's Really Stuck

Signs of actual problems:
- `state_source: "reconstructed"` with no active connections
- All players have played but turn didn't complete
- State machine not running (`is_running: false`)
- Repeated errors in event history

## Recovery Options

1. **Wait for Human Player**
   - Most common solution
   - Check who hasn't played

2. **Trigger State Machine**
   - Force phase transition
   - Requires admin access

3. **Restart Room**
   - Last resort
   - Loses current game progress

## Bot Strategy Reference

### Declaration Impact on Play Style

| Declared | Strategy | Typical Plays |
|----------|----------|---------------|
| 0 | Avoid all wins | Weakest pieces always |
| 1-2 | Conservative | Mix of weak/medium |
| 3-4 | Balanced | Strategic plays |
| 5+ | Aggressive | Strong pieces when needed |

### Urgency Levels

- **Low**: Dispose burdens, play weak
- **Medium**: Balanced play, use openers
- **High**: Try to win needed piles
- **Critical**: Must win almost every turn

## Debugging Commands Reference

```bash
# Room stats
curl -s http://localhost:5050/api/debug/room-stats | python -m json.tool

# Health check
curl -s http://localhost:5050/api/health/detailed

# Recovery status
curl -s http://localhost:5050/api/recovery/status | python -m json.tool

# Event store stats
curl -s http://localhost:5050/api/event-store/stats
```

## Remember

1. **Context is Everything**
   - Check declarations before judging bot behavior
   - Verify complete turn sequence
   - Understand game phase and round number

2. **Not Every Oddity is a Bug**
   - Conservative play might be strategic
   - Waiting might be for human input
   - State representation might be misleading

3. **Use the Tools**
   - Diagnostic scripts
   - Event history analysis
   - Git history for recent changes