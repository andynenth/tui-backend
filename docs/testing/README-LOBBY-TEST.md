# Lobby Auto-Update Bug Investigation

This Playwright test script simulates the lobby auto-update bug to help identify why the backend sends 0 rooms instead of the actual room list.

## Test Scenario

1. **Two Users**: Andy and Alexanderium both enter the lobby
2. **Room Creation**: Andy creates a room while Alexanderium waits in lobby
3. **Auto-Update Check**: Verify if Alexanderium automatically sees Andy's room appear
4. **WebSocket Analysis**: Capture and analyze all WebSocket messages
5. **Bug Detection**: Identify if `room_list_update` events are sent correctly

## Setup and Installation

### Prerequisites
- Application running on `http://localhost:5050`
- Node.js installed

### Install Dependencies
```bash
# Install Playwright
npm install
npx playwright install chromium
```

## Running the Test

### Basic Test Run
```bash
npm run test:lobby
```

### Run with Browser Visible (for debugging)
```bash
npm run test:lobby:headed
```

### Run with Debug Mode (step-by-step)
```bash
npm run test:lobby:debug
```

### Direct Playwright Command
```bash
npx playwright test test_lobby_auto_update.js --headed --workers=1
```

## Test Output

The test will:

1. **Console Logs**: Real-time progress and WebSocket message analysis
2. **HTML Report**: Detailed test report with screenshots/videos if failures occur
3. **JSON Report**: Machine-readable test results in `test-results.json`
4. **Bug Report**: Detailed analysis saved to `lobby-bug-report.json`

## Expected Results

### If Bug is Present
- Alexanderium won't see Andy's room automatically appear
- `room_list_update` messages will show 0 rooms
- Manual refresh will show the room (confirming backend has the data)

### If Bug is Fixed
- Alexanderium will automatically see Andy's room appear
- `room_list_update` messages will contain the new room

## WebSocket Message Analysis

The test captures all WebSocket messages and analyzes:

- **Outgoing Messages**: `create_room`, `get_rooms`, etc.
- **Incoming Messages**: `room_created`, `room_list_update`, etc.
- **Timing Issues**: Race conditions between room creation and lobby updates
- **Data Integrity**: Whether `room_list_update` contains correct room data

## Key Areas to Investigate

Based on the captured messages, look for:

1. **Missing Events**: Are `room_list_update` events being sent to lobby users?
2. **Empty Data**: Do `room_list_update` events contain 0 rooms when they should contain 1?
3. **Timing Issues**: Is there a race condition in the backend?
4. **WebSocket Routing**: Are lobby WebSocket connections receiving broadcasts correctly?

## Troubleshooting

### Application Not Running
```bash
# Make sure the application is running first
./start.sh
# Or check if it's accessible
curl http://localhost:5050
```

### Browser Issues
```bash
# Reinstall browser if needed
npx playwright install chromium --force
```

### Test Timeouts
- Increase timeouts in `playwright.config.js` if your system is slow
- Check if WebSocket connections are established properly

## Files Generated

- `lobby-bug-report.json`: Detailed analysis with all WebSocket messages
- `test-results/`: HTML reports and screenshots
- `test-results.json`: Machine-readable test results

## Integration with MCP

This test is designed to work with MCP (Model Context Protocol) for analysis. The generated `lobby-bug-report.json` contains structured data that can be easily analyzed to identify the root cause of the lobby auto-update issue.