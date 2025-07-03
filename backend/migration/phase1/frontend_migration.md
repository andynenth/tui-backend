# Frontend Migration Guide: GameService → UnifiedGameStore

This guide provides step-by-step instructions to migrate from the old GameService to the new UnifiedGameStore.

## Overview

The migration replaces the fragmented state management (GameService, NetworkService) with a unified store that:
- Maintains a single source of truth for game state
- Handles version tracking and checksums
- Provides automatic state synchronization
- Offers cleaner React integration via hooks

## Files to Update

### 1. Core Service Files to Replace

**DELETE these files after migration:**
- `frontend/src/services/GameService.ts`
- `frontend/src/services/NetworkService.ts` (keep network layer, remove state management)
- `frontend/src/services/index.ts` (if only re-exporting the above)

### 2. Component Files to Update

The following files import and use GameService/NetworkService:

```bash
# Find all files using GameService
grep -r "GameService" frontend/src --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx"

# Find all files using NetworkService
grep -r "NetworkService" frontend/src --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx"
```

Typical files that need updates:
- `frontend/src/App.tsx`
- `frontend/src/components/GameBoard.tsx`
- `frontend/src/components/PlayerHand.tsx`
- `frontend/src/phases/*.tsx` (all phase components)
- `frontend/src/pages/GamePage.tsx`

## Migration Steps

### Step 1: Install UnifiedGameStore

Ensure the UnifiedGameStore is in place:
```bash
# The file should already exist at:
# frontend/src/stores/UnifiedGameStore.ts
```

### Step 2: Create Hook for React Integration

Create `frontend/src/hooks/useGameStore.ts`:

```typescript
import { useEffect, useState, useCallback } from 'react';
import { UnifiedGameStore } from '../stores/UnifiedGameStore';
import type { GameState, GameAction } from '../types/game';

export function useGameStore() {
  const store = UnifiedGameStore.getInstance();
  const [state, setState] = useState<GameState>(store.getState());
  const [isConnected, setIsConnected] = useState(store.isConnected());

  useEffect(() => {
    // Subscribe to state changes
    const unsubscribeState = store.subscribe((newState) => {
      setState(newState);
    });

    // Subscribe to connection changes
    const handleConnectionChange = (connected: boolean) => {
      setIsConnected(connected);
    };
    
    // Listen for connection events
    store.on('connected', () => handleConnectionChange(true));
    store.on('disconnected', () => handleConnectionChange(false));

    return () => {
      unsubscribeState();
    };
  }, []);

  const dispatch = useCallback((action: GameAction) => {
    return store.dispatch(action);
  }, []);

  return {
    state,
    isConnected,
    dispatch,
    // Convenience methods
    currentPlayer: state.players[state.currentPlayerIndex],
    isMyTurn: state.players[state.currentPlayerIndex]?.id === store.getPlayerId(),
  };
}
```

### Step 3: Update App.tsx

**Before:**
```typescript
import { GameService } from './services/GameService';
import { NetworkService } from './services/NetworkService';

function App() {
  const [gameState, setGameState] = useState(null);
  
  useEffect(() => {
    const gameService = GameService.getInstance();
    const networkService = NetworkService.getInstance();
    
    gameService.on('stateChange', setGameState);
    networkService.connect();
    
    return () => {
      gameService.off('stateChange', setGameState);
    };
  }, []);
  
  // ...
}
```

**After:**
```typescript
import { useGameStore } from './hooks/useGameStore';
import { UnifiedGameStore } from './stores/UnifiedGameStore';

function App() {
  const { state, isConnected } = useGameStore();
  
  useEffect(() => {
    const store = UnifiedGameStore.getInstance();
    store.connect(); // Connect on app mount
    
    return () => {
      store.disconnect(); // Cleanup on unmount
    };
  }, []);
  
  if (!isConnected) {
    return <div>Connecting...</div>;
  }
  
  // Use state directly
  // ...
}
```

### Step 4: Update Component Files

**Before (in any component):**
```typescript
import { GameService } from '../services/GameService';

function GameBoard() {
  const gameService = GameService.getInstance();
  const [pieces, setPieces] = useState(gameService.getBoardPieces());
  
  const handlePieceClick = (piece) => {
    gameService.playPiece(piece);
  };
  
  useEffect(() => {
    const updatePieces = () => setPieces(gameService.getBoardPieces());
    gameService.on('boardUpdate', updatePieces);
    return () => gameService.off('boardUpdate', updatePieces);
  }, []);
  
  // ...
}
```

**After:**
```typescript
import { useGameStore } from '../hooks/useGameStore';

function GameBoard() {
  const { state, dispatch } = useGameStore();
  const pieces = state.board.pieces;
  
  const handlePieceClick = (piece) => {
    dispatch({
      type: 'PLAY_PIECE',
      payload: { piece }
    });
  };
  
  // No need for manual subscriptions - hook handles it
  // ...
}
```

### Step 5: Update Phase Components

**Before (example from TurnPhase):**
```typescript
import { GameService } from '../../services/GameService';
import { NetworkService } from '../../services/NetworkService';

export function TurnPhase() {
  const gameService = GameService.getInstance();
  const networkService = NetworkService.getInstance();
  const [currentPlayer, setCurrentPlayer] = useState(gameService.getCurrentPlayer());
  
  const playPieces = (pieces: Piece[]) => {
    networkService.send('play', { pieces });
  };
  
  // ...
}
```

**After:**
```typescript
import { useGameStore } from '../../hooks/useGameStore';

export function TurnPhase() {
  const { state, dispatch, currentPlayer, isMyTurn } = useGameStore();
  
  const playPieces = (pieces: Piece[]) => {
    dispatch({
      type: 'PLAY_PIECES',
      payload: { pieces }
    });
  };
  
  // ...
}
```

### Step 6: Update Network Layer

Update `frontend/src/network/websocket.ts` to work with UnifiedGameStore:

```typescript
import { UnifiedGameStore } from '../stores/UnifiedGameStore';

class WebSocketClient {
  private store = UnifiedGameStore.getInstance();
  
  constructor() {
    this.setupMessageHandlers();
  }
  
  private setupMessageHandlers() {
    this.on('phase_change', (data) => {
      // Let the store handle state updates
      this.store.handleServerUpdate(data);
    });
    
    this.on('game_event', (data) => {
      this.store.handleServerUpdate(data);
    });
  }
  
  // Remove any state management logic - just handle connection
}
```

## Search and Replace Patterns

Use these regex patterns to help with migration:

### 1. Import Statements
```bash
# Find GameService imports
sed -i '' 's/import.*GameService.*from.*[\"'\''']\.\.\/services\/GameService[\"'\'''];?/import { useGameStore } from '\''..\/hooks\/useGameStore'\'';/g' frontend/src/**/*.{ts,tsx}

# Find NetworkService imports (be careful - might need network functionality)
grep -r "import.*NetworkService" frontend/src
```

### 2. Instance Creation
```javascript
// Find: GameService.getInstance()
// Replace with: (remove - use hook instead)

// Find: const gameService = GameService.getInstance();
// Replace with: const { state, dispatch } = useGameStore();
```

### 3. Method Calls
```javascript
// Find: gameService.getCurrentPlayer()
// Replace with: currentPlayer (from hook)

// Find: gameService.getState()
// Replace with: state

// Find: gameService.playPiece(piece)
// Replace with: dispatch({ type: 'PLAY_PIECE', payload: { piece } })

// Find: networkService.send(action, data)
// Replace with: dispatch({ type: action.toUpperCase(), payload: data })
```

## Validation Checklist

After migration, verify:

- [ ] All imports updated to use UnifiedGameStore or useGameStore hook
- [ ] No remaining references to GameService or NetworkService (except network layer)
- [ ] Components re-render on state changes
- [ ] Actions dispatch correctly to the server
- [ ] State synchronization works (version increments, checksums match)
- [ ] No console errors about missing services
- [ ] Hot reload still works in development
- [ ] Build completes without errors: `npm run build`

## Rollback Plan

If issues arise:

1. Restore backed up files from `migration/phase1/backups/[timestamp]/`
2. Restart the development server
3. Document what went wrong for troubleshooting

## Common Issues and Solutions

### Issue: "Cannot read property 'getInstance' of undefined"
**Solution:** You missed updating an import. Search for GameService/NetworkService imports.

### Issue: Components not re-rendering
**Solution:** Ensure you're using the useGameStore hook, not direct store access.

### Issue: Actions not reaching server
**Solution:** Check that dispatch is being called with correct action format.

### Issue: TypeScript errors about missing types
**Solution:** Update type imports to use the new store's type definitions.

## Next Steps

After completing frontend migration:
1. Run validation tests: `python migration/phase1/validation_tests.py`
2. Proceed with backend migration: See `backend_migration.md`
3. Test full game flow end-to-end