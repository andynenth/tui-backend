# AI Testing Workflow for Claude Code

This document provides a structured workflow for testing implementations in a single-terminal environment using Claude Code with Playwright MCP.

## Pre-Testing Checklist

### 1. Code Quality Verification
Before ANY testing:
```bash
# Python code quality
source venv/bin/activate && cd backend && pylint [changed_files]

# Frontend code quality  
cd frontend && npm run lint
cd frontend && npm run type-check

# Fix any errors BEFORE proceeding to testing
```

### 2. Dependency Check
```bash
# Frontend dependencies (CRITICAL after git operations)
cd frontend && npm install

# Backend dependencies
source venv/bin/activate && pip install -r requirements.txt
```

## Testing Workflow

### Phase 1: Server Startup with Monitoring

#### Step 1.1: Start Server in Background
```bash
# Kill any existing servers
pkill -f "uvicorn backend.api.main:app" || true

# Start with comprehensive logging
nohup ./start.sh > test_server_full.log 2>&1 &
SERVER_PID=$!

# Verify server started
sleep 5
curl -s http://localhost:5050/api/health | jq
```

#### Step 1.2: Monitor Server Health
```bash
# Check for startup errors
tail -n 50 test_server_full.log | grep -E "ERROR|CRITICAL|AttributeError|ImportError"

# If errors found, STOP and fix before proceeding
```

### Phase 2: Playwright Test Setup

#### Step 2.1: Initial Browser Setup
```
mcp__playwright__browser_navigate(url="http://localhost:5050")
mcp__playwright__browser_snapshot()  # Verify page loaded
```

#### Step 2.2: Create Test Environment
```
# Create room with bots
1. Click "Enter Lobby"
2. Click "Create Room" 
3. Note room ID from URL
4. Verify 3 bots auto-added
5. Click "Start Game"
6. Wait for game page to load
```

### Phase 3: Test Execution

#### Step 3.1: Pre-Test Data Verification
```bash
# Store room ID
ROOM_ID="[room_id_from_url]"

# Verify event collection is working
curl -s "http://localhost:5050/api/debug/events/$ROOM_ID" | jq '.total_events'
# Should be > 0
```

#### Step 3.2: Execute Test Scenario
Example: Testing Disconnection/Reconnection
```
# 1. Close browser (simulate disconnect)
mcp__playwright__browser_close()

# 2. Wait for grace period
sleep 6

# 3. Verify disconnection events
curl -s "http://localhost:5050/api/debug/events/$ROOM_ID?event_type=player_disconnected" | jq

# 4. Reconnect
mcp__playwright__browser_navigate(url="http://localhost:5050/game/$ROOM_ID")

# 5. Verify reconnection events
curl -s "http://localhost:5050/api/debug/events/$ROOM_ID?event_type=player_reconnected" | jq
```

### Phase 4: Data Collection Verification

#### Step 4.1: Event Verification Checklist
```bash
# Essential events to verify
EVENT_TYPES=(
  "player_disconnected"
  "bot_takeover_scheduled"
  "bot_takeover_activated"
  "bot_control_released"
  "human_action"
  "bot_action"
)

for event in "${EVENT_TYPES[@]}"; do
  echo "Checking $event:"
  curl -s "http://localhost:5050/api/debug/events/$ROOM_ID?event_type=$event" | jq '.total_events'
done
```

#### Step 4.2: Debug Endpoint Verification
```bash
# Connection timeline
curl -s "http://localhost:5050/api/debug/connection-timeline/$ROOM_ID" | jq '.timeline_events'

# Bot control analysis
curl -s "http://localhost:5050/api/debug/bot-control-analysis/$ROOM_ID" | jq '.summary'
```

### Phase 5: Error Investigation

#### Step 5.1: Check Server Logs for Errors
```bash
# Look for specific error patterns
grep -n "ERROR" test_server_full.log | tail -20
grep -n "AttributeError" test_server_full.log
grep -n "TypeError" test_server_full.log
```

#### Step 5.2: Analyze Failed Events
```bash
# Check events with null player_id
curl -s "http://localhost:5050/api/debug/events/$ROOM_ID" | jq '.events[] | select(.player_id == null)'
```

## Common Testing Patterns

### Pattern 1: Game State Testing
```python
# Test script template
test_steps = """
1. Navigate to lobby
2. Create room (note ID)
3. Start game
4. Wait for phase change
5. Perform test action
6. Verify expected events
7. Check debug endpoints
"""
```

### Pattern 2: Disconnection Testing
```python
disconnect_test = """
1. Get to player's turn
2. Close browser
3. Wait grace period (5s)
4. Verify bot takeover
5. Reconnect
6. Verify control release
7. Make human move
8. Verify move success
"""
```

### Pattern 3: Performance Testing
```python
performance_test = """
1. Create multiple rooms
2. Monitor response times
3. Check event storage latency
4. Verify no memory leaks
5. Test concurrent connections
"""
```

## Error Recovery Procedures

### Server Crash Recovery
```bash
# 1. Save current logs
cp test_server_full.log "crash_log_$(date +%Y%m%d_%H%M%S).log"

# 2. Kill stuck processes
pkill -f "uvicorn backend.api.main:app"
pkill -f "npm run dev"

# 3. Clean state
rm -f game_events.db  # If testing with fresh DB

# 4. Restart
./start.sh > test_server_full.log 2>&1 &
```

### Browser State Recovery
```
# If browser gets stuck
mcp__playwright__browser_close()
# Wait 2 seconds
mcp__playwright__browser_navigate(url="http://localhost:5050")
```

## Testing Best Practices

### 1. Always Test Happy Path First
- Create room → Add bots → Start game → Play normally
- Verify basic functionality before edge cases

### 2. Test One Thing at a Time
- Don't combine multiple test scenarios
- Isolate variables for clear results

### 3. Document Everything
```bash
# Create test session log
echo "Test Session: $(date)" > test_session.log
echo "Testing: [feature_name]" >> test_session.log
echo "Room ID: $ROOM_ID" >> test_session.log
# Add observations as you go
```

### 4. Verify Prerequisites
- Server healthy: `curl http://localhost:5050/api/health`
- No existing errors: `tail -f test_server_full.log`
- Clean browser state: Close all tabs first

### 5. Use Systematic Verification
```bash
# Create verification script
cat > verify_test.sh << 'EOF'
#!/bin/bash
ROOM_ID=$1
echo "=== Event Summary for Room $ROOM_ID ==="
curl -s "http://localhost:5050/api/debug/events/$ROOM_ID" | \
  jq '.events[].event_type' | sort | uniq -c
echo "=== Connection Timeline ==="
curl -s "http://localhost:5050/api/debug/connection-timeline/$ROOM_ID" | \
  jq '.timeline_events'
EOF
chmod +x verify_test.sh
```

## Common Pitfalls to Avoid

1. **Testing with stale code**: Always restart server after code changes
2. **Ignoring error logs**: Check logs continuously during testing
3. **Not waiting for async operations**: Give sufficient time for events
4. **Testing with corrupted state**: Start fresh if behavior seems wrong
5. **Not verifying prerequisites**: Ensure all services are running

## Test Result Documentation Template

```markdown
## Test Results: [Feature Name]

### Test Environment
- Date/Time: [timestamp]
- Branch: [git branch name]
- Room ID: [room_id]
- Player: [player_name]

### Test Scenario
[Describe what was tested]

### Steps Executed
1. [Step 1 with result]
2. [Step 2 with result]
3. [etc...]

### Events Captured
- player_disconnected: [count]
- bot_takeover_scheduled: [count]
- [other events...]

### Issues Found
1. [Issue description]
   - Error: [error message]
   - File: [file:line]
   - Fix: [what was done]

### Debug Endpoint Results
[Paste relevant endpoint responses]

### Conclusion
[Pass/Fail with summary]
```

## Automation Helper Scripts

### Create Test Helper Script
```bash
cat > test_helper.py << 'EOF'
#!/usr/bin/env python3
import subprocess
import time
import json
import sys

def check_server_health():
    """Verify server is running"""
    try:
        result = subprocess.run(
            ["curl", "-s", "http://localhost:5050/api/health"],
            capture_output=True,
            text=True
        )
        return "healthy" in result.stdout
    except:
        return False

def get_event_count(room_id, event_type=None):
    """Get count of events for a room"""
    url = f"http://localhost:5050/api/debug/events/{room_id}"
    if event_type:
        url += f"?event_type={event_type}"
    
    result = subprocess.run(
        ["curl", "-s", url],
        capture_output=True,
        text=True
    )
    
    try:
        data = json.loads(result.stdout)
        return data.get("total_events", 0)
    except:
        return -1

def wait_for_event(room_id, event_type, timeout=10):
    """Wait for a specific event to appear"""
    start = time.time()
    while time.time() - start < timeout:
        if get_event_count(room_id, event_type) > 0:
            return True
        time.sleep(1)
    return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        room_id = sys.argv[1]
        print(f"Room {room_id} total events: {get_event_count(room_id)}")
    else:
        print(f"Server healthy: {check_server_health()}")
EOF
chmod +x test_helper.py
```

## Summary

This workflow ensures systematic, repeatable testing with proper verification at each step. Key principles:

1. **Verify before testing**: Check code quality and server health
2. **Monitor continuously**: Watch logs during entire test
3. **Validate systematically**: Check each expected outcome
4. **Document thoroughly**: Record all observations and results
5. **Automate repetitive tasks**: Use scripts for common checks

Following this workflow will prevent the issues encountered in the previous test session and ensure reliable, comprehensive testing.