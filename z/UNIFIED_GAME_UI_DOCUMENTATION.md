# UnifiedGameUI Component Documentation

## Overview

UnifiedGameUI is a React component that provides a unified container for all game phases (Preparation, Declaration, Turn) with smooth transitions between phases. It maintains common UI elements while dynamically updating phase-specific content.

## Architecture

### Component Structure
```
UnifiedGameUI
├── Common Container (game-container)
│   ├── Fixed Badges (round indicator, multiplier)
│   ├── Phase Header (title, subtitle)
│   └── Dynamic Content Section
│       ├── Preparation Content
│       ├── Declaration Content
│       └── Turn Content (uses TableTurnUI)
├── Hand Section (always visible except during dealing)
└── Declaration Popup (modal for declarations)
```

### Key Features
1. **Unified Container**: Maintains consistent structure across phases
2. **Smooth Transitions**: Only content changes, not the entire UI
3. **Phase-Specific Content**: Each phase has its own content section
4. **Shared Elements**: Round indicator, multiplier badge, and hand section persist

## Implementation Guide

### 1. Basic Setup

```jsx
import UnifiedGameUI from './UnifiedGameUI';

// In your game container
<UnifiedGameUI
  phase="DECLARATION"  // Current phase
  myHand={gameState.myHand}
  players={gameState.players}
  roundNumber={gameState.currentRound}
  // ... other props
/>
```

### 2. Props Interface

#### Common Props (All Phases)
```typescript
{
  phase: 'PREPARATION' | 'DECLARATION' | 'TURN' | 'SCORING',
  myHand: Array<Piece>,
  players: Array<Player>,
  roundNumber: number
}
```

#### Phase-Specific Props

**Preparation Phase:**
```typescript
{
  weakHands: Array<string>,        // Players with weak hands
  redealMultiplier: number,        // Current redeal multiplier
  isMyHandWeak: boolean,          // If current player has weak hand
  isMyDecision: boolean,          // If waiting for player's decision
  onAcceptRedeal: Function,       // Handler for accepting redeal
  onDeclineRedeal: Function       // Handler for declining redeal
}
```

**Declaration Phase:**
```typescript
{
  declarations: Object,           // {playerName: value}
  currentTotal: number,          // Sum of declarations
  isMyTurnToDeclare: boolean,    // If it's player's turn
  validOptions: Array<number>,   // Valid declaration values
  isLastPlayer: boolean,         // If player is last to declare
  onDeclare: Function           // Handler for making declaration
}
```

**Turn Phase:**
```typescript
{
  currentTurnPlays: Array,       // Plays made this turn
  requiredPieceCount: number,    // Required pieces to play
  turnNumber: number,            // Current turn number
  isMyTurn: boolean,            // If it's player's turn
  canPlayAnyCount: boolean,      // If player can choose count
  currentPlayer: string,         // Current player's name
  onPlayPieces: Function        // Handler for playing pieces
}
```

### 3. Phase Content Implementation

#### Preparation Phase
```jsx
{phase === 'PREPARATION' && (
  <>
    {showDealing ? (
      <div className="dealing-container">
        {/* Dealing animation */}
      </div>
    ) : (
      <div className="weak-hand-section">
        {/* Weak hand alerts and decisions */}
      </div>
    )}
  </>
)}
```

#### Declaration Phase
```jsx
{phase === 'DECLARATION' && (
  <div className="game-status-section">
    <div className="declaration-requirement">
      Declare your target pile count
    </div>
    <div className="players-list">
      {/* Player rows with declaration status */}
    </div>
  </div>
)}

{/* Declaration popup - outside main container */}
{phase === 'DECLARATION' && isMyTurnToDeclare && (
  <div className="declaration-popup">
    {/* Declaration options grid */}
  </div>
)}
```

#### Turn Phase
The Turn phase uses a separate component for complex table layout:
```jsx
if (phase === 'TURN') {
  return <TableTurnUI {...turnProps} />;
}
```

### 4. State Management

Internal state includes:
- `showDealing`: Controls dealing animation
- `showWeakAlert`: Shows weak hand notification
- `selectedDeclaration`: Tracks selected declaration value
- `selectedPieces`: Array of selected piece indices
- `showConfirmPanel`: Shows piece play confirmation

### 5. Adding a New Phase

To add a new phase (e.g., SCORING):

1. **Update Phase Title/Subtitle:**
```jsx
const getPhaseTitle = () => {
  switch (phase) {
    case 'SCORING': return 'Scoring Phase';
    // ...
  }
};
```

2. **Add Phase Content:**
```jsx
{phase === 'SCORING' && (
  <div className="scoring-content">
    {/* Your scoring UI */}
  </div>
)}
```

3. **Add Phase-Specific Props:**
```jsx
// In PropTypes
scoringData: PropTypes.object,
onNextRound: PropTypes.func
```

4. **Handle Special Cases:**
For complex phases, consider creating a separate component like TableTurnUI.

### 6. CSS Structure

The component relies on custom CSS classes defined in `custom.css`:

- `.game-container`: Main container with fixed aspect ratio
- `.phase-header`: Common header for all phases
- `.content-section`: Dynamic content area
- `.hand-section`: Player's hand display
- Phase-specific classes for each phase's content

### 7. Best Practices

1. **Keep Common Elements Stable**: Don't modify structure of shared elements
2. **Use CSS Classes**: Avoid inline styles, use predefined CSS classes
3. **Handle Loading States**: Show appropriate loading/waiting UI
4. **Smooth Transitions**: Use CSS transitions for state changes
5. **Responsive Design**: Ensure content works within fixed container

### 8. Integration Example

```jsx
// In GameContainer.jsx
const unifiedGameProps = useMemo(() => {
  const phaseMap = {
    'preparation': 'PREPARATION',
    'declaration': 'DECLARATION',
    'turn': 'TURN'
  };
  
  return {
    phase: phaseMap[gameState.phase],
    myHand: gameState.myHand || [],
    players: gameState.players || [],
    roundNumber: gameState.currentRound || 1,
    // ... map all phase-specific props
  };
}, [gameState, gameActions]);

return <UnifiedGameUI {...unifiedGameProps} />;
```

### 9. Troubleshooting

**Common Issues:**
1. **Phase not updating**: Check prop mapping in container
2. **Missing styles**: Ensure custom.css is imported
3. **State not persisting**: Check if modifying shared elements
4. **Animations glitchy**: Verify CSS transition timing

**Debug Tips:**
- Add console.logs for phase changes
- Check React DevTools for prop values
- Verify CSS classes in browser inspector
- Test phase transitions manually

## Summary

UnifiedGameUI provides a consistent, maintainable approach to handling multiple game phases. By keeping common elements stable and only updating phase-specific content, it creates smooth transitions and a cohesive user experience. The component is designed to be extended with new phases while maintaining the existing structure.