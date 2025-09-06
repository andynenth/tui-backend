# Play History Implementation - TDD Checklist

## Overview
This document provides a Test-Driven Development (TDD) checklist for implementing the Play History feature with a focus on immutability and comprehensive error handling. The UI implementation targets the `1_round_timeline_v2.html` design.

## Core Principles
- ✅ Write tests BEFORE implementation
- ✅ Ensure all data structures are immutable
- ✅ Handle all error scenarios gracefully
- ✅ Validate all API responses
- ✅ Match the exact UI from mockup

---

## Phase 1: Data Types and Immutability Tests

### 1.1 TypeScript Interfaces
- [ ] **Test**: Define TypeScript interfaces for all data types
  ```typescript
  // __tests__/types/playHistory.test.ts
  describe('PlayHistory Type Definitions', () => {
    it('should enforce immutable types', () => {
      // Test that interfaces are readonly
      // Test that arrays are ReadonlyArray<T>
      // Test that objects have readonly properties
    });
  });
  ```

- [ ] **Test**: Validate API response shapes match interfaces
  ```typescript
  it('should validate API response against PlayHistory interface', () => {
    const response = mockApiResponse;
    expect(validatePlayHistory(response)).toBe(true);
  });
  ```

- [ ] **Implementation**: Create immutable type definitions
  ```typescript
  interface PlayHistory {
    readonly roomId: string;
    readonly rounds: ReadonlyArray<Round>;
    readonly players: ReadonlyArray<Player>;
    readonly gameStatus: Readonly<GameStatus>;
  }
  ```

### 1.2 Immutability Helpers
- [ ] **Test**: Create tests for immutability utilities
  ```typescript
  describe('Immutability Helpers', () => {
    it('should deep freeze objects', () => {
      const obj = deepFreeze({ a: { b: 1 } });
      expect(() => obj.a.b = 2).toThrow();
    });
    
    it('should create immutable updates', () => {
      const original = { score: 10 };
      const updated = updateImmutable(original, { score: 20 });
      expect(original.score).toBe(10);
      expect(updated.score).toBe(20);
      expect(original).not.toBe(updated);
    });
  });
  ```

---

## Phase 2: API Service Layer

### 2.1 API Client Tests
- [ ] **Test**: Base API client with error handling
  ```typescript
  describe('PlayHistoryAPI', () => {
    it('should handle successful responses', async () => {
      fetchMock.mockResponseOnce(JSON.stringify(mockData));
      const result = await playHistoryApi.getHistory('23BEBA');
      expect(result).toEqual(mockData);
    });
    
    it('should handle 404 errors', async () => {
      fetchMock.mockResponseOnce('', { status: 404 });
      await expect(playHistoryApi.getHistory('invalid')).rejects.toThrow('Game history not found');
    });
    
    it('should handle network errors', async () => {
      fetchMock.mockRejectOnce(new Error('Network error'));
      await expect(playHistoryApi.getHistory('23BEBA')).rejects.toThrow('Network error');
    });
    
    it('should handle malformed JSON', async () => {
      fetchMock.mockResponseOnce('invalid json');
      await expect(playHistoryApi.getHistory('23BEBA')).rejects.toThrow('Invalid response format');
    });
    
    it('should validate response data structure', async () => {
      fetchMock.mockResponseOnce(JSON.stringify({ invalid: 'data' }));
      await expect(playHistoryApi.getHistory('23BEBA')).rejects.toThrow('Invalid game history data');
    });
  });
  ```

### 2.2 Data Validation
- [ ] **Test**: Response validation functions
  ```typescript
  describe('Data Validation', () => {
    it('should validate player data', () => {
      expect(isValidPlayer({ name: 'Andy', type: 'human' })).toBe(true);
      expect(isValidPlayer({ name: '' })).toBe(false);
      expect(isValidPlayer(null)).toBe(false);
    });
    
    it('should validate round data', () => {
      expect(isValidRound(mockRound)).toBe(true);
      expect(isValidRound({ ...mockRound, turns: null })).toBe(false);
    });
    
    it('should validate piece data', () => {
      expect(isValidPiece({ type: 'GENERAL', point: 14, color: 'red' })).toBe(true);
      expect(isValidPiece({ type: 'INVALID', point: -1 })).toBe(false);
    });
  });
  ```

### 2.3 Error Handling
- [ ] **Test**: Comprehensive error scenarios
  ```typescript
  describe('Error Handling', () => {
    it('should handle timeout errors', async () => {
      jest.setTimeout(5000);
      const promise = playHistoryApi.getHistory('23BEBA', { timeout: 1 });
      await expect(promise).rejects.toThrow('Request timeout');
    });
    
    it('should retry on 503 errors', async () => {
      fetchMock
        .mockResponseOnce('', { status: 503 })
        .mockResponseOnce('', { status: 503 })
        .mockResponseOnce(JSON.stringify(mockData));
      
      const result = await playHistoryApi.getHistory('23BEBA', { retries: 3 });
      expect(result).toEqual(mockData);
      expect(fetchMock).toHaveBeenCalledTimes(3);
    });
    
    it('should handle corrupted game data gracefully', async () => {
      const corruptedData = { ...mockData, rounds: [{ invalid: true }] };
      fetchMock.mockResponseOnce(JSON.stringify(corruptedData));
      
      const result = await playHistoryApi.getHistory('23BEBA');
      expect(result.error).toBeDefined();
      expect(result.error.type).toBe('CORRUPTED_DATA');
    });
  });
  ```

---

## Phase 3: React Hooks

### 3.1 usePlayHistory Hook
- [ ] **Test**: Hook behavior and state management
  ```typescript
  describe('usePlayHistory', () => {
    it('should fetch data on mount', async () => {
      const { result } = renderHook(() => usePlayHistory('23BEBA'));
      
      expect(result.current.loading).toBe(true);
      expect(result.current.data).toBe(null);
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
        expect(result.current.data).toEqual(mockData);
      });
    });
    
    it('should handle loading states correctly', () => {
      const { result } = renderHook(() => usePlayHistory('23BEBA'));
      
      expect(result.current).toEqual({
        data: null,
        loading: true,
        error: null,
        retry: expect.any(Function)
      });
    });
    
    it('should handle errors', async () => {
      fetchMock.mockRejectOnce(new Error('API Error'));
      const { result } = renderHook(() => usePlayHistory('23BEBA'));
      
      await waitFor(() => {
        expect(result.current.error).toEqual({
          message: 'API Error',
          code: 'FETCH_ERROR',
          retry: true
        });
      });
    });
    
    it('should not mutate data', async () => {
      const { result } = renderHook(() => usePlayHistory('23BEBA'));
      
      await waitFor(() => {
        expect(result.current.data).toBeTruthy();
      });
      
      const originalData = result.current.data;
      expect(() => {
        originalData.rounds[0].winner = 'Modified';
      }).toThrow();
    });
  });
  ```

### 3.2 useRoundSelection Hook
- [ ] **Test**: Round selection state management
  ```typescript
  describe('useRoundSelection', () => {
    it('should initialize with round 1', () => {
      const { result } = renderHook(() => useRoundSelection(mockData));
      expect(result.current.selectedRound).toBe(1);
    });
    
    it('should update selected round immutably', () => {
      const { result } = renderHook(() => useRoundSelection(mockData));
      
      act(() => {
        result.current.selectRound(2);
      });
      
      expect(result.current.selectedRound).toBe(2);
      expect(result.current.roundData).toEqual(mockData.rounds[1]);
    });
    
    it('should handle invalid round numbers', () => {
      const { result } = renderHook(() => useRoundSelection(mockData));
      
      act(() => {
        result.current.selectRound(999);
      });
      
      expect(result.current.selectedRound).toBe(1);
      expect(result.current.error).toBe('Invalid round number');
    });
  });
  ```

---

## Phase 4: Component Tests (Matching 1_round_timeline_v2.html)

### 4.1 PlayHistoryPage Component
- [ ] **Test**: Main page component rendering
  ```typescript
  describe('PlayHistoryPage', () => {
    it('should render loading state', () => {
      const { getByText } = render(<PlayHistoryPage />);
      expect(getByText('Loading game history...')).toBeInTheDocument();
    });
    
    it('should render error state with retry button', async () => {
      fetchMock.mockRejectOnce(new Error('Network error'));
      const { getByText, getByRole } = render(<PlayHistoryPage />);
      
      await waitFor(() => {
        expect(getByText('Failed to load game history')).toBeInTheDocument();
        expect(getByRole('button', { name: 'Retry' })).toBeInTheDocument();
      });
    });
    
    it('should render game header with round selector', async () => {
      const { getByText, getByRole } = render(<PlayHistoryPage />);
      
      await waitFor(() => {
        expect(getByText('Room 23BEBA - Round 1')).toBeInTheDocument();
        expect(getByRole('combobox', { name: 'Round:' })).toBeInTheDocument();
      });
    });
  });
  ```

### 4.2 GameHeader Component
- [ ] **Test**: Header with round selection
  ```typescript
  describe('GameHeader', () => {
    it('should render room info and round selector', () => {
      const { getByText, getByRole } = render(<GameHeader data={mockData} />);
      
      expect(getByText('Room 23BEBA - Round 1')).toBeInTheDocument();
      expect(getByText('Total Turns: 6')).toBeInTheDocument();
      expect(getByText('Winner: Bot 2 (+6 points)')).toBeInTheDocument();
      
      const selector = getByRole('combobox');
      expect(selector).toHaveValue('1');
      expect(selector.options).toHaveLength(5);
    });
    
    it('should handle round selection', () => {
      const onRoundSelect = jest.fn();
      const { getByRole } = render(
        <GameHeader data={mockData} onRoundSelect={onRoundSelect} />
      );
      
      fireEvent.change(getByRole('combobox'), { target: { value: '3' } });
      expect(onRoundSelect).toHaveBeenCalledWith(3);
    });
  });
  ```

### 4.3 PlayerOverview Component
- [ ] **Test**: Player cards grid
  ```typescript
  describe('PlayerOverview', () => {
    it('should render all 4 players', () => {
      const { getAllByTestId } = render(<PlayerOverview players={mockPlayers} />);
      expect(getAllByTestId('player-card')).toHaveLength(4);
    });
    
    it('should highlight starter player', () => {
      const { getByText } = render(<PlayerOverview players={mockPlayers} />);
      const starterCard = getByText('Bot 3').closest('[data-testid="player-card"]');
      expect(starterCard).toHaveClass('starter');
      expect(getByText('STARTER')).toBeInTheDocument();
    });
    
    it('should display correct stats for each player', () => {
      const { getByTestId } = render(<PlayerOverview players={mockPlayers} />);
      const andyCard = getByTestId('player-andy');
      
      within(andyCard).getByText('3'); // Declared
      within(andyCard).getByText('0'); // Captured
      within(andyCard).getByText('-3'); // Score
    });
  });
  ```

### 4.4 HandBeforePlay Component
- [ ] **Test**: Hand display before play
  ```typescript
  describe('HandBeforePlay', () => {
    it('should show all pieces in hand', () => {
      const hand = [
        { type: 'ADVISOR', point: 12, color: 'red' },
        { type: 'HORSE', point: 6, color: 'red' }
      ];
      
      const { getByText } = render(<HandBeforePlay pieces={hand} />);
      expect(getByText('ADVISOR(12)')).toBeInTheDocument();
      expect(getByText('HORSE(6)')).toBeInTheDocument();
    });
    
    it('should apply correct color classes', () => {
      const { getByText } = render(<HandBeforePlay pieces={mockHand} />);
      expect(getByText('ADVISOR(12)').parentElement).toHaveClass('hand-before-piece red');
    });
  });
  ```

### 4.5 TurnSection Component
- [ ] **Test**: Turn display with all player plays
  ```typescript
  describe('TurnSection', () => {
    it('should render turn header with winner', () => {
      const { getByText } = render(<TurnSection turn={mockTurn} />);
      expect(getByText('Turn 1 - Triple Play Showdown')).toBeInTheDocument();
      expect(getByText('Bot 3 wins')).toBeInTheDocument();
      expect(getByText('3 pieces')).toBeInTheDocument();
    });
    
    it('should render all 4 player plays', () => {
      const { getAllByTestId } = render(<TurnSection turn={mockTurn} />);
      expect(getAllByTestId('play-card')).toHaveLength(4);
    });
    
    it('should highlight winner play card', () => {
      const { getByText } = render(<TurnSection turn={mockTurn} />);
      const winnerCard = getByText('Bot 3 (Starter)').closest('[data-testid="play-card"]');
      expect(winnerCard).toHaveClass('winner');
    });
    
    it('should show hand info without hand size', () => {
      const { getByText, queryByText } = render(<TurnSection turn={mockTurn} />);
      expect(getByText('Captured: 0→3')).toBeInTheDocument();
      expect(getByText('Declared: 6')).toBeInTheDocument();
      expect(queryByText(/Hand:/)).not.toBeInTheDocument();
    });
  });
  ```

---

## Phase 5: Error Boundary Tests

### 5.1 Component Error Handling
- [ ] **Test**: Error boundaries for each section
  ```typescript
  describe('PlayHistoryErrorBoundary', () => {
    it('should catch component errors and display fallback', () => {
      const ThrowError = () => {
        throw new Error('Component error');
      };
      
      const { getByText } = render(
        <PlayHistoryErrorBoundary>
          <ThrowError />
        </PlayHistoryErrorBoundary>
      );
      
      expect(getByText('Something went wrong')).toBeInTheDocument();
      expect(getByText('Unable to display game history')).toBeInTheDocument();
    });
    
    it('should log errors to console', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      const error = new Error('Test error');
      
      render(
        <PlayHistoryErrorBoundary>
          <ThrowError error={error} />
        </PlayHistoryErrorBoundary>
      );
      
      expect(consoleSpy).toHaveBeenCalledWith('PlayHistory Error:', error);
    });
  });
  ```

### 5.2 Data Corruption Handling
- [ ] **Test**: Graceful handling of corrupted data
  ```typescript
  describe('Data Corruption Handling', () => {
    it('should handle missing player data', () => {
      const corruptedData = { ...mockData, players: null };
      const { getByText } = render(<PlayHistoryPage data={corruptedData} />);
      expect(getByText('Invalid game data')).toBeInTheDocument();
    });
    
    it('should handle missing round data', () => {
      const corruptedData = { ...mockData, rounds: [] };
      const { getByText } = render(<PlayHistoryPage data={corruptedData} />);
      expect(getByText('No rounds found')).toBeInTheDocument();
    });
    
    it('should handle partial turn data', () => {
      const partialTurn = { ...mockTurn, plays: mockTurn.plays.slice(0, 2) };
      const { getAllByTestId } = render(<TurnSection turn={partialTurn} />);
      expect(getAllByTestId('play-card')).toHaveLength(2);
      expect(getAllByTestId('missing-player')).toHaveLength(2);
    });
  });
  ```

---

## Phase 6: Integration Tests

### 6.1 Full Page Flow
- [ ] **Test**: Complete user flow
  ```typescript
  describe('PlayHistory Integration', () => {
    it('should load and display game history', async () => {
      const { getByText, getByRole } = render(<PlayHistoryPage />);
      
      // Loading state
      expect(getByText('Loading game history...')).toBeInTheDocument();
      
      // Data loaded
      await waitFor(() => {
        expect(getByText('Room 23BEBA - Round 1')).toBeInTheDocument();
      });
      
      // Change round
      fireEvent.change(getByRole('combobox'), { target: { value: '2' } });
      
      await waitFor(() => {
        expect(getByText('Room 23BEBA - Round 2')).toBeInTheDocument();
      });
    });
    
    it('should handle error and retry', async () => {
      fetchMock.mockRejectOnce(new Error('Network error'));
      const { getByText, getByRole } = render(<PlayHistoryPage />);
      
      await waitFor(() => {
        expect(getByText('Failed to load game history')).toBeInTheDocument();
      });
      
      fetchMock.mockResponseOnce(JSON.stringify(mockData));
      fireEvent.click(getByRole('button', { name: 'Retry' }));
      
      await waitFor(() => {
        expect(getByText('Room 23BEBA - Round 1')).toBeInTheDocument();
      });
    });
  });
  ```

### 6.2 Performance Tests
- [ ] **Test**: Rendering performance
  ```typescript
  describe('Performance', () => {
    it('should render large game history efficiently', () => {
      const largeData = generateLargeGameHistory(20); // 20 rounds
      
      const startTime = performance.now();
      const { container } = render(<PlayHistoryPage data={largeData} />);
      const renderTime = performance.now() - startTime;
      
      expect(renderTime).toBeLessThan(1000); // Under 1 second
      expect(container.querySelectorAll('[data-testid="turn-section"]')).toHaveLength(6); // Only current round
    });
    
    it('should not re-render unnecessarily', () => {
      const renderSpy = jest.fn();
      const TrackedComponent = () => {
        renderSpy();
        return <PlayHistoryPage />;
      };
      
      const { rerender } = render(<TrackedComponent />);
      expect(renderSpy).toHaveBeenCalledTimes(1);
      
      rerender(<TrackedComponent />);
      expect(renderSpy).toHaveBeenCalledTimes(1); // No additional render
    });
  });
  ```

---

## Phase 7: Accessibility Tests

### 7.1 Keyboard Navigation
- [ ] **Test**: Keyboard accessibility
  ```typescript
  describe('Accessibility', () => {
    it('should be keyboard navigable', () => {
      const { getByRole } = render(<PlayHistoryPage />);
      
      const roundSelector = getByRole('combobox');
      roundSelector.focus();
      
      fireEvent.keyDown(roundSelector, { key: 'ArrowDown' });
      expect(roundSelector).toHaveValue('2');
    });
    
    it('should have proper ARIA labels', () => {
      const { getByLabelText } = render(<PlayHistoryPage />);
      expect(getByLabelText('Round selector')).toBeInTheDocument();
      expect(getByLabelText('Player overview')).toBeInTheDocument();
    });
  });
  ```

---

## Implementation Order

1. **Start with Types and Interfaces** (no mutations possible)
2. **Build API Service with Tests** (validate all data)
3. **Create Hooks with Tests** (ensure immutable state)
4. **Build Components Bottom-Up** (test each in isolation)
5. **Integration Tests** (verify complete flow)
6. **Performance & Accessibility** (ensure quality)

## Key Immutability Patterns

```typescript
// ✅ Good - Immutable update
const updateRound = (round: number) => {
  setGameState(prev => ({
    ...prev,
    selectedRound: round,
    roundData: prev.rounds[round - 1]
  }));
};

// ❌ Bad - Mutation
const updateRound = (round: number) => {
  gameState.selectedRound = round; // Mutation!
  setGameState(gameState);
};
```

## Error Handling Checklist

- [ ] Network errors (offline, timeout)
- [ ] HTTP errors (404, 500, etc.)
- [ ] Invalid JSON responses
- [ ] Missing required fields
- [ ] Type mismatches
- [ ] Corrupted data
- [ ] Empty data sets
- [ ] Out of bounds access
- [ ] Component render errors
- [ ] Async operation cancellation

## Success Criteria

- [ ] All tests pass before implementation
- [ ] Zero mutations in codebase
- [ ] 100% error scenario coverage
- [ ] UI matches mockup exactly
- [ ] Sub-1 second load time
- [ ] Graceful degradation
- [ ] No console errors in production