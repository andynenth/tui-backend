# Troubleshooting Guide

## Disconnect Handling Issues

### Player Cannot Reconnect

**Symptoms:**
- Player tries to join but gets "Room is full" error
- Player name is not recognized
- Connection fails repeatedly

**Solutions:**

1. **Verify Player Name**
   - Must use exact same name (case-sensitive)
   - No extra spaces before/after name
   - Special characters must match exactly

2. **Check Room Status**
   ```javascript
   // In browser console
   const state = gameService.getState();
   console.log('Room ID:', state.roomId);
   console.log('Disconnected:', state.disconnectedPlayers);
   ```

3. **Verify Bot Status**
   - Ensure the player slot hasn't been permanently taken
   - Check if player is marked as bot in backend

4. **Clear Browser Cache**
   - Force refresh (Ctrl+Shift+R or Cmd+Shift+R)
   - Clear localStorage if session data is corrupted

### AI Not Taking Over

**Symptoms:**
- Game freezes when player disconnects
- Turn timer runs out without bot action
- Other players see no activity

**Solutions:**

1. **Check Bot Activation**
   ```python
   # Backend logs should show:
   # "Player X disconnected from game in room Y. Bot activated."
   ```

2. **Verify Game Phase**
   - Some phases may not require immediate action
   - Check if it's actually the bot's turn

3. **Review AI Logic**
   - Check `backend/engine/ai.py` for phase-specific logic
   - Ensure AI can handle current game state

### Missing Game Events

**Symptoms:**
- Reconnected player has outdated state
- Some moves appear to be missing
- Score doesn't match actual game

**Solutions:**

1. **Check Message Queue**
   ```python
   # In backend, check queue status
   status = message_queue_manager.get_status()
   print(f"Queues: {status['total_queues']}")
   ```

2. **Verify Critical Events**
   - Ensure important events are marked as critical
   - Check queue overflow hasn't dropped critical messages

3. **Force State Sync**
   - Trigger a phase_change event to resync
   - Have player refresh to get full state

### Host Migration Failures

**Symptoms:**
- No new host selected when host disconnects
- Wrong player becomes host
- Host privileges not transferred

**Solutions:**

1. **Check Player List**
   - Ensure room has valid players
   - Verify human players are available

2. **Review Migration Logic**
   ```python
   # Check room.migrate_host() implementation
   # Should prefer humans over bots
   ```

3. **Manual Host Assignment**
   - Admin can manually set host if needed
   - Update room.host_name directly

## Connection Quality Issues

### High Latency

**Symptoms:**
- Slow response to actions
- Connection quality shows "poor"
- Frequent reconnection attempts

**Solutions:**

1. **Network Diagnostics**
   - Run speed test
   - Check for packet loss
   - Try wired connection

2. **Server Location**
   - Check server region
   - Consider CDN for static assets

3. **Reduce Traffic**
   - Minimize broadcast frequency
   - Batch multiple updates

### WebSocket Drops

**Symptoms:**
- Frequent disconnections
- "WebSocket closed" errors
- Reconnection loop

**Solutions:**

1. **Firewall/Proxy**
   - Check corporate firewall rules
   - Verify WebSocket protocol allowed
   - Try different port if blocked

2. **Browser Issues**
   - Update to latest browser version
   - Disable problematic extensions
   - Try different browser

3. **Server Configuration**
   - Increase WebSocket timeout
   - Check server load
   - Review rate limiting rules

## UI/UX Issues

### Animations Not Working

**Symptoms:**
- No transition effects
- Instant state changes
- Missing visual feedback

**Solutions:**

1. **CSS Loading**
   - Verify `connection-animations.css` is loaded
   - Check browser console for CSS errors

2. **Browser Compatibility**
   - Ensure browser supports CSS animations
   - Check for vendor prefixes needed

3. **Performance Mode**
   - Disable browser "reduce motion" setting
   - Check if hardware acceleration is enabled

### Toast Notifications Not Appearing

**Symptoms:**
- No disconnect notifications
- Missing reconnection alerts
- Silent state changes

**Solutions:**

1. **Event Listeners**
   - Verify toast container is mounted
   - Check event listeners are registered

2. **Z-Index Issues**
   - Ensure toasts have high z-index
   - Check for overlapping elements

3. **Browser Permissions**
   - Some browsers block notifications
   - Check console for permission errors

## Performance Issues

### Slow Bot Decisions

**Symptoms:**
- Long delay before bot plays
- UI freezes during bot turn
- Timeout errors

**Solutions:**

1. **AI Optimization**
   - Profile AI decision time
   - Add caching for common scenarios
   - Simplify complex calculations

2. **Async Processing**
   - Ensure AI runs asynchronously
   - Don't block main thread

3. **Timeout Adjustment**
   - Increase bot decision timeout
   - Add loading indicator

### Memory Leaks

**Symptoms:**
- Browser tab uses excessive memory
- Performance degrades over time
- Page becomes unresponsive

**Solutions:**

1. **Event Listener Cleanup**
   - Remove listeners on unmount
   - Check for circular references

2. **Message Queue Limits**
   - Ensure queues have size limits
   - Clear old messages periodically

3. **State Management**
   - Limit state history size
   - Clear unnecessary data

## Debug Commands

### Backend Debugging

```python
# Check all connections
from backend.api.websocket.connection_manager import connection_manager
connections = connection_manager.get_all_connections()

# Check message queues
from backend.api.websocket.message_queue import message_queue_manager
status = message_queue_manager.get_status()

# Force bot activation
player.is_bot = True
player.is_connected = False
```

### Frontend Debugging

```javascript
// Get current game state
const state = gameService.getState();
console.log('Full state:', state);

// Check connection status
const connStatus = networkService.getConnectionStatus();
console.log('Connection:', connStatus);

// Trigger test notification
showToast('info', 'Test notification');

// Force reconnection
networkService.reconnect();
```

### Network Debugging

```bash
# Check WebSocket connection
wscat -c ws://localhost:8000/ws/ROOM_ID

# Monitor network traffic
tcpdump -i any port 8000

# Test with curl
curl -N http://localhost:8000/api/rooms
```

## Contact Support

If issues persist after trying these solutions:

1. **Gather Information**
   - Browser console logs
   - Network tab screenshots
   - Backend error logs
   - Steps to reproduce

2. **Report Issue**
   - GitHub Issues: [Project Repository]
   - Include all gathered information
   - Specify browser and OS versions

3. **Temporary Workarounds**
   - Refresh page to reset state
   - Create new room if current is corrupted
   - Use different browser/device