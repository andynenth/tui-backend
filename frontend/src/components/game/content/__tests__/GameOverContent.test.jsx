import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import GameOverContent from '../GameOverContent';

// Mock the FooterTimer component to control timer behavior
jest.mock('../../shared/FooterTimer', () => ({
  __esModule: true,
  default: ({ onComplete, duration, prefix, suffix, variant }) => (
    <div data-testid="footer-timer" data-duration={duration}>
      {prefix} {duration} {suffix}
      <button data-testid="complete-timer" onClick={onComplete}>
        Complete Timer
      </button>
    </div>
  ),
}));

// Mock data for testing
const mockPlayers = [
  { id: 'Alice', name: 'Alice', turns_won: 12, perfect_rounds: 5 },
  { id: 'Bob', name: 'Bob', turns_won: 8, perfect_rounds: 3 },
  { id: 'Charlie', name: 'Charlie', turns_won: 0, perfect_rounds: 0 },
  { id: 'Diana', name: 'Diana', turns_won: 2, perfect_rounds: 1 },
];

const mockFinalScores = {
  Alice: 58,
  Bob: 45,
  Charlie: 32,
  Diana: 38,
};

const mockWinner = { id: 'Alice', name: 'Alice' };

const mockGameStats = {
  totalRounds: 20,
  duration: 2700, // 45 minutes in seconds
  highestScore: 58,
};

describe('GameOverContent', () => {
  const renderComponent = (props = {}) => {
    const defaultProps = {
      winner: mockWinner,
      finalScores: mockFinalScores,
      players: mockPlayers,
      gameStats: mockGameStats,
      onBackToLobby: jest.fn(),
    };

    return render(
      <BrowserRouter>
        <GameOverContent {...defaultProps} {...props} />
      </BrowserRouter>
    );
  };

  describe('Basic Display Tests', () => {
    test('displays winner name correctly', () => {
      renderComponent();
      // Use more specific query since Alice appears multiple times
      const winnerSection = document.querySelector('.go-winner-section');
      expect(winnerSection).toBeInTheDocument();
      expect(winnerSection.querySelector('.go-winner-name')).toHaveTextContent(
        'Alice'
      );
      expect(screen.getByText('Champion!')).toBeInTheDocument();
    });

    test('displays player statistics correctly', () => {
      renderComponent();

      // Check Alice's stats
      expect(screen.getByText('5 perfect rounds')).toBeInTheDocument();

      // Check Bob's stats
      expect(screen.getByText('3 perfect rounds')).toBeInTheDocument();

      // Check Charlie's stats (no perfect rounds)
      expect(screen.getByText('Aim needs work 🎯')).toBeInTheDocument();

      // Check Diana's stats (singular)
      expect(screen.getByText('1 perfect round')).toBeInTheDocument();
    });

    test('displays final scores correctly', () => {
      renderComponent();

      // Get all final scores
      const finalScores = document.querySelectorAll('.go-final-score');
      const scores = Array.from(finalScores).map((el) => el.textContent);

      // Check that all expected scores are present
      expect(scores).toContain('58'); // Alice
      expect(scores).toContain('45'); // Bob
      expect(scores).toContain('32'); // Charlie
      expect(scores).toContain('38'); // Diana
    });

    test('displays medals for top 3 players', () => {
      renderComponent();

      const medals = screen.getAllByText(/[🥇🥈🥉]/u);
      expect(medals).toHaveLength(3); // Only top 3 get medals
    });

    test('displays game statistics', () => {
      renderComponent();

      expect(screen.getByText('Game Statistics')).toBeInTheDocument();
      expect(screen.getByText('Game Duration')).toBeInTheDocument();
      expect(screen.getByText('Rounds Played')).toBeInTheDocument();
      expect(screen.getByText('Highest Score')).toBeInTheDocument();

      expect(screen.getByText('20')).toBeInTheDocument(); // Total rounds

      // Find duration specifically
      const durationItem = Array.from(
        document.querySelectorAll('.go-stat-item')
      ).find(
        (item) =>
          item.querySelector('.go-stat-label')?.textContent === 'Game Duration'
      );
      expect(durationItem.querySelector('.go-stat-value').textContent).toBe(
        '45'
      );
    });

    test('displays countdown timer', () => {
      renderComponent();

      expect(screen.getByText(/Returning to lobby in/)).toBeInTheDocument();
      expect(screen.getByTestId('footer-timer')).toHaveAttribute(
        'data-duration',
        '10'
      );
    });
  });

  describe('Confetti Animation Tests', () => {
    test('renders 50 confetti particles', () => {
      renderComponent();
      const confettiParticles = document.querySelectorAll('.go-confetti');
      expect(confettiParticles).toHaveLength(50);
    });

    test('confetti particles have random properties', () => {
      renderComponent();
      const particles = document.querySelectorAll('.go-confetti');

      const colorClasses = new Set();
      const sizeClasses = new Set();
      const positions = new Set();

      particles.forEach((particle) => {
        // Check color variety
        const colorClass = Array.from(particle.classList).find((c) =>
          c.includes('color-')
        );
        if (colorClass) colorClasses.add(colorClass);

        // Check size variety
        const sizeClass = Array.from(particle.classList).find((c) =>
          c.includes('size-')
        );
        if (sizeClass) sizeClasses.add(sizeClass);

        // Check position variety
        const left = particle.style.left;
        positions.add(left);
      });

      // Should have variety in properties
      expect(colorClasses.size).toBeGreaterThan(1);
      expect(sizeClasses.size).toBeGreaterThan(1);
      expect(positions.size).toBeGreaterThan(10); // Should have many different positions
    });

    test('confetti particles have animation properties', () => {
      renderComponent();
      const particles = document.querySelectorAll('.go-confetti');

      particles.forEach((particle) => {
        const delay = parseFloat(particle.style.animationDelay);
        const duration = parseFloat(particle.style.animationDuration);

        // Check animation delay is within expected range
        expect(delay).toBeGreaterThanOrEqual(0);
        expect(delay).toBeLessThan(3);

        // Check animation duration is within expected range
        expect(duration).toBeGreaterThanOrEqual(3);
        expect(duration).toBeLessThan(5);
      });
    });
  });

  describe('Trophy Animation Tests', () => {
    test('renders trophy with correct emoji and container', () => {
      renderComponent();
      expect(screen.getByText('🏆')).toBeInTheDocument();

      const trophy = screen.getByText('🏆');
      expect(trophy).toHaveClass('go-trophy');
      expect(trophy.closest('.go-trophy-container')).toBeInTheDocument();
    });
  });

  describe('Action Button Tests', () => {
    test('Return to Lobby button is clickable', () => {
      const mockOnBackToLobby = jest.fn();
      renderComponent({ onBackToLobby: mockOnBackToLobby });

      const returnButton = screen.getByText('Return to Lobby');
      expect(returnButton).not.toBeDisabled();
      expect(returnButton).toHaveClass('go-action-button', 'primary');

      fireEvent.click(returnButton);
      expect(mockOnBackToLobby).toHaveBeenCalledTimes(1);
    });

    test('Play Again button is disabled', () => {
      renderComponent();

      const playAgainButton = screen.getByText('Play Again');
      expect(playAgainButton).toBeDisabled();
      expect(playAgainButton).toHaveClass('go-action-button', 'secondary');
    });
  });

  describe('Timer Functionality Tests', () => {
    test('calls onBackToLobby when timer completes', () => {
      const mockOnBackToLobby = jest.fn();
      renderComponent({ onBackToLobby: mockOnBackToLobby });

      // Simulate timer completion
      const completeButton = screen.getByTestId('complete-timer');
      fireEvent.click(completeButton);

      expect(mockOnBackToLobby).toHaveBeenCalledTimes(1);
    });

    test('timer displays correct prefix and suffix', () => {
      renderComponent();

      expect(screen.getByText(/Returning to lobby in/)).toBeInTheDocument();
      expect(screen.getByText(/seconds/)).toBeInTheDocument();
    });
  });

  describe('Edge Case Tests', () => {
    test('handles missing statistics gracefully', () => {
      const playersWithoutStats = mockPlayers.map((p) => ({
        ...p,
        turns_won: undefined,
        perfect_rounds: undefined,
      }));

      renderComponent({ players: playersWithoutStats });

      // Should show "Aim needs work 🎯" for all players with undefined stats
      const aimNeedsWorkElements = screen.getAllByText('Aim needs work 🎯');
      expect(aimNeedsWorkElements).toHaveLength(4);
    });

    test('handles missing winner gracefully', () => {
      renderComponent({ winner: null });

      expect(screen.getByText('Unknown')).toBeInTheDocument();
    });

    test('sorts players by score correctly', () => {
      renderComponent();

      // Get player names in ranking order
      const rankItems = document.querySelectorAll('.go-rank-item');
      const playerNamesInOrder = Array.from(rankItems).map(
        (item) => item.querySelector('.go-player-name').textContent
      );

      // Check order is correct (by score descending)
      expect(playerNamesInOrder[0]).toBe('Alice'); // 58 points
      expect(playerNamesInOrder[1]).toBe('Bob'); // 45 points
      expect(playerNamesInOrder[2]).toBe('Diana'); // 38 points
      expect(playerNamesInOrder[3]).toBe('Charlie'); // 32 points
    });

    test('handles empty players array', () => {
      renderComponent({ players: [] });

      // Rankings section should exist without title
      expect(document.querySelector('.go-rankings')).toBeInTheDocument();
      // Should not crash, rankings container should be empty
      const rankingsContainer = document.querySelector('.go-rankings');
      expect(rankingsContainer).toBeInTheDocument();
      expect(rankingsContainer.children).toHaveLength(0);
    });

    test('handles missing game stats', () => {
      renderComponent({ gameStats: null });

      // Should not show stats section
      expect(screen.queryByText('Game Statistics')).not.toBeInTheDocument();
    });

    test('formats game duration correctly for edge cases', () => {
      // Test 0 seconds (0 minutes)
      const { rerender } = renderComponent({
        gameStats: { duration: 0, totalRounds: 1, highestScore: 0 },
      });

      // Find the duration value specifically by looking for the Game Duration label
      let durationItem = Array.from(
        document.querySelectorAll('.go-stat-item')
      ).find(
        (item) =>
          item.querySelector('.go-stat-label')?.textContent === 'Game Duration'
      );
      expect(durationItem).toBeTruthy();
      expect(durationItem.querySelector('.go-stat-value').textContent).toBe(
        '0'
      );

      // Test exactly 1 minute
      rerender(
        <BrowserRouter>
          <GameOverContent
            winner={mockWinner}
            finalScores={mockFinalScores}
            players={mockPlayers}
            gameStats={{ duration: 60, totalRounds: 1, highestScore: 0 }}
            onBackToLobby={jest.fn()}
          />
        </BrowserRouter>
      );
      durationItem = Array.from(
        document.querySelectorAll('.go-stat-item')
      ).find(
        (item) =>
          item.querySelector('.go-stat-label')?.textContent === 'Game Duration'
      );
      expect(durationItem).toBeTruthy();
      expect(durationItem.querySelector('.go-stat-value').textContent).toBe(
        '1'
      );

      // Test 65 seconds (1 minute, ignoring extra seconds)
      rerender(
        <BrowserRouter>
          <GameOverContent
            winner={mockWinner}
            finalScores={mockFinalScores}
            players={mockPlayers}
            gameStats={{ duration: 65, totalRounds: 1, highestScore: 0 }}
            onBackToLobby={jest.fn()}
          />
        </BrowserRouter>
      );
      durationItem = Array.from(
        document.querySelectorAll('.go-stat-item')
      ).find(
        (item) =>
          item.querySelector('.go-stat-label')?.textContent === 'Game Duration'
      );
      expect(durationItem).toBeTruthy();
      expect(durationItem.querySelector('.go-stat-value').textContent).toBe(
        '1'
      );
    });

    test('handles tied scores correctly', () => {
      const tiedScores = {
        Alice: 50,
        Bob: 50,
        Charlie: 50,
        Diana: 30,
      };

      renderComponent({ finalScores: tiedScores });

      // All tied players should still get correct medals
      const medals = screen.getAllByText(/[🥇🥈🥉]/u);
      expect(medals).toHaveLength(3); // Still only top 3 positions get medals
    });

    test('handles missing player scores', () => {
      const incompleteScores = {
        Alice: 58,
        Bob: 45,
        // Charlie and Diana scores missing
      };

      renderComponent({ finalScores: incompleteScores });

      // Should display 0 for missing scores
      const zeroScores = screen.getAllByText('0');
      expect(zeroScores.length).toBeGreaterThanOrEqual(2); // At least Charlie and Diana should show 0
    });
  });

  describe('Accessibility Tests', () => {
    test('has proper button roles and labels', () => {
      renderComponent();

      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThanOrEqual(2); // At least Return to Lobby and Play Again

      const returnButton = screen.getByRole('button', {
        name: /Return to Lobby/i,
      });
      expect(returnButton).toBeInTheDocument();

      const playAgainButton = screen.getByRole('button', {
        name: /Play Again/i,
      });
      expect(playAgainButton).toBeInTheDocument();
    });

    test('has proper semantic structure', () => {
      renderComponent();

      // Check main containers exist
      expect(document.querySelector('.go-content')).toBeInTheDocument();
      expect(
        document.querySelector('.go-trophy-container')
      ).toBeInTheDocument();
      expect(document.querySelector('.go-winner-section')).toBeInTheDocument();
      expect(
        document.querySelector('.go-rankings-container')
      ).toBeInTheDocument();
      expect(document.querySelector('.go-actions')).toBeInTheDocument();
    });
  });

  describe('Integration Tests', () => {
    test('full game over flow works correctly', () => {
      const mockOnBackToLobby = jest.fn();
      renderComponent({ onBackToLobby: mockOnBackToLobby });

      // Check all major elements are present
      const winnerSection = document.querySelector('.go-winner-section');
      expect(winnerSection.querySelector('.go-winner-name')).toHaveTextContent(
        'Alice'
      );
      expect(screen.getByText('Champion!')).toBeInTheDocument();
      // Rankings section should exist without title
      expect(document.querySelector('.go-rankings')).toBeInTheDocument();
      expect(screen.getByText('Return to Lobby')).toBeInTheDocument();

      // Check confetti is animating
      const confetti = document.querySelectorAll('.go-confetti');
      expect(confetti.length).toBe(50);

      // Test manual return to lobby
      fireEvent.click(screen.getByText('Return to Lobby'));
      expect(mockOnBackToLobby).toHaveBeenCalledTimes(1);

      // Test timer-based return
      mockOnBackToLobby.mockClear();
      fireEvent.click(screen.getByTestId('complete-timer'));
      expect(mockOnBackToLobby).toHaveBeenCalledTimes(1);
    });

    test('renders correctly with minimal data', () => {
      const minimalProps = {
        winner: { id: 'Test', name: 'Test Player' },
        finalScores: { Test: 100 },
        players: [{ id: 'Test', name: 'Test Player' }],
        gameStats: null,
        onBackToLobby: jest.fn(),
      };

      renderComponent(minimalProps);

      // Should still render without crashing
      const winnerSection = document.querySelector('.go-winner-section');
      expect(winnerSection.querySelector('.go-winner-name')).toHaveTextContent(
        'Test Player'
      );
      expect(screen.getByText('Champion!')).toBeInTheDocument();

      // Check score is displayed
      const finalScores = document.querySelectorAll('.go-final-score');
      expect(
        Array.from(finalScores).some((el) => el.textContent === '100')
      ).toBe(true);
    });
  });
});
