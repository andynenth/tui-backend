# Debug Logging Added for Grace Period Investigation

## Purpose
To investigate why the grace period mechanism isn't preventing false disconnect notifications when starting a game.

## Debug Logs Added

### 1. GamePage.jsx
Added logging when dispatching the game_started event:
- `🎮 GamePage: Dispatching game_started event at [timestamp]`
- `🎮 GamePage: game_started event dispatched`

### 2. useToastNotifications.js
Added comprehensive logging:
- `🔔 useToastNotifications: Listening for game_started event` - When hook initializes
- `🔔 useToastNotifications: Received game_started event, grace period starts at [timestamp]` - When event received
- Detailed disconnect notification check with all timing information:
  ```
  🔔 Disconnect notification check: {
    playerName,
    gameStartTime,
    now,
    timeSinceGameStart,
    GRACE_PERIOD_MS,
    isWithinGracePeriod,
    willShowToast
  }
  ```
- `🔔 Showing disconnect toast for [playerName]` - When showing toast
- `🔔 Suppressing disconnect toast for [playerName] (within grace period)` - When suppressing

## What to Look For in Logs

1. **Event Dispatch**: Look for "Dispatching game_started event" to confirm GamePage is firing the event
2. **Event Reception**: Look for "Received game_started event" to confirm the toast hook is receiving it
3. **Timing**: Check the timestamps to see if the disconnect events are happening after the grace period
4. **Grace Period Logic**: The detailed logs will show exactly why notifications are or aren't being suppressed

## Next Steps
Run the application and check the browser console for these debug messages when starting a game. This will reveal:
- If the event system is working
- The exact timing of events
- Why the grace period isn't preventing the notifications