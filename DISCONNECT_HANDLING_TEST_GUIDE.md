# Disconnect Handling Manual Test Guide

## 🎯 Test Objectives
Verify that the disconnect handling system works correctly for:
1. Player disconnection detection
2. Bot activation
3. Toast notifications
4. Session persistence
5. Reconnection flow

## 🚀 Setup Instructions

### Start the Development Environment
```bash
# Start both backend and frontend
./start.sh

# Or start them separately:
# Backend
docker-compose -f docker-compose.dev.yml up backend

# Frontend (in another terminal)
cd frontend && npm run dev
```

### Access the Application
- Open browser at: http://localhost:3456
- You'll need multiple browser windows/tabs to simulate multiple players

## 📋 Test Scenarios

### Test 1: Basic Disconnect Detection
**Setup:**
1. Open 4 browser windows (use incognito/private windows for separate sessions)
2. Create a room with Player 1
3. Join the room with Players 2, 3, and 4
4. Start the game

**Test Steps:**
1. Close Player 2's browser window completely
2. Wait 2-3 seconds

**Expected Results:**
- [ ] Other players see toast: "Player2 disconnected - AI is now playing for them"
- [ ] Player 2's name shows bot indicator (🤖 or similar visual cue)
- [ ] Game continues without interruption
- [ ] Bot makes moves for Player 2 when it's their turn

### Test 2: Session Persistence
**Setup:**
1. Use the game from Test 1 (with Player 2 disconnected)

**Test Steps:**
1. As Player 3, note the game URL (e.g., http://localhost:3456/game/room123)
2. Close Player 3's browser completely
3. Open a new browser window
4. Navigate directly to the game URL

**Expected Results:**
- [ ] Browser automatically redirects to the game
- [ ] Player 3's name is restored
- [ ] Player 3 rejoins the game in the correct state
- [ ] Other players see toast: "Player3 reconnected and resumed control"
- [ ] Player 3 can continue playing

### Test 3: Browser Refresh Recovery
**Setup:**
1. Continue with the same game

**Test Steps:**
1. As Player 1 (host), press F5 or Cmd+R to refresh the browser
2. Wait for the page to reload

**Expected Results:**
- [ ] Player 1 automatically reconnects to the game
- [ ] Game state is preserved
- [ ] Player 1 remains the host
- [ ] No "Not Found" error

### Test 4: Multiple Disconnections
**Setup:**
1. Continue with the same game

**Test Steps:**
1. Close both Player 2 and Player 4's browsers
2. Wait 5 seconds
3. Player 2 returns by navigating to the game URL

**Expected Results:**
- [ ] Both disconnections show separate toast notifications
- [ ] Both players show bot indicators
- [ ] When Player 2 returns, only Player 2's bot indicator is removed
- [ ] Player 4 remains as bot
- [ ] Reconnection toast shows only for Player 2

### Test 5: Host Migration
**Setup:**
1. Start a new game with 4 players
2. Note who is the host (usually Player 1)

**Test Steps:**
1. Close the host's browser
2. Observe other players' screens

**Expected Results:**
- [ ] Toast notification: "Player1 disconnected - AI is now playing for them"
- [ ] New host notification: "Player2 is now the host" (or whoever became host)
- [ ] Game continues without interruption
- [ ] New host can control game flow

### Test 6: Edge Cases

#### 6.1 Quick Disconnect/Reconnect
1. Close a player's browser
2. Immediately (within 2 seconds) navigate back to the game URL

**Expected:**
- [ ] Player reconnects successfully
- [ ] Minimal disruption to game flow

#### 6.2 Network Interruption
1. Open browser DevTools (F12)
2. Go to Network tab
3. Set to "Offline"
4. Wait 10 seconds
5. Set back to "Online"

**Expected:**
- [ ] Automatic reconnection attempt
- [ ] Game state restored after reconnection

#### 6.3 Multiple Tabs
1. Open the same game in two tabs with the same player name
2. Close one tab

**Expected:**
- [ ] Other tab remains connected
- [ ] No disconnect notification (player still has active connection)

## 🐛 Common Issues to Check

### Issue 1: No Toast Notifications
**Check:**
- Open browser console (F12)
- Look for errors related to ToastContainer or useToastNotifications
- Verify ToastContainer is rendered in GamePage

### Issue 2: "Not Found" Error on Return
**Check:**
- Open browser DevTools > Application > Local Storage
- Look for "liap_tui_session" key
- Verify it contains roomId and playerName

### Issue 3: Bot Not Activating
**Check:**
- Backend logs should show: "Player X disconnected from game in room Y. Bot activated."
- Check browser console for WebSocket errors

## 📊 Test Results Template

```markdown
### Test Run: [Date/Time]
**Environment:** [Development/Staging/Production]
**Browsers Tested:** [Chrome/Firefox/Safari/Edge]

#### Test 1: Basic Disconnect Detection
- [ ] Toast notification appeared: Yes/No
- [ ] Bot indicator shown: Yes/No
- [ ] Game continued: Yes/No
- Notes: 

#### Test 2: Session Persistence
- [ ] Auto-redirect worked: Yes/No
- [ ] Player name restored: Yes/No
- [ ] Reconnection successful: Yes/No
- Notes:

[Continue for all tests...]

### Overall Results: PASS/FAIL
### Issues Found:
1. 
2. 

### Recommendations:
```

## 🔍 Debugging Tips

1. **Check Backend Logs:**
   ```bash
   docker-compose -f docker-compose.dev.yml logs -f backend
   ```
   Look for:
   - "Successfully registered player X for room Y"
   - "Player X disconnected from game in room Y. Bot activated."

2. **Check Browser Console:**
   - Connection status messages
   - Toast notification triggers
   - Session storage operations

3. **Check Network Tab:**
   - WebSocket connection status
   - client_ready events with player_name
   - player_disconnected/reconnected events

## ✅ Success Criteria

The disconnect handling system is working correctly when:
1. All players are properly registered (no empty ConnectionManager)
2. Disconnections are detected within 5 seconds
3. Toast notifications appear for all game events
4. Players can close and reopen their browser without losing their game
5. Bot players make valid moves
6. No "Not Found" errors on reconnection
7. Host migration works seamlessly

## 🎉 Next Steps

After successful manual testing:
1. Document any issues found
2. Fix any bugs discovered
3. Consider writing automated tests for the scenarios above
4. Update documentation with final implementation details