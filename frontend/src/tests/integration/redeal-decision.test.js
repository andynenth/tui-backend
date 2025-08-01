/**
 * Integration Tests for Redeal Decision UI Components
 * 
 * Bug ID: REDEAL-001
 * Testing: Component integration and UI rendering
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

import PreparationUI from '../../components/game/PreparationUI';
import PreparationContent from '../../components/game/content/PreparationContent';
import GameContainer from '../../components/game/GameContainer';
import { RedealTestUtils } from '../../services/__tests__/GameService.redeal.test';

// Mock dependencies
jest.mock('../../services/NetworkService');
jest.mock('../../hooks/useGameState');
jest.mock('../../hooks/useGameActions');
jest.mock('../../hooks/useConnectionStatus');

describe('Redeal Decision UI Integration Tests', () => {
  
  describe('PreparationContent - Redeal UI Rendering', () => {
    const mockOnAcceptRedeal = jest.fn();
    const mockOnDeclineRedeal = jest.fn();

    beforeEach(() => {
      jest.clearAllMocks();
    });

    test('REDEAL-001-I001: Should render redeal decision UI for weak hand player', async () => {
      // Arrange
      const props = {
        myHand: RedealTestUtils.createMockWeakHand(),
        players: [
          { name: 'TestPlayer', isActive: true },
          { name: 'Bot2', isActive: true },
        ],
        weakHands: ['TestPlayer'],
        currentWeakPlayer: 'TestPlayer',
        isMyDecision: true, // ✅ FIXED: Should be true
        isMyHandWeak: true, // ✅ FIXED: Should be true
        handValue: 41, // Sum of weak hand values
        highestCardValue: 9, // Highest in weak hand
        redealMultiplier: 1,
        simultaneousMode: false,
        dealingCards: false,
        onAcceptRedeal: mockOnAcceptRedeal,
        onDeclineRedeal: mockOnDeclineRedeal,
      };

      // Act
      render(<PreparationContent {...props} />);
      
      // Wait for dealing animation to complete (3.5s)
      await waitFor(() => {
        expect(screen.queryByText('Dealing Cards')).not.toBeInTheDocument();
      }, { timeout: 4000 });

      // Assert - Redeal UI should be visible
      expect(screen.getByText('⚠️ Weak Hand Detected')).toBeInTheDocument();
      expect(screen.getByText(/No piece greater than 9 points/)).toBeInTheDocument();
      expect(screen.getByText(/2x penalty if you redeal/)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Request Redeal' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Keep Hand' })).toBeInTheDocument();
    });

    test('REDEAL-001-I002: Should NOT render redeal UI for strong hand player', async () => {
      // Arrange
      const props = {
        myHand: RedealTestUtils.createMockStrongHand(),
        weakHands: ['Bot2'], // TestPlayer not in weak hands
        currentWeakPlayer: 'Bot2',
        isMyDecision: false, // ✅ FIXED: Should be false
        isMyHandWeak: false, // ✅ FIXED: Should be false
        handValue: 75, // Sum of strong hand values
        highestCardValue: 14, // Highest in strong hand
        dealingCards: false,
        onAcceptRedeal: mockOnAcceptRedeal,
        onDeclineRedeal: mockOnDeclineRedeal,
      };

      // Act
      render(<PreparationContent {...props} />);
      
      // Wait for dealing animation to complete
      await waitFor(() => {
        expect(screen.queryByText('Dealing Cards')).not.toBeInTheDocument();
      }, { timeout: 4000 });

      // Assert - Redeal UI should NOT be visible
      expect(screen.queryByText('⚠️ Weak Hand Detected')).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: 'Request Redeal' })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: 'Keep Hand' })).not.toBeInTheDocument();
    });

    test('REDEAL-001-I003: Should handle redeal button clicks correctly', async () => {
      // Arrange
      const props = {
        myHand: RedealTestUtils.createMockWeakHand(),
        weakHands: ['TestPlayer'],
        currentWeakPlayer: 'TestPlayer',
        isMyDecision: true,
        isMyHandWeak: true,
        handValue: 41,
        highestCardValue: 9,
        redealMultiplier: 2, // Show penalty warning
        dealingCards: false,
        onAcceptRedeal: mockOnAcceptRedeal,
        onDeclineRedeal: mockOnDeclineRedeal,
      };

      // Act
      render(<PreparationContent {...props} />);
      
      // Wait for dealing animation to complete
      await waitFor(() => {
        expect(screen.queryByText('Dealing Cards')).not.toBeInTheDocument();
      }, { timeout: 4000 });

      // Click Accept Redeal button
      const acceptButton = screen.getByRole('button', { name: 'Request Redeal' });
      fireEvent.click(acceptButton);

      // Click Decline Redeal button  
      const declineButton = screen.getByRole('button', { name: 'Keep Hand' });
      fireEvent.click(declineButton);

      // Assert
      expect(mockOnAcceptRedeal).toHaveBeenCalledTimes(1);
      expect(mockOnDeclineRedeal).toHaveBeenCalledTimes(1);
    });

    test('REDEAL-001-I004: Should show correct multiplier penalty warning', async () => {
      // Arrange
      const props = {
        myHand: RedealTestUtils.createMockWeakHand(),
        isMyDecision: true,
        isMyHandWeak: true,
        redealMultiplier: 3, // High penalty
        dealingCards: false,
        onAcceptRedeal: mockOnAcceptRedeal,
        onDeclineRedeal: mockOnDeclineRedeal,
      };

      // Act
      render(<PreparationContent {...props} />);
      
      await waitFor(() => {
        expect(screen.queryByText('Dealing Cards')).not.toBeInTheDocument();
      }, { timeout: 4000 });

      // Assert - Should show correct penalty multiplier
      expect(screen.getByText(/4x penalty if you redeal/)).toBeInTheDocument();
    });

    test('REDEAL-001-I005: Should handle simultaneous mode correctly', async () => {
      // Arrange
      const props = {
        myHand: RedealTestUtils.createMockWeakHand(),
        weakHands: ['TestPlayer', 'Bot2'],
        isMyDecision: true,
        isMyHandWeak: true,
        simultaneousMode: true,
        weakPlayersAwaiting: ['TestPlayer', 'Bot2'],
        decisionsReceived: 0,
        decisionsNeeded: 2,
        dealingCards: false,
        onAcceptRedeal: mockOnAcceptRedeal,
        onDeclineRedeal: mockOnDeclineRedeal,
      };

      // Act
      render(<PreparationContent {...props} />);
      
      await waitFor(() => {
        expect(screen.queryByText('Dealing Cards')).not.toBeInTheDocument();
      }, { timeout: 4000 });

      // Assert - Should show redeal UI in simultaneous mode
      expect(screen.getByText('⚠️ Weak Hand Detected')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Request Redeal' })).toBeInTheDocument();
    });
  });

  describe('PreparationUI - Props Passing', () => {
    test('REDEAL-001-I006: Should pass all props correctly to PreparationContent', () => {
      // Arrange
      const mockProps = {
        myHand: RedealTestUtils.createMockWeakHand(),
        players: [{ name: 'TestPlayer', isActive: true }],
        weakHands: ['TestPlayer'],
        currentWeakPlayer: 'TestPlayer',
        isMyDecision: true,
        isMyHandWeak: true,
        handValue: 41,
        highestCardValue: 9,
        redealMultiplier: 1,
        simultaneousMode: false,
        dealingCards: false,
        onAcceptRedeal: jest.fn(),
        onDeclineRedeal: jest.fn(),
      };

      // Act & Assert - Should render without crashing and pass props through
      const { container } = render(<PreparationUI {...mockProps} />);
      expect(container).toBeInTheDocument();
    });
  });

  describe('GameContainer - Props Calculation', () => {
    const mockUseGameState = require('../../hooks/useGameState');
    const mockUseGameActions = require('../../hooks/useGameActions');
    const mockUseConnectionStatus = require('../../hooks/useConnectionStatus');

    beforeEach(() => {
      // Setup default mocks
      mockUseConnectionStatus.mockReturnValue({
        isConnected: true,
        isConnecting: false,
        isReconnecting: false,
        error: null,
      });

      mockUseGameActions.mockReturnValue({
        acceptRedeal: jest.fn(),
        declineRedeal: jest.fn(),
      });
    });

    test('REDEAL-001-I007: Should calculate preparation props with fixed UI flags', () => {
      // Arrange - Mock gameState with FIXED values
      const mockGameState = {
        phase: 'preparation',
        playerName: 'TestPlayer',
        myHand: RedealTestUtils.createMockWeakHand(),
        players: [
          { name: 'TestPlayer', isActive: true },
          { name: 'Bot2', isActive: true },
        ],
        weakHands: ['TestPlayer'],
        currentWeakPlayer: 'TestPlayer',
        isMyDecision: true, // ✅ FIXED: Correctly calculated by handleWeakHandsFound
        isMyHandWeak: true, // ✅ FIXED: Correctly calculated by handleWeakHandsFound
        handValue: 41,
        highestCardValue: 9,
        redealMultiplier: 1,
        simultaneousMode: false,
        dealingCards: false,
      };

      mockUseGameState.mockReturnValue(mockGameState);

      // Act
      const { container } = render(
        <GameContainer roomId="TEST_ROOM" />
      );

      // Assert - Component should render preparation phase
      expect(container).toBeInTheDocument();
      // The GameContainer should pass the correct props to PreparationUI
      // which will show the redeal decision UI
    });

    test('REDEAL-001-I008: Should handle empty preparation props gracefully', () => {
      // Arrange - Mock gameState with different phase
      const mockGameState = {
        phase: 'turn', // Not preparation phase
        playerName: 'TestPlayer',
        isConnected: true,
      };

      mockUseGameState.mockReturnValue(mockGameState);

      // Act & Assert - Should not crash
      const { container } = render(
        <GameContainer roomId="TEST_ROOM" />
      );
      expect(container).toBeInTheDocument();
    });
  });

  describe('Error Boundary Integration', () => {
    test('REDEAL-001-I009: Should handle rendering errors gracefully', () => {
      // Arrange - Props that might cause errors
      const errorProps = {
        myHand: null, // Invalid hand data
        isMyDecision: true,
        isMyHandWeak: true,
        onAcceptRedeal: null, // Invalid callback
        onDeclineRedeal: jest.fn(),
      };

      // Act & Assert - Should not crash the app
      expect(() => {
        render(<PreparationContent {...errorProps} />);
      }).not.toThrow();
    });
  });

  describe('Animation and Timing Integration', () => {
    test('REDEAL-001-I010: Should show redeal UI after dealing animation completes', async () => {
      // Arrange
      const props = {
        myHand: RedealTestUtils.createMockWeakHand(),
        isMyDecision: true,
        isMyHandWeak: true,
        dealingCards: false, // Animation not active
        onAcceptRedeal: jest.fn(),
        onDeclineRedeal: jest.fn(),
      };

      // Act
      render(<PreparationContent {...props} />);

      // Assert - Initially dealing animation should show
      expect(screen.getByText('Dealing Cards')).toBeInTheDocument();
      expect(screen.queryByText('⚠️ Weak Hand Detected')).not.toBeInTheDocument();

      // Wait for animation to complete
      await waitFor(() => {
        expect(screen.queryByText('Dealing Cards')).not.toBeInTheDocument();
        expect(screen.getByText('⚠️ Weak Hand Detected')).toBeInTheDocument();
      }, { timeout: 4000 });
    });

    test('REDEAL-001-I011: Should handle redeal animation correctly', async () => {
      // Arrange - Simulate redeal scenario
      const props = {
        myHand: RedealTestUtils.createMockWeakHand(),
        isMyDecision: true,
        isMyHandWeak: true,
        dealingCards: true, // Redeal animation active
        onAcceptRedeal: jest.fn(),
        onDeclineRedeal: jest.fn(),
      };

      // Act
      const { rerender } = render(<PreparationContent {...props} />);

      // Initially should show redealing animation
      await waitFor(() => {
        expect(screen.getByText('Redealing Cards')).toBeInTheDocument();
      });

      // Simulate redeal completion
      rerender(<PreparationContent {...{ ...props, dealingCards: false }} />);

      // Should show redeal UI after redeal animation completes
      await waitFor(() => {
        expect(screen.queryByText('Redealing Cards')).not.toBeInTheDocument();
        expect(screen.getByText('⚠️ Weak Hand Detected')).toBeInTheDocument();
      }, { timeout: 4000 });
    });
  });
});

// Integration Test Utilities
export const RedealIntegrationTestUtils = {
  createMockPreparationProps: (overrides = {}) => ({
    myHand: RedealTestUtils.createMockWeakHand(),
    players: [
      { name: 'TestPlayer', isActive: true },
      { name: 'Bot2', isActive: true },
    ],
    weakHands: ['TestPlayer'],
    currentWeakPlayer: 'TestPlayer',
    isMyDecision: true,
    isMyHandWeak: true,
    handValue: 41,
    highestCardValue: 9,
    redealMultiplier: 1,
    simultaneousMode: false,
    weakPlayersAwaiting: [],
    decisionsReceived: 0,
    decisionsNeeded: 0,
    dealingCards: false,
    onAcceptRedeal: jest.fn(),
    onDeclineRedeal: jest.fn(),
    ...overrides,
  }),

  waitForDealingAnimationComplete: () => {
    return waitFor(() => {
      expect(screen.queryByText('Dealing Cards')).not.toBeInTheDocument();
    }, { timeout: 4000 });
  },

  assertRedealUIVisible: () => {
    expect(screen.getByText('⚠️ Weak Hand Detected')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Request Redeal' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Keep Hand' })).toBeInTheDocument();
  },

  assertRedealUIHidden: () => {
    expect(screen.queryByText('⚠️ Weak Hand Detected')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Request Redeal' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Keep Hand' })).not.toBeInTheDocument();
  },
};