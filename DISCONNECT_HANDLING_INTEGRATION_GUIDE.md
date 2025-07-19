# Disconnect Handling Integration Guide

This guide provides step-by-step tasks to integrate the existing disconnect handling components into the Liap Tui game. Each task is independent and can be implemented one at a time.

## Overview

The disconnect handling system consists of several components that were created but not fully integrated:
- **ConnectionIndicator**: Shows real-time connection status
- **EnhancedPlayerAvatar**: Displays player disconnect states with animations
- **ToastNotifications**: Shows disconnect/reconnect alerts
- **ReconnectionPrompt**: Modal for returning players
- **ReconnectionProgress**: Progress bar during reconnection

## Current Issues

1. **ConnectionIndicator is hidden** - All pages set `showConnection={false}`
2. **PlayerAvatar not enhanced** - Using basic version without disconnect features
3. **Toast notifications not triggering** - Hook exists but may not detect events
4. **No reconnection UI** - Components exist but aren't shown

---

## Task 1: Enable Connection Indicator

### What It Does
Shows a real-time connection status indicator in the top-right corner with the room ID and connection state.

### Implementation Steps

#### 1.1 Enable in RoomPage
**File**: `/frontend/src/pages/RoomPage.jsx`
**Line**: ~161
```jsx
// Change from:
<Layout title="" showConnection={false} showHeader={false}>

// To:
<Layout 
  title="" 
  showConnection={true} 
  showHeader={false}
  connectionProps={{
    roomId: roomId,
    isConnected: true, // TODO: Get from connectionStatus
  }}
>
```

#### 1.2 Enable in LobbyPage
**File**: `/frontend/src/pages/LobbyPage.jsx`
**Line**: ~286
```jsx
// Change from:
<Layout title="" showConnection={false} showHeader={false}>

// To:
<Layout 
  title="" 
  showConnection={true} 
  showHeader={false}
  connectionProps={{
    roomId: 'lobby',
    isConnected: true, // TODO: Get from connectionStatus
  }}
>
```

#### 1.3 Add to GamePage
**File**: `/frontend/src/pages/GamePage.jsx`
**Location**: Wrap GameContainer with Layout
```jsx
// Add Layout wrapper around GameContainer
return (
  <ErrorBoundary>
    <Layout 
      title="" 
      showConnection={true} 
      showHeader={true}
      connectionProps={{
        roomId: roomId,
        isConnected: connectionStatus?.isConnected || false,
        isConnecting: connectionStatus?.isConnecting || false,
        error: connectionStatus?.error,
      }}
    >
      <GameContainer
        playerName={playerName}
        // ... other props
      />
      <ToastContainer position="top-right" maxToasts={5} />
    </Layout>
  </ErrorBoundary>
);
```

### Testing
1. Navigate to each page (Lobby, Room, Game)
2. Verify connection indicator appears in top-right
3. Check that room ID is displayed correctly

---

## Task 2: Replace PlayerAvatar with EnhancedPlayerAvatar

### What It Does
EnhancedPlayerAvatar adds:
- Smooth animations when players disconnect/reconnect
- Bot indicator with transition effects
- Connection quality display (optional)
- Host crown indicator

### Implementation Steps

#### 2.1 In RoomPage
**File**: `/frontend/src/pages/RoomPage.jsx`
**Import Section**: Add import
```jsx
import EnhancedPlayerAvatar from '../components/EnhancedPlayerAvatar';
// Remove or comment out: import PlayerAvatar from '../components/game/shared/PlayerAvatar';
```

**Replace Usage**: Find PlayerAvatar usage and replace
```jsx
// Change from:
<PlayerAvatar
  player={player}
  size="large"
  showName={true}
/>

// To:
<EnhancedPlayerAvatar
  player={player}
  size="large"
  isHost={player.name === room.host}
  showConnectionQuality={false}
  roomId={roomId}
/>
```

#### 2.2 In TurnContent
**File**: `/frontend/src/components/game/content/TurnContent.jsx`
**Import Section**: Update import
```jsx
import EnhancedPlayerAvatar from '../../EnhancedPlayerAvatar';
// Remove: import { PlayerAvatar } from '../shared';
```

**Replace Usage**: In the player list rendering
```jsx
// Change from:
<PlayerAvatar 
  player={playerData} 
  isCurrentPlayer={isCurrentPlayer}
  size="medium"
/>

// To:
<EnhancedPlayerAvatar
  player={playerData}
  isHost={false} // Or check if player is host
  showConnectionQuality={false}
  roomId={gameState.roomId}
  size="medium"
  className={isCurrentPlayer ? 'current-player' : ''}
/>
```

#### 2.3 In DeclarationContent
**File**: `/frontend/src/components/game/content/DeclarationContent.jsx`
**Similar replacement as above**

#### 2.4 In ScoringContent
**File**: `/frontend/src/components/game/content/ScoringContent.jsx`
**Similar replacement as above**

### Testing
1. Join a game with multiple players
2. Have one player disconnect (close browser)
3. Verify smooth animation to bot indicator
4. Verify host crown shows correctly
5. Have player reconnect and verify animation back

---

## Task 3: Fix Toast Notifications

### What It Does
Shows toast notifications for:
- Player disconnections ("Player X disconnected")
- Bot activation ("AI is now playing for X")
- Player reconnections ("Player X reconnected")
- Host migration ("Player Y is now the host")

### Implementation Steps

#### 3.1 Debug useToastNotifications Hook
**File**: `/frontend/src/hooks/useToastNotifications.js`
**Add console logs to debug**:
```jsx
// Around line 55, add debugging:
useEffect(() => {
  console.log('🔔 Toast hook monitoring gameState:', gameState);
  
  if (!gameState || !gameState.players) {
    console.log('🔔 No gameState or players to monitor');
    return;
  }

  // Compare with previous state
  const currentDisconnected = gameState.disconnectedPlayers || [];
  console.log('🔔 Disconnected players:', currentDisconnected);
  console.log('🔔 Previous disconnected:', previousDisconnectedPlayers.current);
```

#### 3.2 Ensure GameService Updates State
**File**: `/frontend/src/services/GameService.ts`
**Check handlePlayerDisconnected method**:
```typescript
// Verify this method updates state correctly
handlePlayerDisconnected(data) {
  console.log('🎮 GameService: Player disconnected', data);
  this.updateState({
    disconnectedPlayers: [...(this.state.disconnectedPlayers || []), data.player_name],
    players: this.state.players.map(p => 
      p.name === data.player_name ? { ...p, is_bot: true, is_connected: false } : p
    )
  });
}
```

#### 3.3 Add Manual Toast Trigger (for testing)
**File**: `/frontend/src/pages/GamePage.jsx`
**Add test button temporarily**:
```jsx
// Add this inside the component for testing
const testToast = () => {
  window.dispatchEvent(new CustomEvent('show-toast', {
    detail: {
      type: 'disconnect',
      title: 'Test Disconnect',
      message: 'Player Test has disconnected'
    }
  }));
};

// Add button in render:
{process.env.NODE_ENV === 'development' && (
  <button onClick={testToast} style={{ position: 'fixed', bottom: 20, left: 20 }}>
    Test Toast
  </button>
)}
```

### Testing
1. Open browser console to see debug logs
2. Have a player disconnect
3. Check if toast appears
4. Use test button to verify toast rendering works
5. Remove test button when done

---

## Task 4: Add Reconnection Prompt

### What It Does
Shows a modal when a player returns to the game, offering to rejoin or start fresh.

### Implementation Steps

#### 4.1 Add to App.jsx
**File**: `/frontend/src/App.jsx`
**Import ReconnectionPrompt**:
```jsx
import ReconnectionPrompt from './components/ReconnectionPrompt';
```

**Add state and logic in AppWithServices**:
```jsx
const [showReconnectPrompt, setShowReconnectPrompt] = useState(false);
const [reconnectSession, setReconnectSession] = useState(null);

// In useEffect after session check:
if (hasValidSession()) {
  const session = getSession();
  console.log('🎮 Found stored session:', session);
  // Instead of auto-reconnecting, show prompt
  setReconnectSession(session);
  setShowReconnectPrompt(true);
}

// Add handlers:
const handleReconnect = async () => {
  if (reconnectSession) {
    setSessionToRecover(reconnectSession);
    setShowReconnectPrompt(false);
  }
};

const handleJoinAsNew = () => {
  clearSession();
  setShowReconnectPrompt(false);
  setReconnectSession(null);
};

// In render, add before router:
{showReconnectPrompt && (
  <ReconnectionPrompt
    sessionInfo={reconnectSession}
    onReconnect={handleReconnect}
    onJoinAsNew={handleJoinAsNew}
    isReconnecting={false}
    isDuplicateTab={false}
  />
)}
```

### Testing
1. Join a game
2. Close browser completely
3. Reopen browser and navigate to app
4. Verify reconnection prompt appears
5. Test both "Rejoin" and "Join as New" options

---

## Task 5: Add Reconnection Progress (Optional)

### What It Does
Shows a progress bar during reconnection attempts with retry count.

### Implementation Steps

#### 5.1 Add to GamePage
**File**: `/frontend/src/pages/GamePage.jsx`
**Import**:
```jsx
import ReconnectionProgress from '../components/ReconnectionProgress';
```

**Add state**:
```jsx
const [reconnectAttempt, setReconnectAttempt] = useState(0);
```

**Add to render**:
```jsx
{connectionStatus?.isReconnecting && (
  <ReconnectionProgress
    isReconnecting={true}
    attemptNumber={reconnectAttempt}
    maxAttempts={5}
    onCancel={() => {
      // Handle cancel
      navigate('/');
    }}
  />
)}
```

### Testing
1. Simulate connection loss
2. Verify progress bar appears
3. Check attempt counter increments
4. Test cancel button

---

## Task 6: Enable PlayerSlot Component (Optional)

### What It Does
PlayerSlot provides a better room slot UI with animations and bot controls.

### Note
⚠️ This component uses Tailwind CSS classes. Only implement if you plan to add Tailwind CSS to the project.

---

## Testing Checklist

After implementing all tasks:

- [ ] Connection indicator visible on all pages
- [ ] Connection indicator updates when disconnecting
- [ ] Player avatars show bot indicator when disconnected
- [ ] Toast notifications appear for disconnect events
- [ ] Reconnection prompt shows when returning to game
- [ ] Players can successfully reconnect
- [ ] Host migration notifications work
- [ ] Animations are smooth and not jarring

## Troubleshooting

### Toasts Not Appearing
1. Check browser console for errors
2. Verify `useToastNotifications` hook is detecting state changes
3. Ensure GameService is updating `disconnectedPlayers` array
4. Check CSS is loaded for toast styles

### Connection Indicator Not Updating
1. Verify `connectionStatus` hook is working
2. Check NetworkService connection state
3. Ensure WebSocket events are being handled

### EnhancedPlayerAvatar Not Animating
1. Check CSS animations are loaded
2. Verify player state changes are detected
3. Check browser supports CSS transitions

## Next Steps

Once basic integration is complete:
1. Add connection quality indicators
2. Implement automatic reconnection with exponential backoff
3. Add sound effects for disconnect/reconnect events
4. Create admin controls for managing disconnected players
5. Add reconnection history/logs for debugging