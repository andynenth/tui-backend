/**
 * Unit Tests for Redeal Decision Bug Fix
 * 
 * Bug ID: REDEAL-001
 * Testing: GameService.handleWeakHandsFound method
 */

import { GameService } from '../GameService';

describe('GameService - Redeal Decision Bug Tests', () => {
  let gameService;

  beforeEach(() => {
    // Create fresh instance for each test
    gameService = new GameService();
  });

  afterEach(() => {
    // Clean up
    if (gameService && gameService.cleanup) {
      gameService.cleanup();
    }
  });

  describe('handleWeakHandsFound - Core Bug Fix', () => {
    const mockWeakHand = [
      { kind: 'SOLDIER', color: 'red', value: 2 },
      { kind: 'SOLDIER', color: 'black', value: 1 },
      { kind: 'ADVISOR', color: 'red', value: 8 },
      { kind: 'HORSE', color: 'black', value: 5 },
      { kind: 'CANNON', color: 'red', value: 7 },
      { kind: 'CHARIOT', color: 'black', value: 9 },
      { kind: 'ELEPHANT', color: 'red', value: 6 },
      { kind: 'GENERAL', color: 'black', value: 3 },
    ];

    const mockStrongHand = [
      { kind: 'GENERAL', color: 'red', value: 14 },
      { kind: 'ADVISOR', color: 'black', value: 11 },
      { kind: 'ELEPHANT', color: 'red', value: 10 },
      { kind: 'HORSE', color: 'black', value: 5 },
      { kind: 'CHARIOT', color: 'red', value: 13 },
      { kind: 'CANNON', color: 'black', value: 12 },
      { kind: 'SOLDIER', color: 'red', value: 2 },
      { kind: 'SOLDIER', color: 'black', value: 1 },
    ];

    test('REDEAL-001-T001: Should calculate isMyHandWeak correctly for weak hand', () => {
      // Arrange
      const initialState = {
        phase: 'preparation',
        playerName: 'TestPlayer',
        myHand: mockWeakHand,
        isMyHandWeak: false, // ❌ Bug: Should be recalculated
        isMyDecision: false,
        simultaneousMode: false,
      };

      const weakHandsFoundData = {
        weak_hands: ['TestPlayer', 'Bot2'],
        current_weak_player: 'TestPlayer',
      };

      // Act
      const result = gameService.handleWeakHandsFound(initialState, weakHandsFoundData);

      // Assert
      expect(result.isMyHandWeak).toBe(true); // ✅ Should be true for weak hand
      expect(result.weakHands).toEqual(['TestPlayer', 'Bot2']);
      expect(result.currentWeakPlayer).toBe('TestPlayer');
    });

    test('REDEAL-001-T002: Should calculate isMyHandWeak correctly for strong hand', () => {
      // Arrange
      const initialState = {
        phase: 'preparation',
        playerName: 'TestPlayer',
        myHand: mockStrongHand,
        isMyHandWeak: true, // Stale value
        isMyDecision: false,
        simultaneousMode: false,
      };

      const weakHandsFoundData = {
        weak_hands: ['Bot2'], // TestPlayer not in weak hands
        current_weak_player: 'Bot2',
      };

      // Act
      const result = gameService.handleWeakHandsFound(initialState, weakHandsFoundData);

      // Assert
      expect(result.isMyHandWeak).toBe(false); // ✅ Should be false for strong hand
      expect(result.weakHands).toEqual(['Bot2']);
      expect(result.currentWeakPlayer).toBe('Bot2');
    });

    test('REDEAL-001-T003: Should calculate isMyDecision correctly in sequential mode', () => {
      // Arrange
      const initialState = {
        phase: 'preparation',
        playerName: 'TestPlayer',
        myHand: mockWeakHand,
        isMyHandWeak: false,
        isMyDecision: false, // ❌ Bug: Should be recalculated
        simultaneousMode: false,
      };

      const weakHandsFoundData = {
        weak_hands: ['TestPlayer', 'Bot2'],
        current_weak_player: 'TestPlayer', // It's TestPlayer's turn
      };

      // Act
      const result = gameService.handleWeakHandsFound(initialState, weakHandsFoundData);

      // Assert
      expect(result.isMyDecision).toBe(true); // ✅ Should be true - it's my turn
      expect(result.currentWeakPlayer).toBe('TestPlayer');
    });

    test('REDEAL-001-T004: Should calculate isMyDecision correctly in simultaneous mode', () => {
      // Arrange
      const initialState = {
        phase: 'preparation',
        playerName: 'TestPlayer',
        myHand: mockWeakHand,
        isMyHandWeak: false,
        isMyDecision: false, // ❌ Bug: Should be recalculated
        simultaneousMode: true,
        weakPlayersAwaiting: ['TestPlayer', 'Bot3'],
      };

      const weakHandsFoundData = {
        weak_hands: ['TestPlayer', 'Bot2', 'Bot3'],
        current_weak_player: null, // No single current player in simultaneous mode
      };

      // Act
      const result = gameService.handleWeakHandsFound(initialState, weakHandsFoundData);

      // Assert
      expect(result.isMyDecision).toBe(true); // ✅ Should be true - I'm awaiting decision
      expect(result.simultaneousMode).toBe(true);
    });

    test('REDEAL-001-T005: Should calculate handValue and highestCardValue', () => {
      // Arrange
      const initialState = {
        phase: 'preparation',
        playerName: 'TestPlayer',
        myHand: mockWeakHand,
        handValue: 0, // Stale value
        highestCardValue: 0, // Stale value
      };

      const weakHandsFoundData = {
        weak_hands: ['TestPlayer'],
        current_weak_player: 'TestPlayer',
      };

      // Act
      const result = gameService.handleWeakHandsFound(initialState, weakHandsFoundData);

      // Assert
      expect(result.handValue).toBeGreaterThan(0); // Should calculate total value
      expect(result.highestCardValue).toBe(9); // Highest card in mockWeakHand
    });
  });

  describe('Edge Cases and Error Handling', () => {
    test('REDEAL-001-T006: Should handle empty myHand gracefully', () => {
      // Arrange
      const initialState = {
        phase: 'preparation',
        playerName: 'TestPlayer',
        myHand: [], // Empty hand
        isMyHandWeak: false,
        isMyDecision: false,
      };

      const weakHandsFoundData = {
        weak_hands: ['TestPlayer'],
        current_weak_player: 'TestPlayer',
      };

      // Act
      const result = gameService.handleWeakHandsFound(initialState, weakHandsFoundData);

      // Assert - Should not crash, should not update hand-related values
      expect(result.isMyHandWeak).toBe(false); // Should remain unchanged
      expect(result.handValue).toBeUndefined(); // Should not be set
      expect(result.highestCardValue).toBeUndefined(); // Should not be set
    });

    test('REDEAL-001-T007: Should handle missing playerName gracefully', () => {
      // Arrange
      const initialState = {
        phase: 'preparation',
        playerName: null, // Missing player name
        myHand: [{ kind: 'SOLDIER', color: 'red', value: 2 }],
        isMyHandWeak: false,
        isMyDecision: false,
      };

      const weakHandsFoundData = {
        weak_hands: ['TestPlayer'],
        current_weak_player: 'TestPlayer',
      };

      // Act
      const result = gameService.handleWeakHandsFound(initialState, weakHandsFoundData);

      // Assert - Should not crash, isMyDecision should remain false
      expect(result.isMyDecision).toBe(false);
      expect(result.playerName).toBe(null);
    });

    test('REDEAL-001-T008: Should handle malformed event data', () => {
      // Arrange
      const initialState = {
        phase: 'preparation',
        playerName: 'TestPlayer',
        myHand: [{ kind: 'SOLDIER', color: 'red', value: 2 }],
      };

      const malformedData = null; // Malformed event data

      // Act
      const result = gameService.handleWeakHandsFound(initialState, malformedData);

      // Assert - Should handle gracefully with defaults
      expect(result.weakHands).toEqual([]);
      expect(result.currentWeakPlayer).toBe(null);
    });
  });

  describe('Integration with UI State Flags', () => {
    test('REDEAL-001-T009: Should enable redeal UI for weak hand player in sequential mode', () => {
      // Arrange - Scenario where redeal UI should appear
      const initialState = {
        phase: 'preparation',
        playerName: 'TestPlayer',
        myHand: [
          { kind: 'SOLDIER', color: 'red', value: 2 },
          { kind: 'SOLDIER', color: 'black', value: 1 },
          { kind: 'ADVISOR', color: 'red', value: 8 },
          { kind: 'HORSE', color: 'black', value: 5 },
        ],
        isMyHandWeak: false, // Will be updated
        isMyDecision: false, // Will be updated
        simultaneousMode: false,
      };

      const weakHandsFoundData = {
        weak_hands: ['TestPlayer'],
        current_weak_player: 'TestPlayer',
      };

      // Act
      const result = gameService.handleWeakHandsFound(initialState, weakHandsFoundData);

      // Assert - Both flags should be true for UI to appear
      expect(result.isMyHandWeak).toBe(true); // Has weak hand
      expect(result.isMyDecision).toBe(true); // Is current player's turn
      
      // UI should appear when: isMyHandWeak && isMyDecision
      const shouldShowRedealUI = result.isMyHandWeak && result.isMyDecision;
      expect(shouldShowRedealUI).toBe(true);
    });

    test('REDEAL-001-T010: Should disable redeal UI for strong hand player', () => {
      // Arrange - Scenario where redeal UI should NOT appear
      const initialState = {
        phase: 'preparation',
        playerName: 'TestPlayer',
        myHand: [
          { kind: 'GENERAL', color: 'red', value: 14 }, // Strong hand
          { kind: 'ADVISOR', color: 'black', value: 11 },
          { kind: 'ELEPHANT', color: 'red', value: 10 },
          { kind: 'CHARIOT', color: 'black', value: 13 },
        ],
        isMyHandWeak: true, // Stale - will be updated
        isMyDecision: false,
        simultaneousMode: false,
      };

      const weakHandsFoundData = {
        weak_hands: ['Bot2'], // TestPlayer not in weak hands
        current_weak_player: 'Bot2',
      };

      // Act
      const result = gameService.handleWeakHandsFound(initialState, weakHandsFoundData);

      // Assert - UI should not appear for strong hand
      expect(result.isMyHandWeak).toBe(false); // Strong hand
      expect(result.isMyDecision).toBe(false); // Not my turn
      
      const shouldShowRedealUI = result.isMyHandWeak && result.isMyDecision;
      expect(shouldShowRedealUI).toBe(false);
    });
  });

  describe('Regression Tests', () => {
    test('REDEAL-001-T011: Should maintain existing functionality', () => {
      // Arrange - Test that existing functionality is preserved
      const initialState = {
        phase: 'preparation',
        playerName: 'TestPlayer',
        myHand: [],
        someOtherProperty: 'should be preserved',
        anotherProperty: 42,
      };

      const weakHandsFoundData = {
        weak_hands: ['Bot1'],
        current_weak_player: 'Bot1',
      };

      // Act
      const result = gameService.handleWeakHandsFound(initialState, weakHandsFoundData);

      // Assert - Existing properties should be preserved
      expect(result.someOtherProperty).toBe('should be preserved');
      expect(result.anotherProperty).toBe(42);
      expect(result.phase).toBe('preparation');
      expect(result.playerName).toBe('TestPlayer');
    });

    test('REDEAL-001-T012: Should not affect non-preparation phases', () => {
      // Arrange - Test behavior in other phases
      const initialState = {
        phase: 'turn', // Different phase
        playerName: 'TestPlayer',
        myHand: [{ kind: 'SOLDIER', color: 'red', value: 2 }],
        isMyHandWeak: false,
        isMyDecision: false,
      };

      const weakHandsFoundData = {
        weak_hands: ['TestPlayer'],
        current_weak_player: 'TestPlayer',
      };

      // Act
      const result = gameService.handleWeakHandsFound(initialState, weakHandsFoundData);

      // Assert - Should still update UI flags even in other phases (they might be used)
      expect(result.weakHands).toEqual(['TestPlayer']);
      expect(result.currentWeakPlayer).toBe('TestPlayer');
      // The UI flags should still be calculated as they might be relevant
    });
  });
});

// Test Utilities
export const RedealTestUtils = {
  createMockWeakHand: () => [
    { kind: 'SOLDIER', color: 'red', value: 2 },
    { kind: 'SOLDIER', color: 'black', value: 1 },
    { kind: 'ADVISOR', color: 'red', value: 8 },
    { kind: 'HORSE', color: 'black', value: 5 },
    { kind: 'CANNON', color: 'red', value: 7 },
    { kind: 'CHARIOT', color: 'black', value: 9 },
    { kind: 'ELEPHANT', color: 'red', value: 6 },
    { kind: 'GENERAL', color: 'black', value: 3 },
  ],

  createMockStrongHand: () => [
    { kind: 'GENERAL', color: 'red', value: 14 },
    { kind: 'ADVISOR', color: 'black', value: 11 },
    { kind: 'ELEPHANT', color: 'red', value: 10 },
    { kind: 'HORSE', color: 'black', value: 5 },
    { kind: 'CHARIOT', color: 'red', value: 13 },
    { kind: 'CANNON', color: 'black', value: 12 },
    { kind: 'SOLDIER', color: 'red', value: 2 },
    { kind: 'SOLDIER', color: 'black', value: 1 },
  ],

  createMockGameState: (overrides = {}) => ({
    phase: 'preparation',
    playerName: 'TestPlayer',
    myHand: [],
    isMyHandWeak: false,
    isMyDecision: false,
    simultaneousMode: false,
    weakHands: [],
    currentWeakPlayer: null,
    handValue: 0,
    highestCardValue: 0,
    ...overrides,
  }),
};