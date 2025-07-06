# UI Implementation Plan

This document outlines the implementation plan for transitioning the mockup HTML designs into the React component system without modifying the backend.

## Overview

We need to implement three key UI pages based on the HTML mockups:
1. **start-page-mockup.html** → StartPage.jsx
2. **room-page-alt-display-mockup.html** → RoomPage.jsx  
3. **lobby-page-simplified-mockup.html** → LobbyPage.jsx

## Current System Analysis

### Existing Infrastructure
- **React 19.1.0** with React Router DOM
- **Tailwind CSS** for styling (via `@import 'tailwindcss'`)
- **Component Library**: Button, Input, Layout, Modal, LoadingOverlay
- **Network Service**: WebSocket communication via `networkService`
- **App Context**: Player name and navigation management

### Current Page Functions
1. **StartPage.jsx**
   - Player name input/validation
   - Navigation to lobby
   - Form handling with react-hook-form

2. **RoomPage.jsx**
   - Room connection management
   - Player slot display (grid layout)
   - Bot add/remove functionality
   - Game start control
   - Leave room functionality

3. **LobbyPage.jsx** 
   - Room list display
   - Create/join room
   - Refresh room list
   - Connection status

## Implementation Tasks

### Phase 1: Custom CSS Setup

#### Task 1.1: Create Theme CSS Module
- [ ] Create `/frontend/src/styles/theme.css`
- [ ] Import Google Fonts: Plus Jakarta Sans, Crimson Pro
- [ ] Define CSS variables for colors, gradients, shadows
- [ ] Create animation keyframes (pulse, spin, float)

#### Task 1.2: Create Component CSS Modules
- [ ] Create `/frontend/src/styles/components/startpage.module.css`
- [ ] Create `/frontend/src/styles/components/roompage.module.css`
- [ ] Create `/frontend/src/styles/components/lobbypage.module.css`
- [ ] Import modules in respective components

### Phase 2: StartPage Implementation

#### Task 2.1: Update Page Structure
- [ ] Replace current gradient background with paper texture design
- [ ] Implement floating game pieces animation
- [ ] Update container to match 9:16 aspect ratio styling

#### Task 2.2: Enhance Form Design
- [ ] Style input field with gradient borders and focus effects
- [ ] Update button with gradient background and hover animations
- [ ] Add helper text styling

#### Task 2.3: Add Game Icon Animation
- [ ] Create animated dice/pieces icon component
- [ ] Implement rotation and floating animations
- [ ] Position above the title

### Phase 3: RoomPage Implementation

#### Task 3.1: Replace Grid Layout with Table Visualization
- [ ] Create table surface component with wood texture styling
- [ ] Position player cards around the table (4 positions)
- [ ] Add green felt inlay effect

#### Task 3.2: Update Player Cards
- [ ] Remove avatars (as per mockup)
- [ ] White background with colored borders
- [ ] Host badge styling (gold gradient)
- [ ] Bot naming convention (Bot 2, Bot 3, Bot 4)

#### Task 3.3: Update Room Header
- [ ] Add room ID badge with yellow accent
- [ ] Update subtitle based on room state:
  - "Waiting for players to join" (not full)
  - "All players ready - Start the game!" (full)

#### Task 3.4: Style Control Buttons
- [ ] Green gradient for Start Game button
- [ ] White/gray for Leave Room button
- [ ] Proper disabled states

### Phase 4: LobbyPage Implementation

#### Task 4.1: Update Header Section
- [ ] Add player info badge (top left)
- [ ] Simplify connection status badge
- [ ] Remove API toggle functionality

#### Task 4.2: Enhance Room List
- [ ] Implement custom scrollbar styling
- [ ] Create room card components with hover effects
- [ ] Add player slot visualization (filled/empty/bot)
- [ ] Show room occupancy badges

#### Task 4.3: Update Action Bar
- [ ] Position refresh button to the right
- [ ] Style Create Room and Join by ID buttons
- [ ] Add loading spinner animation

#### Task 4.4: Update Footer
- [ ] Change to "← Back to Start Page"
- [ ] Remove "Change Name" functionality

### Phase 5: Component Updates

#### Task 5.1: Create Reusable Components
- [ ] ConnectionStatus component (green/red pill)
- [ ] RoomIdBadge component
- [ ] PlayerSlot component (for room cards)
- [ ] AnimatedIcon component (for start page)

#### Task 5.2: Update Existing Components
- [ ] Extend Button component with gradient variants
- [ ] Update Modal styling to match mockup design
- [ ] Enhance LoadingOverlay with custom spinner

### Phase 6: Integration & Testing

#### Task 6.1: Function Mapping
- [ ] Map existing WebSocket events to new UI
- [ ] Ensure all current functionality is preserved
- [ ] Test room creation/joining flow
- [ ] Test game start flow

#### Task 6.2: Responsive Design
- [ ] Test 9:16 aspect ratio container
- [ ] Ensure mobile compatibility
- [ ] Test on different screen sizes

#### Task 6.3: Animation Performance
- [ ] Optimize CSS animations
- [ ] Test on lower-end devices
- [ ] Add reduced motion support

## Technical Considerations

### CSS Architecture
```
/frontend/src/styles/
├── globals.css          # Keep existing Tailwind imports
├── theme.css           # New: Global theme variables
└── components/         # New: Component-specific styles
    ├── startpage.module.css
    ├── roompage.module.css
    └── lobbypage.module.css
```

### Tailwind Integration
- Use Tailwind for layout utilities (flex, grid, spacing)
- Use custom CSS for:
  - Complex gradients
  - Custom animations
  - Paper textures
  - Special effects (shadows, borders)

### Component Structure
```jsx
// Example: RoomPage.jsx
import styles from '../styles/components/roompage.module.css';

const RoomPage = () => {
  return (
    <div className={`${styles.gameContainer} relative`}>
      {/* Mix Tailwind utilities with CSS modules */}
    </div>
  );
};
```

## Implementation Order

1. **Week 1**: Phase 1 (CSS Setup) + Phase 2 (StartPage)
2. **Week 2**: Phase 3 (RoomPage) + Phase 4 (LobbyPage)
3. **Week 3**: Phase 5 (Components) + Phase 6 (Integration)

## Success Criteria

- [ ] All three pages match the visual design of mockups
- [ ] No loss of existing functionality
- [ ] Smooth animations and transitions
- [ ] Consistent design language across pages
- [ ] Performance optimization (< 60fps animations)
- [ ] Accessible (keyboard navigation, screen readers)

## Common Pitfalls to Avoid

1. **CSS Specificity Issues**
   - Use CSS modules to avoid global conflicts
   - Don't use !important unless absolutely necessary
   - Keep Tailwind utilities for layout, custom CSS for styling

2. **Animation Performance**
   - Always use transform and opacity for animations
   - Avoid animating width, height, or position properties
   - Use will-change sparingly

3. **State Management**
   - Don't duplicate WebSocket state in components
   - Keep single source of truth in existing state management
   - Use React.memo for expensive renders

4. **Responsive Design**
   - Test on actual devices, not just browser resize
   - Consider touch targets (minimum 44x44px)
   - Test with different font sizes (accessibility)

## Notes

- Backend remains unchanged - only frontend UI updates
- WebSocket communication patterns stay the same
- Player data structure and game logic unchanged
- Focus on visual enhancement while maintaining functionality

## Detailed Implementation Specifications

### Color Palette & Variables

```css
/* theme.css */
:root {
  /* Primary Colors */
  --color-primary: #0D6EFD;
  --color-primary-dark: #0056B3;
  --color-success: #28A745;
  --color-success-light: #20C997;
  --color-warning: #FFC107;
  --color-warning-dark: #FF9800;
  --color-danger: #DC3545;
  --color-danger-dark: #C82333;
  
  /* Neutral Colors */
  --color-gray-50: #F8F9FA;
  --color-gray-100: #E9ECEF;
  --color-gray-200: #DEE2E6;
  --color-gray-300: #CED4DA;
  --color-gray-400: #ADB5BD;
  --color-gray-500: #6C757D;
  --color-gray-600: #495057;
  --color-gray-700: #343A40;
  --color-gray-800: #212529;
  
  /* Gradients */
  --gradient-gray: linear-gradient(135deg, #F8F9FA 0%, #E9ECEF 25%, #DEE2E6 50%, #CED4DA 75%, #ADB5BD 100%);
  --gradient-success: linear-gradient(135deg, #28A745 0%, #20C997 100%);
  --gradient-warning: linear-gradient(135deg, #FFC107 0%, #FF9800 100%);
  --gradient-danger: linear-gradient(135deg, #DC3545 0%, #C82333 100%);
  --gradient-primary: linear-gradient(135deg, #0D6EFD 0%, #0056B3 100%);
  --gradient-white: linear-gradient(145deg, #FFFFFF 0%, #F8F9FA 100%);
  
  /* Shadows */
  --shadow-sm: 0 2px 6px rgba(0, 0, 0, 0.04);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.08);
  --shadow-lg: 0 8px 20px rgba(0, 0, 0, 0.12);
  --shadow-xl: 0 20px 40px rgba(0, 0, 0, 0.15);
  
  /* Table Surface (Wood Texture) */
  --gradient-wood: linear-gradient(135deg, #E8D5B7 0%, #D4A574 50%, #C19A6B 100%);
  --color-felt: rgba(34, 139, 34, 0.15);
  
  /* Animations */
  --transition-base: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  --transition-fast: all 0.15s ease;
}
```

### Animation Keyframes

```css
/* animations.css */
@keyframes float {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  33% { transform: translateY(-10px) rotate(5deg); }
  66% { transform: translateY(-5px) rotate(-3deg); }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes slideInFromBottom {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
```

### Component CSS Specifications

#### StartPage Specific Styles

```css
/* startpage.module.css */
.gameContainer {
  width: min(100vw, 56.25vh);
  height: min(100vh, 177.78vw);
  max-width: 400px;
  max-height: 711px;
  background: var(--gradient-white);
  border-radius: 20px;
  position: relative;
  overflow: hidden;
}

.floatingPiece {
  position: absolute;
  animation: float 4s ease-in-out infinite;
  font-size: 24px;
  opacity: 0.15;
}

.floatingPiece:nth-child(1) { 
  top: 10%; left: 10%; 
  animation-delay: 0s;
}

.floatingPiece:nth-child(2) { 
  top: 20%; right: 15%; 
  animation-delay: 1s;
}

.animatedIcon {
  font-size: 72px;
  animation: spin 8s linear infinite;
  margin-bottom: 24px;
}

.glowingInput:focus {
  background: rgba(255, 251, 240, 0.5);
  border-color: var(--color-warning);
  box-shadow: 0 0 0 3px rgba(255, 193, 7, 0.1);
}
```

#### RoomPage Table Layout

```css
/* roompage.module.css */
.tableSurface {
  width: 280px;
  height: 280px;
  background: var(--gradient-wood);
  border-radius: 24px;
  border: 3px solid rgba(139, 90, 43, 0.3);
  box-shadow: 
    inset 0 2px 12px rgba(0, 0, 0, 0.15),
    inset 0 -2px 8px rgba(255, 255, 255, 0.2),
    0 8px 24px rgba(0, 0, 0, 0.15);
  position: relative;
}

.tableFelt {
  position: absolute;
  inset: 20px;
  background: var(--color-felt);
  border: 1px solid rgba(34, 139, 34, 0.2);
  border-radius: 16px;
}

.playerSeat {
  position: absolute;
  width: 100px;
  text-align: center;
}

.playerSeat.position1 { top: -50px; left: 50%; transform: translateX(-50%); }
.playerSeat.position2 { right: -50px; top: 50%; transform: translateY(-50%); }
.playerSeat.position3 { bottom: -50px; left: 50%; transform: translateX(-50%); }
.playerSeat.position4 { left: -50px; top: 50%; transform: translateY(-50%); }

.playerCard {
  background: white;
  border: 2px solid var(--color-gray-300);
  border-radius: 12px;
  padding: 12px;
  transition: var(--transition-base);
}

.playerCard.filled { border-color: var(--color-success); }
.playerCard.host { border-color: var(--color-warning); }
```

#### LobbyPage Room Cards

```css
/* lobbypage.module.css */
.roomList {
  overflow-y: auto;
  overflow-x: hidden;
  flex: 1;
  padding-right: 4px;
}

.roomList::-webkit-scrollbar { width: 6px; }
.roomList::-webkit-scrollbar-track { 
  background: rgba(173, 181, 189, 0.1); 
  border-radius: 3px;
}
.roomList::-webkit-scrollbar-thumb { 
  background: rgba(173, 181, 189, 0.3); 
  border-radius: 3px;
}
.roomList::-webkit-scrollbar-thumb:hover { 
  background: rgba(173, 181, 189, 0.5); 
}

.roomCard {
  background: var(--gradient-white);
  border: 1px solid rgba(173, 181, 189, 0.15);
  border-radius: 10px;
  padding: 12px;
  transition: var(--transition-base);
  cursor: pointer;
}

.roomCard:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
  border-color: rgba(13, 110, 253, 0.3);
}

.playerSlot {
  width: 22%;
  padding: 6px;
  border-radius: 6px;
  font-size: 11px;
  text-align: center;
}

.playerSlot.filled {
  background: rgba(40, 167, 69, 0.1);
  border: 1px solid rgba(40, 167, 69, 0.3);
  color: var(--color-success);
}

.playerSlot.empty {
  background: rgba(108, 117, 125, 0.1);
  border: 1px dashed rgba(108, 117, 125, 0.2);
  color: var(--color-gray-400);
}
```

### React Component Integration Examples

#### StartPage Integration

```jsx
// StartPage.jsx
import styles from '../styles/components/startpage.module.css';

const StartPage = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100">
      <div className={styles.gameContainer}>
        {/* Floating pieces background */}
        <div className={styles.floatingPiece}>🎲</div>
        <div className={styles.floatingPiece}>♠️</div>
        <div className={styles.floatingPiece}>♥️</div>
        <div className={styles.floatingPiece}>♣️</div>
        <div className={styles.floatingPiece}>♦️</div>
        
        <div className="flex flex-col items-center justify-center h-full px-8">
          <div className={styles.animatedIcon}>🎮</div>
          <h1 className="text-3xl font-bold mb-2">Welcome to Liap TUI</h1>
          {/* Rest of the component */}
        </div>
      </div>
    </div>
  );
};
```

#### RoomPage Table Layout Integration

```jsx
// RoomPage.jsx
import styles from '../styles/components/roompage.module.css';

const RoomPage = () => {
  const renderTableView = () => (
    <div className="flex items-center justify-center p-20">
      <div className={styles.tableSurface}>
        <div className={styles.tableFelt} />
        
        {[1, 2, 3, 4].map((position) => {
          const player = roomData?.players?.[position - 1];
          return (
            <div key={position} className={`${styles.playerSeat} ${styles[`position${position}`]}`}>
              <div className="text-xs font-bold text-gray-500 mb-2">Seat {position}</div>
              <div className={`${styles.playerCard} ${player ? styles.filled : ''} ${player?.is_host ? styles.host : ''}`}>
                <div className="font-semibold">
                  {player ? (player.is_bot ? `Bot ${position}` : player.name) : 'Waiting...'}
                </div>
                {player?.is_host && (
                  <span className={styles.hostBadge}>Host</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
  
  return (
    <Layout>
      {/* Room header */}
      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold">Game Room</h1>
        <p className="text-gray-600">
          {isRoomFull ? 'All players ready - Start the game!' : 'Waiting for players to join'}
        </p>
      </div>
      
      {renderTableView()}
      
      {/* Game controls */}
    </Layout>
  );
};
```

#### LobbyPage Simplified Integration

```jsx
// LobbyPage.jsx
import styles from '../styles/components/lobbypage.module.css';

const LobbyPage = () => {
  const renderRoomCard = (room) => {
    const playerCount = room.players?.filter(p => p !== null).length || 0;
    const canJoin = !room.started && playerCount < 4;
    
    return (
      <div 
        key={room.room_id} 
        className={`${styles.roomCard} ${!canJoin ? styles.full : ''}`}
        onClick={() => canJoin && joinRoom(room.room_id)}
      >
        <div className="flex justify-between items-center mb-2">
          <div className="flex items-center gap-2">
            <div className={styles.roomIdBadge}>{room.room_id}</div>
            <span className="text-xs text-gray-500">Host: {room.host_name}</span>
          </div>
          <div className={`${styles.occupancyBadge} ${playerCount === 4 ? styles.full : ''}`}>
            {playerCount}/4
          </div>
        </div>
        
        <div className="flex gap-1">
          {[0, 1, 2, 3].map((slot) => {
            const player = room.players?.[slot];
            return (
              <div 
                key={slot} 
                className={`${styles.playerSlot} ${player ? styles.filled : styles.empty}`}
              >
                {player ? (player.is_bot ? `Bot ${slot + 1}` : player.name) : 'Empty'}
              </div>
            );
          })}
        </div>
      </div>
    );
  };
  
  return (
    <Layout>
      {/* Action bar with refresh button aligned right */}
      <div className="flex justify-between items-center mb-4">
        <div className="flex gap-2">
          <Button onClick={createRoom}>➕ Create Room</Button>
          <Button variant="outline" onClick={() => setShowJoinModal(true)}>🔗 Join by ID</Button>
        </div>
        <Button variant="ghost" onClick={refreshRooms} className={styles.refreshButton}>
          <span className={isRefreshing ? styles.spinning : ''}>🔄</span>
        </Button>
      </div>
      
      <div className={styles.roomList}>
        {rooms.map(renderRoomCard)}
      </div>
      
      <div className="text-center mt-4">
        <button onClick={() => navigate('/')} className={styles.backButton}>
          ← Back to Start Page
        </button>
      </div>
    </Layout>
  );
};
```

### Utility Functions

```javascript
// utils/roomHelpers.js
export const getBotName = (slotNumber) => {
  // Ensure consistent bot naming
  return `Bot ${slotNumber}`;
};

export const getRoomStatusText = (occupancy, maxPlayers = 4) => {
  if (occupancy === maxPlayers) {
    return 'All players ready - Start the game!';
  }
  return 'Waiting for players to join';
};

export const getPlayerDisplayName = (player, slotNumber) => {
  if (!player) return 'Waiting...';
  if (player.is_bot) return getBotName(slotNumber);
  return player.name;
};
```

### Migration Checklist

- [ ] **Phase 1 Completion**
  - [ ] Create theme.css with all CSS variables
  - [ ] Create animations.css with keyframes
  - [ ] Setup CSS module infrastructure
  - [ ] Test CSS module imports in components

- [ ] **Phase 2 Completion**
  - [ ] StartPage floating pieces animation working
  - [ ] Form styling matches mockup
  - [ ] Animated game icon implemented
  - [ ] Responsive container working

- [ ] **Phase 3 Completion**
  - [ ] Table visualization rendering correctly
  - [ ] Player positions around table working
  - [ ] Bot naming convention implemented
  - [ ] Room subtitle updates when full

- [ ] **Phase 4 Completion**
  - [ ] Room list with custom scrollbar
  - [ ] Room cards hover effects
  - [ ] Player slots visualization
  - [ ] Back to Start Page link

- [ ] **Phase 5 Completion**
  - [ ] All reusable components created
  - [ ] Component props properly typed
  - [ ] Consistent styling across components

- [ ] **Phase 6 Completion**
  - [ ] All functionality preserved
  - [ ] Animations performant
  - [ ] Responsive design tested
  - [ ] Accessibility verified

## Final Testing Scenarios

1. **Start Page Flow**
   - Enter name with validation
   - See floating animations
   - Navigate to lobby

2. **Lobby Flow**
   - View room list with scroll
   - Create new room
   - Join existing room
   - Refresh room list
   - Navigate back to start

3. **Room Flow**
   - See table visualization
   - Add/remove bots
   - See room fill status
   - Start game when full
   - Leave room

4. **Edge Cases**
   - Long player names
   - Many rooms in lobby (scrolling)
   - Connection loss/reconnect
   - Rapid state changes

## Performance Guidelines

- Use CSS transforms for animations (GPU accelerated)
- Lazy load heavy components
- Memoize expensive calculations
- Use CSS containment for animated elements
- Test on throttled CPU (Chrome DevTools)

## Accessibility Requirements

- All interactive elements keyboard accessible
- ARIA labels for icon buttons
- Focus indicators visible
- Reduced motion media query support
- Color contrast WCAG AA compliant