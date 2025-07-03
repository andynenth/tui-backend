# UnifiedGameStore Usage Guide

## Overview
The UnifiedGameStore is a clean, focused state management solution that replaces the 1534-line GameService. It provides:
- Single source of truth for game state
- Automatic versioning and checksums
- Immediate state updates
- React integration via hooks
- Network service integration

## Basic Usage

### In React Components

```typescript
import { useGameStore } from '../hooks/useGameStore';

function GameComponent() {
  const gameState = useGameStore();
  
  return (
    <div>
      <p>Current Phase: {gameState.phase}</p>
      <p>Round: {gameState.currentRound}</p>
      <p>Version: {gameState.version}</p>
    </div>
  );
}
```

### Using Selectors

```typescript
import { useGameStoreSelector } from '../hooks/useGameStore';

function PlayerList() {
  const players = useGameStoreSelector(state => state.players);
  
  return (
    <ul>
      {players.map(player => (
        <li key={player.name}>
          {player.name}: {player.score} points
        </li>
      ))}
    </ul>
  );
}
```

### Direct Store Access

```typescript
import { gameStore } from '../stores';

// Get current state
const state = gameStore.getState();

// Update state
gameStore.updateState({
  phase: 'declaration',
  currentRound: 2
});

// Subscribe to changes
const unsubscribe = gameStore.subscribe((state) => {
  console.log('State updated:', state);
});

// Cleanup
unsubscribe();
```

## Network Integration

The store automatically syncs with backend through NetworkIntegration:

```typescript
import { networkIntegration } from '../stores';

// Initialize on app start
networkIntegration.initialize();

// Cleanup on app unmount
networkIntegration.destroy();
```

## State Validation

```typescript
// Check if state is consistent
const isValid = gameStore.validateState();

// Get current version for sync checking
const version = gameStore.getVersion();
```

## Architecture Benefits

1. **~100 lines vs 1534 lines** - 93% code reduction
2. **Immutable updates** - Prevents accidental mutations
3. **Automatic versioning** - Track state changes
4. **Built-in validation** - Checksum verification
5. **TypeScript safety** - Full type coverage
6. **React optimized** - Efficient re-renders
7. **Single responsibility** - Just state management