# Game Start Grace Period Fix

## Problem
When starting a game, the host (Andy) would appear as disconnected in the notifications. This was a false positive caused by the WebSocket connection handover when transitioning from RoomPage to GamePage.

## Root Cause
During the navigation from `/room/{roomId}` to `/game/{roomId}`:
1. RoomPage WebSocket connection closes
2. GamePage creates a new WebSocket connection  
3. Backend detects the brief disconnect (~100ms) and broadcasts `player_disconnected` event
4. Toast notifications correctly show the disconnect, confusing users

## Solution Implemented
Added a 500ms grace period to suppress disconnect notifications immediately after game start.

### Changes Made

#### 1. `/frontend/src/hooks/useToastNotifications.js`
- Added `gameStartTime` ref to track when game starts
- Added `GRACE_PERIOD_MS = 500` constant
- Modified disconnect notification logic to check if within grace period
- Added event listener for 'game_started' event to set the grace period start time

#### 2. `/frontend/src/pages/GamePage.jsx`
- Added `window.dispatchEvent(new Event('game_started'))` at the beginning of game initialization
- This signals to the toast system that a game is starting

### How It Works
1. When GamePage mounts, it dispatches a 'game_started' event
2. useToastNotifications hook receives this event and records the timestamp
3. Any disconnect notifications within 500ms of game start are suppressed
4. After 500ms, all disconnect notifications work normally

### Benefits
- ✅ No more false disconnect notifications when starting a game
- ✅ Real disconnects during gameplay still show notifications
- ✅ Simple, focused solution
- ✅ No changes to connection handling or backend
- ✅ Grace period is easily adjustable if needed

### Testing
To verify the fix:
1. Start a game - should see NO disconnect notifications
2. After game starts, disconnect a player - should see notification appear
3. Rapid disconnect/reconnect during gameplay - should see all notifications

The grace period only applies to the first 500ms after game start, ensuring all legitimate disconnects are still reported to players.