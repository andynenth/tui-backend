# Disconnect Handling Documentation

## Overview

The Liap Tui game implements a comprehensive disconnect handling system that ensures seamless gameplay even when players lose their connection. The system features:

- **Unlimited Reconnection Time**: Players can reconnect anytime while the game is active
- **Automatic Bot Takeover**: AI immediately takes control when a player disconnects
- **Message Queue System**: Critical game events are stored for disconnected players
- **Host Migration**: Automatic host transfer when the room host disconnects
- **Professional UI Feedback**: Clear visual indicators and smooth animations

## How It Works

### 1. Player Disconnection

When a player's WebSocket connection is lost:

1. The backend detects the disconnect via WebSocket close event
2. The player's `is_bot` flag is set to `true` (bot takeover)
3. A message queue is created to store game events
4. Other players see an "AI Playing" indicator
5. The game continues without interruption

### 2. Bot Behavior

The AI bot that takes over:
- Makes intelligent decisions based on game state
- Follows the same rules as human players
- Maintains the player's strategy and score
- Acts within reasonable time limits

### 3. Reconnection Process

When a disconnected player returns:

1. They connect to the same room with their player name
2. The backend recognizes them and restores control
3. Queued messages are delivered to sync game state
4. The bot is deactivated (`is_bot` returns to `false`)
5. Other players see the reconnection notification

### 4. Host Migration

If the room host disconnects:
- The system automatically selects a new host
- Preference is given to human players over bots
- The new host gains room management privileges
- All players are notified of the host change

## Technical Implementation

### Backend Components

#### ConnectionManager (`backend/api/websocket/connection_manager.py`)
- Tracks all player connections
- Manages connection states (connected, disconnected)
- No grace period - unlimited reconnection time

#### MessageQueueManager (`backend/api/websocket/message_queue.py`)
- Stores game events for disconnected players
- Prioritizes critical events (phase changes, scores)
- Delivers queued messages on reconnection
- Automatic overflow handling

#### WebSocket Handler (`backend/api/routes/ws.py`)
- Detects disconnections and triggers bot activation
- Handles reconnection and state restoration
- Broadcasts connection events to all players

### Frontend Components

#### GameService (`frontend/src/services/GameService.ts`)
- Tracks disconnected players in game state
- Handles disconnect/reconnect events
- Updates UI based on connection status

#### UI Components
- **ConnectionQuality**: Shows network strength and latency
- **ReconnectionProgress**: Displays reconnection attempts
- **EnhancedPlayerAvatar**: Smooth bot/human transitions
- **EnhancedToastContainer**: Stacking notifications

## User Experience

### Visual Indicators

1. **Disconnected Player**
   - Avatar becomes semi-transparent
   - "AI" badge appears
   - Robot icon replaces player initial

2. **Connection Quality**
   - Signal strength bars (1-4)
   - Latency display in milliseconds
   - Color coding (green/yellow/red)

3. **Reconnection**
   - Progress bar during reconnection
   - Success animation with checkmark
   - Toast notification for all players

### Notifications

Players receive clear notifications for:
- Player disconnections ("AI Playing for: [name]")
- Player reconnections ("[name] has reconnected")
- Host changes ("New host: [name]")
- Connection quality warnings

## Best Practices

### For Players

1. **Don't Panic**: Your game continues with AI assistance
2. **Reconnect Anytime**: No time limit for reconnection
3. **Check Connection**: Monitor the quality indicator
4. **Same Name**: Use the same player name to reconnect

### For Developers

1. **Event Handling**: Always use `broadcast_with_queue()` for game events
2. **State Sync**: Ensure phase_change includes full game state
3. **Error Handling**: Gracefully handle reconnection edge cases
4. **Testing**: Test with network throttling and disconnections

## Troubleshooting

### Common Issues

**Issue**: Player can't reconnect
- **Solution**: Ensure using the same player name and room is still active

**Issue**: Missing game events after reconnect
- **Solution**: Check message queue is working and critical events are marked

**Issue**: Bot making poor decisions
- **Solution**: Review AI logic for the specific game phase

**Issue**: Host migration not working
- **Solution**: Verify room has valid players and migration logic is correct

### Debug Tools

1. **Connection Status**
   ```javascript
   // Check connection in browser console
   gameService.getState().disconnectedPlayers
   ```

2. **Message Queue Status**
   ```python
   # Check queue status on backend
   message_queue_manager.get_status()
   ```

3. **Network Logs**
   - Browser DevTools Network tab
   - Backend logs for disconnect events

## Configuration

### Backend Settings

```python
# Message queue size (default: 100)
PlayerQueue.max_size = 100

# Critical event types
MessageQueueManager.CRITICAL_EVENTS = {
    'phase_change',
    'turn_resolved',
    'round_complete',
    'game_ended',
    'score_update',
    'host_changed'
}
```

### Frontend Settings

```javascript
// Toast notification duration (ms)
const TOAST_DURATION = 5000;

// Connection quality thresholds (ms)
const QUALITY_THRESHOLDS = {
  excellent: 50,
  good: 100,
  fair: 200,
  poor: Infinity
};
```

## Security Considerations

1. **Authentication**: Player names are not authenticated
2. **Room Access**: Anyone with room ID can attempt to join
3. **Message Validation**: All WebSocket messages are validated
4. **Rate Limiting**: Connection attempts are rate-limited

## Future Enhancements

1. **Persistent Sessions**: Save game state to database
2. **Authentication**: Secure player identity verification
3. **Spectator Mode**: Allow disconnected players to watch
4. **Mobile Optimization**: Better handling of mobile disconnects
5. **Metrics Dashboard**: Connection quality analytics