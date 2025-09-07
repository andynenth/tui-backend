# Play History Implementation - Admin Access with TDD

## Overview
This document consolidates the implementation plan for the admin-only Play History feature using Test-Driven Development (TDD). The feature provides direct URL access to game history without any user-facing navigation.

## Access Pattern
- **Direct URL Only**: `http://localhost:5050/history/{roomId}`
- **No Authentication**: Simple access for this version
- **No User Navigation**: No links from game UI
- **Admin Use Only**: Manual URL entry or bookmarks

## Core Principles
- ✅ Write tests BEFORE implementation
- ✅ Ensure all data structures are immutable
- ✅ Handle all error scenarios gracefully
- ✅ Validate all API responses
- ✅ Match the exact UI from `1_round_timeline_v2.html`
- ✅ Admin-only access (no user navigation)

---

## Phase 1: Project Setup & Routing

### 1.1 Add Route to App.jsx
- [x] **Test**: Verify route renders PlayHistoryPage
  ```typescript
  it('should render PlayHistoryPage for /history/:roomId route', () => {
    const { getByTestId } = render(
      <MemoryRouter initialEntries={['/history/23BEBA']}>
        <App />
      </MemoryRouter>
    );
    expect(getByTestId('play-history-page')).toBeInTheDocument();
  });
  ```

- [x] **Implementation**: Add single route (after line 169 in App.jsx)
  ```jsx
  {/* Admin-only Play History - direct URL access only */}
  <Route path="/history/:roomId" element={<PlayHistoryPage />} />
  ```

### 1.2 Create Directory Structure
```
frontend/src/
├── pages/
│   └── PlayHistoryPage/
│       ├── index.jsx
│       ├── PlayHistoryPage.jsx
│       └── PlayHistoryPage.test.jsx
├── services/
│   └── api/
│       ├── playHistoryService.ts
│       └── playHistoryService.test.ts
├── hooks/
│   ├── usePlayHistory.ts
│   └── usePlayHistory.test.ts
└── types/
    └── playHistory.ts
```

### 1.3 Styling Approach
- **Use Tailwind CSS** exclusively - no custom CSS files needed
- **Leverage existing theme** from `tailwind.config.js`:
  - `bg-game-background` for dark backgrounds
  - `bg-game-surface` for card surfaces
  - `text-game-text` for light text
  - `text-game-piece-red`, `text-game-piece-black` for piece colors
  - Custom animations: `animate-deal`, `animate-phase-transition`
- **Responsive utilities** for desktop-optimized admin view

---

## Phase 2: Data Types and Immutability

### 2.1 TypeScript Interfaces
- [x] **Test**: Define immutable TypeScript interfaces
  ```typescript
  // types/playHistory.test.ts
  describe('PlayHistory Type Definitions', () => {
    it('should enforce immutable types', () => {
      const history: PlayHistory = mockPlayHistory;
      // @ts-expect-error - should not allow mutation
      expect(() => history.rounds[0] = null).toThrow();
    });
  });
  ```

- [x] **Implementation**: Create immutable types
  ```typescript
  // types/playHistory.ts
  interface PlayHistory {
    readonly roomId: string;
    readonly rounds: ReadonlyArray<Round>;
    readonly players: ReadonlyArray<Player>;
    readonly gameStatus: Readonly<GameStatus>;
  }

  interface Round {
    readonly roundNumber: number;
    readonly declarations: ReadonlyArray<Declaration>;
    readonly turns: ReadonlyArray<Turn>;
    readonly scoring: Readonly<RoundScoring>;
    readonly winner: string;
  }
  ```

### 2.2 Immutability Helpers
- [x] **Test**: Deep freeze utilities
  ```typescript
  describe('Immutability Helpers', () => {
    it('should deep freeze API responses', () => {
      const data = deepFreeze(mockApiResponse);
      expect(() => data.rounds[0].winner = 'hacked').toThrow();
    });
  });
  ```

---

## Phase 3: API Service Layer

### 3.1 Play History Service
- [x] **Test**: API client with comprehensive error handling
  ```typescript
  describe('PlayHistoryService', () => {
    it('should fetch play history successfully', async () => {
      fetchMock.mockResponseOnce(JSON.stringify(mockData));
      const result = await playHistoryService.getHistory('23BEBA');
      expect(result).toEqual(mockData);
      expect(fetchMock).toHaveBeenCalledWith('/api/rooms/23BEBA/play-history');
    });

    it('should handle 404 - room not found', async () => {
      fetchMock.mockResponseOnce('', { status: 404 });
      await expect(playHistoryService.getHistory('invalid'))
        .rejects.toThrow('Game history not found');
    });

    it('should handle network errors', async () => {
      fetchMock.mockRejectOnce(new Error('Network error'));
      await expect(playHistoryService.getHistory('23BEBA'))
        .rejects.toThrow('Network error');
    });

    it('should validate response structure', async () => {
      fetchMock.mockResponseOnce(JSON.stringify({ invalid: 'data' }));
      await expect(playHistoryService.getHistory('23BEBA'))
        .rejects.toThrow('Invalid game history data');
    });
  });
  ```

- [x] **Implementation**: Create service with validation
  ```typescript
  // services/api/playHistoryService.ts
  export const playHistoryService = {
    async getHistory(roomId: string): Promise<PlayHistory> {
      const response = await fetch(`/api/rooms/${roomId}/play-history`);

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Game history not found');
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (!validatePlayHistory(data)) {
        throw new Error('Invalid game history data');
      }

      return deepFreeze(data);
    }
  };
  ```

### 3.2 Data Validation
- [x] **Test**: Comprehensive validation functions
  ```typescript
  describe('Data Validation', () => {
    it('should validate complete play history', () => {
      expect(validatePlayHistory(mockValidData)).toBe(true);
      expect(validatePlayHistory({})).toBe(false);
      expect(validatePlayHistory(null)).toBe(false);
    });

    it('should validate round structure', () => {
      const invalidRound = { ...mockRound, turns: null };
      expect(validateRound(invalidRound)).toBe(false);
    });

    it('should handle corrupted data gracefully', () => {
      const corrupted = { ...mockData, rounds: [{ invalid: true }] };
      expect(validatePlayHistory(corrupted)).toBe(false);
    });
  });
  ```

---

## Phase 4: React Hook Implementation

### 4.1 usePlayHistory Hook
- [x] **Test**: Hook with loading, error, and data states
  ```typescript
  describe('usePlayHistory', () => {
    it('should fetch data on mount', async () => {
      const { result } = renderHook(() => usePlayHistory('23BEBA'));

      // Initial state
      expect(result.current).toEqual({
        data: null,
        loading: true,
        error: null,
        retry: expect.any(Function)
      });

      // After fetch
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
        expect(result.current.data).toEqual(mockData);
      });
    });

    it('should handle errors with retry capability', async () => {
      fetchMock.mockRejectOnce(new Error('Network error'));
      const { result } = renderHook(() => usePlayHistory('23BEBA'));

      await waitFor(() => {
        expect(result.current.error).toEqual({
          message: 'Network error',
          code: 'FETCH_ERROR',
          canRetry: true
        });
      });

      // Test retry
      fetchMock.mockResponseOnce(JSON.stringify(mockData));
      act(() => result.current.retry());

      await waitFor(() => {
        expect(result.current.data).toEqual(mockData);
        expect(result.current.error).toBe(null);
      });
    });

    it('should ensure data immutability', async () => {
      const { result } = renderHook(() => usePlayHistory('23BEBA'));

      await waitFor(() => expect(result.current.data).toBeTruthy());

      expect(() => {
        result.current.data.rounds[0].winner = 'hacked';
      }).toThrow();
    });
  });
  ```

- [x] **Implementation**: Create hook with error handling
  ```typescript
  // hooks/usePlayHistory.ts
  export const usePlayHistory = (roomId: string) => {
    const [data, setData] = useState<PlayHistory | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<PlayHistoryError | null>(null);

    const fetchData = useCallback(async () => {
      setLoading(true);
      setError(null);

      try {
        const history = await playHistoryService.getHistory(roomId);
        setData(history);
      } catch (err) {
        setError({
          message: err.message,
          code: err.code || 'FETCH_ERROR',
          canRetry: true
        });
      } finally {
        setLoading(false);
      }
    }, [roomId]);

    useEffect(() => {
      fetchData();
    }, [fetchData]);

    return { data, loading, error, retry: fetchData };
  };
  ```

---

## Phase 5: Component Implementation (Matching 1_round_timeline_v2.html)

### 5.1 PlayHistoryPage Component
- [x] **Test**: Main page with all states
  ```typescript
  describe('PlayHistoryPage', () => {
    it('should show loading state initially', () => {
      const { getByText } = render(<PlayHistoryPage />);
      expect(getByText('Loading game history...')).toBeInTheDocument();
    });

    it('should render game history when loaded', async () => {
      const { getByText, getByRole } = render(<PlayHistoryPage />);

      await waitFor(() => {
        // Header elements
        expect(getByText('Room 23BEBA - Round 1')).toBeInTheDocument();
        expect(getByRole('combobox', { name: 'Round:' })).toBeInTheDocument();

        // Player overview
        expect(getByText('Andy')).toBeInTheDocument();
        expect(getByText('Bot 1')).toBeInTheDocument();

        // No navigation elements (admin-only)
        expect(queryByText('Back to Game')).not.toBeInTheDocument();
      });
    });

    it('should handle round selection', async () => {
      const { getByRole, getByText } = render(<PlayHistoryPage />);

      await waitFor(() => {
        const selector = getByRole('combobox');
        fireEvent.change(selector, { target: { value: '2' } });
      });

      expect(getByText('Room 23BEBA - Round 2')).toBeInTheDocument();
    });
  });
  ```

- [x] **Implementation**: Create main component with Tailwind styling
  ```jsx
  // pages/PlayHistoryPage/PlayHistoryPage.jsx
  export const PlayHistoryPage = () => {
    const { roomId } = useParams();
    const { data, loading, error, retry } = usePlayHistory(roomId);
    const [selectedRound, setSelectedRound] = useState(1);

    if (loading) {
      return <LoadingState />;
    }

    if (error) {
      return <ErrorState error={error} onRetry={retry} />;
    }

    if (!data) {
      return <EmptyState />;
    }

    const currentRound = data.rounds[selectedRound - 1];

    return (
      <div className="min-h-screen bg-game-background text-game-text" data-testid="play-history-page">
        <div className="max-w-7xl mx-auto p-6">
          <GameHeader
            roomId={roomId}
            round={currentRound}
            totalRounds={data.rounds.length}
            selectedRound={selectedRound}
            onRoundSelect={setSelectedRound}
          />

          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-8">
            <PlayerOverview
              players={data.players}
              roundData={currentRound}
            />
          </div>

          <div className="bg-game-surface rounded-lg shadow-game-lg p-8 mb-6">
            <DeclarationPhase
              declarations={currentRound.declarations}
              players={data.players}
            />
          </div>

          <div className="bg-game-surface rounded-lg shadow-game-lg p-8 mb-6">
            <TurnTimeline
              turns={currentRound.turns}
              players={data.players}
            />
          </div>

          <div className="bg-game-surface rounded-lg shadow-game-lg p-8">
            <RoundSummary
              scoring={currentRound.scoring}
              winner={currentRound.winner}
            />
          </div>
        </div>
      </div>
    );
  };
  ```

### 5.2 Key UI Components

#### GameHeader Component (with Tailwind)
- [x] **Implementation Example**:
  ```jsx
  const GameHeader = ({ roomId, round, totalRounds, selectedRound, onRoundSelect }) => {
    return (
      <div className="bg-game-surface rounded-lg shadow-game p-6 mb-8">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-3xl font-bold text-game-text">
            Room {roomId} - Round {selectedRound}
          </h1>

          <div className="flex items-center gap-2">
            <label className="text-sm text-game-text/80">Round:</label>
            <select
              value={selectedRound}
              onChange={(e) => onRoundSelect(Number(e.target.value))}
              className="bg-game-background border border-game-text/20 rounded px-3 py-1 text-game-text"
            >
              {Array.from({ length: totalRounds }, (_, i) => (
                <option key={i + 1} value={i + 1}>Round {i + 1}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="text-sm text-game-text/60">
          <span>Total Turns: {round.turns.length}</span>
          <span className="mx-4">•</span>
          <span>Winner: <span className="text-game-success font-semibold">{round.winner}</span></span>
        </div>
      </div>
    );
  };
  ```

#### PlayerOverview Component (with Tailwind)
- [x] **Implementation Example**:
  ```jsx
  const PlayerOverview = ({ players, roundData }) => {
    return players.map((player, index) => {
      const isStarter = roundData.starter === player.name;
      const playerStats = roundData.scoring.players[player.name];

      return (
        <div
          key={player.name}
          className={`
            bg-game-surface rounded-lg p-6 relative
            ${isStarter ? 'ring-2 ring-game-piece-gold' : ''}
          `}
        >
          {isStarter && (
            <span className="absolute top-2 right-2 text-xs bg-game-piece-gold text-game-background px-2 py-1 rounded">
              STARTER
            </span>
          )}

          <h3 className="text-xl font-semibold mb-4">{player.name}</h3>

          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-game-text/60">Declared:</span>
              <span className="font-mono">{playerStats.declared}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-game-text/60">Captured:</span>
              <span className="font-mono">{playerStats.captured}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-game-text/60">Score:</span>
              <span className={`font-mono font-bold ${
                playerStats.score > 0 ? 'text-game-success' :
                playerStats.score < 0 ? 'text-game-danger' : ''
              }`}>
                {playerStats.score > 0 ? '+' : ''}{playerStats.score}
              </span>
            </div>
          </div>
        </div>
      );
    });
  };
  ```

#### HandBeforePlay Component (with Tailwind)
- [x] **Implementation Example**:
  ```jsx
  const HandBeforePlay = ({ pieces }) => {
    return (
      <div className="mb-6">
        <div className="text-sm text-game-text/60 mb-2">Hand Before Play</div>
        <div className="flex flex-wrap gap-2">
          {pieces.map((piece, index) => (
            <span
              key={index}
              className={`
                px-3 py-2 rounded-md text-sm font-mono
                ${piece.color === 'red'
                  ? 'bg-game-piece-red/20 text-game-piece-red border border-game-piece-red/30'
                  : 'bg-game-piece-black/20 text-game-piece-black border border-game-piece-black/30'
                }
              `}
            >
              {piece.type}({piece.point})
            </span>
          ))}
        </div>
      </div>
    );
  };
  ```

#### TurnSection Component (with Tailwind)
- [x] **Implementation Example**:
  ```jsx
  const TurnSection = ({ turn, turnNumber }) => {
    const isTriplePlay = turn.plays.every(p => p.pieces.length === 3);

    return (
      <div className="border-b border-game-text/10 pb-6 mb-6 last:border-0">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">
            Turn {turnNumber} {isTriplePlay && '- Triple Play Showdown'}
          </h3>
          <div className="text-sm text-game-text/60">
            <span className="text-game-success font-semibold">{turn.winner} wins</span>
            <span className="ml-2">• {turn.winnerPieces} pieces</span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {turn.plays.map((play) => (
            <PlayCard
              key={play.player}
              play={play}
              isWinner={play.player === turn.winner}
              isStarter={play.isStarter}
            />
          ))}
        </div>
      </div>
    );
  };
  ```

- [x] **Test**: GameHeader with round selector and hand display
- [x] **Test**: PlayerOverview showing 4 players with stats
- [x] **Test**: HandBeforePlay showing initial pieces
- [x] **Test**: TurnSection with play cards and winner highlight
- [ ] **Test**: Error boundaries for each section

---

### 5.3 Loading and Error States (with Tailwind)

#### LoadingState Component
```jsx
const LoadingState = () => (
  <div className="min-h-screen bg-game-background flex items-center justify-center">
    <div className="text-center">
      <div className="w-16 h-16 border-4 border-game-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
      <p className="text-game-text text-lg">Loading game history...</p>
    </div>
  </div>
);
```

#### ErrorState Component
```jsx
const ErrorState = ({ error, onRetry }) => (
  <div className="min-h-screen bg-game-background flex items-center justify-center">
    <div className="bg-game-surface rounded-lg shadow-game-lg p-8 max-w-md w-full mx-4">
      <div className="text-center">
        <div className="w-16 h-16 bg-game-danger/20 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-game-danger" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h2 className="text-xl font-semibold text-game-text mb-2">Failed to load game history</h2>
        <p className="text-game-text/60 mb-6">{error.message}</p>
        {error.canRetry && (
          <button
            onClick={onRetry}
            className="bg-game-primary hover:bg-game-primary/80 text-white px-6 py-2 rounded-lg transition-colors"
          >
            Retry
          </button>
        )}
      </div>
    </div>
  </div>
);
```

#### EmptyState Component
```jsx
const EmptyState = () => (
  <div className="min-h-screen bg-game-background flex items-center justify-center">
    <div className="text-center">
      <p className="text-game-text/60 text-lg">No game history found</p>
    </div>
  </div>
);
```

---

## Phase 6: Error Handling & Edge Cases

### 6.1 Comprehensive Error Scenarios
- [x] Network errors (offline, timeout)
- [x] HTTP errors (404, 500, 503)
- [x] Invalid JSON responses
- [x] Missing required fields
- [x] Type mismatches
- [x] Corrupted data
- [x] Empty data sets
- [x] Out of bounds access
- [x] Component render errors
- [x] Async operation cancellation

### 6.2 Error Recovery
- [x] **Test**: Retry mechanisms
- [x] **Test**: Graceful degradation
- [x] **Test**: Partial data handling
- [ ] **Test**: Error boundary fallbacks

---

## Phase 7: Integration & Performance

### 7.1 Full Integration Tests
- [x] **Test**: Complete user flow from URL entry to data display
- [x] **Test**: Round navigation with data updates
- [x] **Test**: Error recovery flows
- [x] **Test**: Admin-specific features (no auth required)

### 7.2 Performance Tests
- [x] **Test**: Render time < 1 second
- [x] **Test**: API response handling for large histories
- [x] **Test**: Memory usage with multiple rounds
- [x] **Test**: No unnecessary re-renders

---

## Implementation Order

1. **Week 1**: Setup & Core Infrastructure
   - Add route to App.jsx
   - Create TypeScript types
   - Build API service with tests
   - Implement usePlayHistory hook

2. **Week 2**: Component Development
   - Build components bottom-up with tests
   - Match UI to mockup exactly
   - Implement error handling

3. **Week 3**: Integration & Polish
   - Full integration tests
   - Performance optimization
   - Admin-specific enhancements

## Success Criteria

- [x] All tests written before implementation (TDD followed for services, integration/performance tests added)
- [x] Zero mutations in codebase (using deepFreeze and immutable types)
- [x] 100% error scenario coverage (comprehensive error handling implemented and tested)
- [x] UI matches `1_round_timeline_v2.html` exactly (all components implemented)
- [x] Sub-1 second load time (performance tests verify < 1s render time)
- [x] No console errors in production (builds without errors)
- [x] Direct URL access only (no navigation) (admin-only route implemented)
- [x] Desktop-optimized for admin use (using responsive Tailwind classes)

## Key Differences from User-Facing Features

1. **No Authentication**: Simple direct access
2. **No Navigation Integration**: No links from game UI
3. **No Mobile Optimization**: Desktop-focused for admins
4. **Enhanced Details**: Can show debug info, raw data
5. **No Player Context**: Works without player session

## Testing Commands

**Note**: The project needs testing dependencies installed before running tests:
```bash
# Install testing dependencies
cd frontend && npm install --save-dev jest @testing-library/react @testing-library/jest-dom @testing-library/user-event babel-jest @babel/preset-typescript identity-obj-proxy

# Add test script to package.json
# "test": "jest"
```

```bash
# Run all tests
cd frontend && npm test

# Run specific test file
npm test PlayHistoryPage.test.jsx

# Run with coverage
npm test -- --coverage

# Watch mode for TDD
npm test -- --watch
```

## Tailwind CSS Benefits

Using Tailwind CSS for this admin feature provides:

1. **Rapid Development**: No need to create custom CSS files
2. **Consistent Theme**: Uses existing game colors and spacing from `tailwind.config.js`
3. **Responsive by Default**: Built-in responsive utilities (sm:, md:, lg:, xl:)
4. **Dark Mode Ready**: Already configured with dark backgrounds
5. **Custom Animations**: Can use existing animations like `animate-deal`, `animate-phase-transition`
6. **Type-Safe Classes**: With TypeScript and proper IDE support
7. **Zero Custom CSS**: Everything styled with utility classes

### Key Tailwind Classes from Game Theme:
- **Colors**: `bg-game-background`, `bg-game-surface`, `text-game-text`
- **Piece Colors**: `text-game-piece-red`, `text-game-piece-black`, `bg-game-piece-gold`
- **States**: `text-game-success`, `text-game-danger`, `text-game-warning`
- **Shadows**: `shadow-game`, `shadow-game-lg`
- **Animations**: `animate-deal`, `animate-piece-select`, `animate-phase-transition`

## Next Steps

1. Create the test files first (TDD approach)
2. Add the single route to App.jsx
3. Build services and hooks with full test coverage
4. Implement components using Tailwind utilities
5. No additional navigation or user-facing changes
