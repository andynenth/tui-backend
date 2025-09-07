# AI WebSocket Testing Guide

This guide helps AI assistants test WebSocket reconnection and state synchronization issues in the Liap Tui game using Playwright MCP.

## Prerequisites

1. Ensure you have access to Playwright MCP tools
2. The project directory should be `/Users/nrw/python/tui-project/liap-tui/`
3. You need to be able to start the backend server and access browser automation

## Workflow Overview

The testing workflow involves:
1. Starting the backend server with logging
2. Using Playwright MCP to automate browser testing
3. Monitoring server logs for errors
4. Creating comprehensive test reports

## Step-by-Step Testing Process

### 1. Start the Backend Server

First, start the server in the background with full logging:

```bash
cd /Users/nrw/python/tui-project/liap-tui
./start.sh > full_debug.log 2>&1 &
```

This captures all output (stdout and stderr) to `full_debug.log` for later analysis.

### 2. Verify Server is Running

Wait a few seconds for the server to start, then verify it's running:

```bash
curl -s http://localhost:5050/api/health
```

You should see a response indicating the server is healthy.

### 3. Initialize Playwright Browser

Use Playwright MCP to start browser automation:

1. Navigate to the game: `mcp__playwright__browser_navigate` with URL `http://localhost:5050`
2. Take initial screenshot: `mcp__playwright__browser_take_screenshot`

### 4. Create Test Scenarios

Test each game phase systematically:

#### A. Preparation Phase Testing
- Start new game
- Refresh during card dealing
- Check if UI shows correct state

#### B. Declaration Phase Testing
- Navigate to declaration phase
- Refresh before declaring
- Make declaration
- Refresh after declaring
- Verify UI maintains correct state

#### C. Turn Phase Testing (Most Critical)
- Enter turn phase
- Refresh before playing pieces
- Play pieces
- Refresh after playing
- Check for "Waiting for Game" error

#### D. Scoring Phase Testing
- Complete round to reach scoring
- Refresh on score screen
- Verify scores display correctly

### 5. Monitor Server Logs

During testing, regularly check server logs for errors:

```bash
# Check recent logs
tail -n 100 full_debug.log | grep -E "ERROR|Exception|Traceback"

# Check for specific refresh-related logs
grep "REFRESH_DEBUG" full_debug.log

# Check for JSON serialization errors
grep "JSON" full_debug.log | grep -i error
```

### 6. Common Issues and Solutions

#### Issue: "Waiting for Game" on Refresh
**Symptoms**: After refreshing during turn phase, UI shows "Waiting for Game"
**Root Cause**: JSON serialization error with game objects (e.g., Piece objects)
**Solution**: Ensure backend uses `_make_json_safe()` method for all WebSocket data

#### Issue: Missing Player Hands
**Symptoms**: After refresh, player hands are empty
**Root Cause**: Race condition - phase_change arrives before playerName initialized
**Solution**: Check session storage fallback in GameService.ts

### 7. Automated Test Script

Here's a complete test automation flow using Playwright MCP:

```javascript
// 1. Navigate to game
await mcp__playwright__browser_navigate({ url: "http://localhost:5050" })

// 2. Create new game
await mcp__playwright__browser_click({
  element: "Create Game button",
  ref: "button:has-text('Create Game')"
})

// 3. Fill player name
await mcp__playwright__browser_type({
  element: "Player name input",
  ref: "input#playerName",
  text: "TestPlayer"
})

// 4. Submit form
await mcp__playwright__browser_click({
  element: "Submit button",
  ref: "button[type='submit']"
})

// 5. Add bots and start game
// ... (continue with game flow)

// 6. Test refresh at each phase
await mcp__playwright__browser_navigate_back()  // Simulate refresh
await mcp__playwright__browser_navigate({ url: currentUrl })

// 7. Take screenshots for evidence
await mcp__playwright__browser_take_screenshot({
  filename: "refresh-test-turn-phase.png"
})
```

### 8. Creating Test Reports

Document your findings in a structured format:

```markdown
# WebSocket Reconnection Test Report

## Test Environment
- Date: [Current date]
- Server: localhost:5050
- Browser: [Browser used]

## Test Results

### Preparation Phase
- ✅ Refresh during dealing: PASS
- ✅ State maintained: PASS

### Declaration Phase
- ✅ Refresh before declare: PASS
- ✅ Refresh after declare: PASS

### Turn Phase
- ❌ Refresh before play: FAIL - Shows "Waiting for Game"
- ❌ Refresh after play: FAIL - Shows "Waiting for Game"
- Root cause: JSON serialization error with Piece objects

### Scoring Phase
- ✅ Refresh on score screen: PASS

## Errors Found
1. JSON serialization error in turn phase
   - Error: "Object of type Piece is not JSON serializable"
   - Location: backend/engine/state_machine/game_state_machine.py
   - Fix: Use _make_json_safe() method

## Recommendations
1. Implement comprehensive JSON serialization for all game objects
2. Add integration tests for WebSocket reconnection
3. Monitor for race conditions in frontend state initialization
```

## Debugging Tips

1. **Enable Debug Logging**: Add debug statements in critical paths:
   - Frontend: `GameService.ts` handlePhaseChange method
   - Backend: `ws.py` WebSocket reconnection handler

2. **Check Browser Console**: Look for JavaScript errors during refresh

3. **Network Tab**: Monitor WebSocket messages in browser DevTools

4. **Session Storage**: Verify player session data persists across refresh

## Key Files to Monitor

- **Backend**:
  - `/backend/api/routes/ws.py` - WebSocket handling
  - `/backend/engine/state_machine/game_state_machine.py` - State management
  - `/backend/engine/state_machine/base_state.py` - Broadcasting logic

- **Frontend**:
  - `/frontend/src/services/GameService.ts` - Game state management
  - `/frontend/src/services/NetworkService.ts` - WebSocket connection
  - `/frontend/src/hooks/useGameConnection.ts` - Connection hook

## Troubleshooting Checklist

- [ ] Server running and accessible
- [ ] No JSON serialization errors in logs
- [ ] WebSocket connects successfully after refresh
- [ ] Session storage contains valid player data
- [ ] Frontend receives and processes phase_change event
- [ ] Game state properly restored from backend
- [ ] UI renders correct phase after refresh

## Additional Notes

- The issue typically manifests in the turn phase due to complex game objects
- Always check both frontend console and backend logs
- Take screenshots at each test step for documentation
- Test with both human players and bots
- Consider network latency in production environments