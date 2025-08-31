# WebSocket Reconnection Test Plan

## Overview
This document outlines the test plan for verifying the WebSocket reconnection fixes that address the frontend display bug where incorrect round numbers were shown after disconnection.

## Fixes Implemented

### Frontend Changes
1. **Enhanced Logging** (`NetworkService.ts`)
   - Added detailed phase_change logging with round number tracking
   - Added reconnection event logging
   - Timestamp all events for debugging

2. **State Synchronization** (`GameService.ts`)
   - Added reconnection handler that requests full state
   - Fixed round number handling in handlePhaseChange
   - Added warnings when round number is missing from phase_change events

3. **Debug Tools**
   - Created StateDebugOverlay component for visual debugging
   - Created test-reconnection.js script for automated testing
   - Created test-reconnection.html page for UI-based testing

### Backend Verification
1. **Round Number Broadcasting** (`base_state.py`)
   - Verified line 222 includes round number in all phase_change broadcasts
   
2. **Full State Handlers** (`ws.py`)
   - Verified `client_ready` handler sends full state on reconnection (lines 738-775)
   - Verified `get_full_state` handler exists and works (lines 876-916)

## Test Scenarios

### Test 1: Quick Disconnect (1 second)
**Steps:**
1. Start a game and note the current round
2. Use test script: `testReconnection.testQuickReconnect()`
3. Verify round number remains correct after reconnection

**Expected Result:**
- Round number should not change
- Phase should remain the same
- No "Round 2" display when actually in Round 1

### Test 2: Medium Disconnect (5 seconds)
**Steps:**
1. Start a game during an active turn
2. Use test script: `testReconnection.testMediumDisconnect()`
3. Monitor console logs and debug overlay

**Expected Result:**
- Full state requested on reconnection
- Round number synchronized correctly
- State updated without visual glitches

### Test 3: Long Disconnect (15 seconds)
**Steps:**
1. Start a game and progress to middle of round
2. Use test script: `testReconnection.testLongDisconnect()`
3. Check if any bot takeover occurs

**Expected Result:**
- Bot may take over after 10 seconds
- On reconnection, correct round displayed
- Player resumes control from bot

### Test 4: Rapid Disconnects
**Steps:**
1. During active gameplay
2. Use test script: `testReconnection.testRapidDisconnects(3)`
3. Monitor for state corruption

**Expected Result:**
- State remains consistent
- No duplicate or missing updates
- Round number stays synchronized

### Test 5: Cross-Round Disconnect
**Steps:**
1. Disconnect near end of round
2. Let game progress to next round while disconnected
3. Reconnect after round change

**Expected Result:**
- New round number displayed correctly
- Full state sync includes new round data
- No stale round number shown

## Using the Debug Tools

### Browser Console Testing
```javascript
// Load the test script in browser console
const script = document.createElement('script');
script.src = '/test-reconnection.js';
document.head.appendChild(script);

// Monitor messages
testReconnection.monitorMessages();

// Run tests
testReconnection.testQuickReconnect();
```

### Visual Debug Overlay
The StateDebugOverlay component shows:
- Current round number
- Current phase
- Connection status
- Last update timestamp
- Stale state warning (after 30 seconds)
- Recent WebSocket events

### Test UI Page
1. Open `/test-reconnection.html` in browser
2. Ensure game is running in another tab
3. Use buttons to trigger test scenarios
4. Monitor logs in the test page

## Verification Checklist

- [ ] Round number never shows incorrect value after reconnection
- [ ] Phase_change events always include round number
- [ ] Full state is requested and received on reconnection
- [ ] State updates are applied atomically
- [ ] No visual glitches during reconnection
- [ ] Bot takeover/resume works correctly
- [ ] Multiple rapid disconnects don't corrupt state
- [ ] Cross-round disconnections handled properly

## Log Analysis

Look for these key log entries:

### Successful Reconnection
```
🔄 Requesting full state after reconnection
📨 get_full_state event sent
📊 full_state event received - round: X
✅ State synchronized successfully
```

### Warning Signs
```
⚠️ Phase change without round number
⚠️ Round number changed after reconnection!
⚠️ State may be stale (no updates for 30+ seconds)
```

## Production Deployment

1. Deploy frontend changes (NetworkService.ts, GameService.ts)
2. Backend already has correct implementation
3. Monitor logs for any `⚠️` warnings about missing round numbers
4. Use StateDebugOverlay in development/staging for verification
5. Remove debug overlay before production deployment

## Success Criteria

The fix is considered successful when:
1. No incorrect round numbers displayed after any disconnection scenario
2. State synchronization completes within 2 seconds of reconnection
3. No warnings about missing round numbers in logs
4. All test scenarios pass without state corruption