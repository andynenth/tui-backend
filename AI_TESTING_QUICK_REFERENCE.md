# AI Testing Quick Reference

## 🚀 Quick Start Testing Workflow

### 1. Pre-Flight Check (30 seconds)
```bash
# Kill any existing servers
pkill -f "uvicorn backend.api.main:app" || true

# Check code quality FIRST
source venv/bin/activate && cd backend && pylint engine/state_machine/base_state.py api/routes/ws.py
cd frontend && npm run lint --silent

# Start server with logging
cd /Users/nrw/python/tui-project/liap-tui
nohup ./start.sh > test_server_full.log 2>&1 &

# Verify server started (wait 5 seconds)
sleep 5 && curl -s http://localhost:5050/api/health | jq '.status'
```

### 2. Create Test Room (1 minute)
```
# In Playwright MCP:
mcp__playwright__browser_navigate(url="http://localhost:5050")
# Enter name, click "Enter Lobby"
# Click "Create Room"
# Note room ID from URL (e.g., "ABC123")
# Click "Start Game"
```

### 3. Run Automated Tests (2 minutes)
```bash
# Run test suite
python run_bot_takeover_tests.py ABC123

# Or manual verification
ROOM_ID=ABC123
curl -s "http://localhost:5050/api/debug/events/$ROOM_ID" | jq '.total_events'
```

### 4. Test Disconnection Manually (1 minute)
```
# Close browser
mcp__playwright__browser_close()

# Wait 6 seconds for bot takeover
# Check events
curl -s "http://localhost:5050/api/debug/events/$ROOM_ID?event_type=bot_takeover_activated" | jq

# Reconnect
mcp__playwright__browser_navigate(url="http://localhost:5050/game/$ROOM_ID")
```

## 📋 Essential Commands

### Check Event Collection
```bash
# See all events
curl -s "http://localhost:5050/api/debug/events/$ROOM_ID" | jq '.events[].event_type' | sort | uniq -c

# Check specific event
curl -s "http://localhost:5050/api/debug/events/$ROOM_ID?event_type=player_disconnected" | jq

# Connection timeline
curl -s "http://localhost:5050/api/debug/connection-timeline/$ROOM_ID" | jq

# Bot control analysis
curl -s "http://localhost:5050/api/debug/bot-control-analysis/$ROOM_ID" | jq
```

### Monitor Server Health
```bash
# Check for errors
tail -f test_server_full.log | grep -E "ERROR|AttributeError"

# See recent logs
tail -n 50 test_server_full.log

# Check specific error
grep -n "player_id" test_server_full.log
```

## 🔍 What to Look For

### ✅ Good Signs
- Events being stored with timestamps
- Both human_action and bot_action events present
- player_disconnected followed by bot_takeover_scheduled
- No AttributeError or TypeError in logs

### ❌ Bad Signs
- Events with null player_id
- Missing event types
- Server errors during tests
- Empty debug endpoint responses

## 🛠️ Common Issues & Fixes

### Server Won't Start
```bash
# Check if port in use
lsof -i :5050
# Kill if needed
kill -9 [PID]
```

### Events Not Storing
```bash
# Check EventStore
ls -la game_events.db
# Verify it's writable
```

### Browser Gets Stuck
```
mcp__playwright__browser_close()
# Wait 2 seconds
mcp__playwright__browser_navigate(url="http://localhost:5050")
```

## 📊 Test Success Criteria

Minimum requirements for successful test:
- [ ] Server starts without errors
- [ ] Can create room and start game
- [ ] Events are being stored (total > 0)
- [ ] Both human and bot actions captured
- [ ] Disconnection events recorded
- [ ] Debug endpoints return data
- [ ] No new errors in server log

## 🚨 Emergency Recovery

If everything breaks:
```bash
# Full reset
pkill -f "uvicorn"
pkill -f "npm run dev"
rm -f test_server_full.log
rm -f game_events.db  # Only if testing fresh

# Start fresh
./start.sh > test_server_full.log 2>&1 &
```

## 📝 Test Report Template

```
Test Session: [Date/Time]
Room ID: [room_id]
Duration: [time]

Events Captured:
- player_disconnected: [count]
- bot_takeover_scheduled: [count]
- bot_takeover_activated: [count]
- human_action: [count]
- bot_action: [count]

Issues Found:
1. [Issue description]
   Fix: [What was done]

Result: PASS/FAIL
```