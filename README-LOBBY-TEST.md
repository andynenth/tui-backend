# Lobby to Game Transition Test Suite

This test suite helps diagnose issues with the lobby-to-game transition in the Liap TUI game.

## Prerequisites

1. Ensure the game server is running on `http://localhost:5050`
2. Install test dependencies:
   ```bash
   npm install
   npx playwright install chromium
   ```

## Available Tests

### 1. Comprehensive Single Player Test
**File:** `test_lobby_game_transition.js`

This test simulates a single player creating a room, adding bots, and attempting to start the game. It provides detailed WebSocket monitoring and generates a comprehensive report.

```bash
# Run with UI (recommended for debugging)
npm run test:lobby:headed

# Run headless
npm run test:lobby

# Run with Playwright inspector
npm run test:lobby:debug
```

**Output:**
- Screenshots in `./test-screenshots/`
- Detailed report in `./test-screenshots/test-report.json`

### 2. Multiplayer Simulation Test
**File:** `test_multiplayer_lobby_transition.js`

Simulates 4 real players joining a room and starting a game simultaneously. Useful for detecting synchronization issues.

```bash
npx playwright test test_multiplayer_lobby_transition.js --headed
```

**Output:**
- Screenshots in `./test-screenshots-multiplayer/`
- Report in `./test-screenshots-multiplayer/multiplayer-report.json`

### 3. Quick Check Test
**File:** `test_quick_lobby_check.js`

A simple, fast test to quickly verify the current state of the lobby-to-game transition.

```bash
npx playwright test test_quick_lobby_check.js --headed
```

## What the Tests Monitor

1. **WebSocket Events**
   - All incoming and outgoing messages
   - Connection state changes
   - Error events
   - Timing of events

2. **Console Messages**
   - JavaScript errors
   - Warning messages
   - Custom log outputs

3. **Page Navigation**
   - URL changes
   - Page content changes
   - Presence of waiting indicators

4. **UI State**
   - Button visibility and enabled state
   - Player list updates
   - Error messages

## Interpreting Results

### Common Issues Detected:

1. **"No game_started event received"**
   - Server didn't send the game_started WebSocket message
   - Check server logs for errors in game initialization

2. **"Stuck on waiting state"**
   - Frontend received game_started but didn't navigate
   - Check for JavaScript errors in navigation logic

3. **"WebSocket connection closed"**
   - Connection dropped during transition
   - Check for server crashes or network issues

4. **"Start button disabled"**
   - Room state not properly synchronized
   - Player count might be incorrect

### Reading the Report

The JSON report includes:
- `summary`: High-level test results
- `wsAnalysis`: Breakdown of WebSocket events
- `consoleAnalysis`: Console errors and warnings
- `issues`: Automatically identified problems
- `finalState`: Where the test ended up

## Debugging Tips

1. **Run with `--headed` flag** to see the browser actions
2. **Check screenshots** for visual clues about the failure
3. **Look for patterns** in WebSocket events timing
4. **Compare successful vs failed transitions** if some work

## Next Steps

Based on test results:
1. If no `game_started` event → Check backend game initialization
2. If event received but no navigation → Check frontend routing logic
3. If inconsistent behavior → Look for race conditions
4. If WebSocket errors → Check connection handling code