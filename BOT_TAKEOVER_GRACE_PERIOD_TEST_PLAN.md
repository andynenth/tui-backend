# Bot Takeover Grace Period Test Plan

## Test Environment Setup

### Prerequisites
1. Backend running: `./start.sh`
2. Frontend accessible at http://localhost:8000
3. Playwright for automated testing
4. Multiple browser windows for multi-player testing

### Test Data
- Room ID: Will be generated
- Test Players: 
  - Human1 (test user)
  - Bot1, Bot2, Bot3 (auto-generated)

## Test Cases

### Test 1: Basic Grace Period Functionality
**Purpose**: Verify bot doesn't take over for 5 seconds after disconnect

**Steps**:
1. Create room as Human1
2. Start game with 3 bots
3. During Human1's turn, disconnect (close browser/tab)
4. Monitor logs for grace period message
5. Wait and verify bot doesn't act for 5 seconds
6. After 5 seconds, verify bot takes over

**Expected Results**:
- Log shows: `🕐 [GRACE_PERIOD] Player Human1 disconnected. Bot takeover scheduled in 5 seconds`
- No bot actions for 5 seconds
- After 5 seconds: `🤖 [GRACE_PERIOD] Bot takeover activated for Human1`
- Bot makes the required play

**Verification Commands**:
```bash
# Watch logs in real-time
tail -f backend/logs/game.log | grep -E "GRACE_PERIOD|BOT_HANDLER"
```

### Test 2: Reconnection Within Grace Period
**Purpose**: Verify player can reconnect and cancel bot takeover

**Steps**:
1. Create room and start game
2. During Human1's turn, disconnect
3. Within 3 seconds, reconnect (refresh page)
4. Verify player regains control
5. Make a play as Human1

**Expected Results**:
- Grace period starts on disconnect
- On reconnect: `🕐 [GRACE_PERIOD] Cancelled bot takeover for Human1 - player reconnected`
- Player can make moves normally
- Bot never takes over

### Test 3: Reconnection After Grace Period
**Purpose**: Verify player can reclaim control after bot takeover

**Steps**:
1. Create room and start game
2. Disconnect and wait 6+ seconds
3. Verify bot takes over and makes a play
4. Reconnect as Human1
5. Verify control returns to human

**Expected Results**:
- Bot takes over after 5 seconds
- Bot makes plays
- On reconnect, human regains control
- Future turns handled by human

### Test 4: Multiple Disconnections
**Purpose**: Test grace period reset on multiple disconnects

**Steps**:
1. Start game
2. Disconnect for 3 seconds
3. Reconnect
4. Disconnect again immediately
5. Verify new 5-second grace period starts

**Expected Results**:
- Each disconnect starts fresh 5-second grace period
- No zombie bot tasks
- Clean state transitions

### Test 5: Declaration Phase Grace Period
**Purpose**: Test grace period during declaration phase

**Steps**:
1. Start game
2. During declaration phase, disconnect when it's Human1's turn
3. Monitor grace period
4. Verify bot declares after 5 seconds

**Expected Results**:
- 5-second grace period applies
- Bot declares appropriate value after grace period
- Game continues normally

### Test 6: Edge Cases

#### 6a: Game End During Grace Period
**Steps**:
1. Disconnect during final round
2. Other players complete game within 5 seconds
3. Verify grace period task cancels cleanly

#### 6b: Room Closure During Grace Period
**Steps**:
1. Disconnect
2. All other players leave within grace period
3. Verify room cleanup and grace period cancellation

#### 6c: Host Migration During Grace Period
**Steps**:
1. Host disconnects
2. Verify host migration happens immediately
3. Verify grace period still applies to disconnected host

### Test 7: Performance and Load Testing
**Purpose**: Ensure grace period doesn't impact game performance

**Steps**:
1. Create multiple rooms
2. Simulate multiple disconnections across rooms
3. Monitor server performance
4. Verify no memory leaks or hanging tasks

**Metrics to Monitor**:
- Response time remains <100ms
- No increase in memory usage
- No hanging asyncio tasks

## Automated Test Script

```python
# test_grace_period.py
import asyncio
import time
from playwright.async_api import async_playwright

async def test_basic_grace_period():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Create room and start game
        await page.goto("http://localhost:8000")
        await page.fill('input[placeholder="Enter your name"]', "Human1")
        await page.click('button:has-text("Enter Lobby")')
        await page.click('button:has-text("Create Room")')
        
        # Get room code
        room_code = await page.text_content('.room-code')
        print(f"Created room: {room_code}")
        
        # Start game
        await page.click('button:has-text("Start Game")')
        
        # Wait for turn
        await page.wait_for_selector('text=Your turn')
        
        # Disconnect by closing page
        disconnect_time = time.time()
        await page.close()
        
        # Wait 3 seconds (within grace period)
        await asyncio.sleep(3)
        
        # Reconnect
        page2 = await browser.new_page()
        await page2.goto(f"http://localhost:8000/room/{room_code}")
        
        # Verify still in control
        await page2.wait_for_selector('text=Your turn')
        reconnect_time = time.time()
        
        print(f"Grace period test passed! Reconnected after {reconnect_time - disconnect_time:.1f} seconds")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_basic_grace_period())
```

## Manual Testing Checklist

- [ ] Grace period starts on disconnect
- [ ] Bot doesn't act for 5 seconds
- [ ] Bot takes over after 5 seconds
- [ ] Reconnection within grace cancels takeover
- [ ] Reconnection after grace returns control
- [ ] Multiple disconnects work correctly
- [ ] Declaration phase grace period works
- [ ] Turn phase grace period works
- [ ] No performance degradation
- [ ] Clean logs with clear messages
- [ ] Frontend shows appropriate status

## Log Monitoring Commands

```bash
# Watch for grace period events
tail -f backend/logs/game.log | grep GRACE_PERIOD

# Monitor bot actions
tail -f backend/logs/game.log | grep -E "BOT_HANDLER|GRACE_PERIOD"

# Check for errors
tail -f backend/logs/game.log | grep -E "ERROR|Error in activate_bot_after_grace"
```

## Success Criteria

1. **Functionality**: All test cases pass
2. **Performance**: No degradation in response times
3. **Reliability**: No race conditions or edge case failures
4. **User Experience**: Clear feedback about grace period
5. **Code Quality**: Clean implementation without breaking existing features