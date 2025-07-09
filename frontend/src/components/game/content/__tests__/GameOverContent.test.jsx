import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import GameOverContent from '../GameOverContent';

// Mock data for testing
const mockPlayers = [
  { id: 'Alice', name: 'Alice', turns_won: 12, perfect_rounds: 5 },
  { id: 'Bob', name: 'Bob', turns_won: 8, perfect_rounds: 3 },
  { id: 'Charlie', name: 'Charlie', turns_won: 0, perfect_rounds: 0 },
  { id: 'Diana', name: 'Diana', turns_won: 2, perfect_rounds: 1 }
];

const mockFinalScores = {
  Alice: 58,
  Bob: 45,
  Charlie: 32,
  Diana: 38
};

const mockWinner = { id: 'Alice', name: 'Alice' };

const mockGameStats = {
  totalRounds: 20,
  duration: 2700, // 45 minutes in seconds
  highestScore: 58
};

describe('GameOverContent', () => {
  const renderComponent = (props = {}) => {
    const defaultProps = {
      winner: mockWinner,
      finalScores: mockFinalScores,
      players: mockPlayers,
      gameStats: mockGameStats,
      onBackToLobby: jest.fn()
    };
    
    return render(
      <BrowserRouter>
        <GameOverContent {...defaultProps} {...props} />
      </BrowserRouter>
    );
  };

  test('displays winner name correctly', () => {
    renderComponent();
    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.getByText('Champion!')).toBeInTheDocument();
  });

  test('displays player statistics correctly', () => {
    renderComponent();
    
    // Check Alice's stats
    expect(screen.getByText('Won 12 turns • 5 perfect rounds')).toBeInTheDocument();
    
    // Check Bob's stats
    expect(screen.getByText('Won 8 turns • 3 perfect rounds')).toBeInTheDocument();
    
    // Check Charlie's stats (no wins)
    expect(screen.getByText('No turns won')).toBeInTheDocument();
    
    // Check Diana's stats (singular)
    expect(screen.getByText('Won 2 turns • 1 perfect round')).toBeInTheDocument();
  });

  test('displays final scores correctly', () => {
    renderComponent();
    
    expect(screen.getByText('58')).toBeInTheDocument(); // Alice
    expect(screen.getByText('45')).toBeInTheDocument(); // Bob
    expect(screen.getByText('32')).toBeInTheDocument(); // Charlie
    expect(screen.getByText('38')).toBeInTheDocument(); // Diana
  });

  test('displays medals for top 3 players', () => {
    renderComponent();
    
    const medals = screen.getAllByText(/[🥇🥈🥉]/u);
    expect(medals).toHaveLength(3); // Only top 3 get medals
  });

  test('displays game statistics', () => {
    renderComponent();
    
    expect(screen.getByText('20')).toBeInTheDocument(); // Total rounds
    expect(screen.getByText('45:00')).toBeInTheDocument(); // Duration
    expect(screen.getByText('58')).toBeInTheDocument(); // Highest score
  });

  test('displays countdown timer', () => {
    renderComponent();
    
    expect(screen.getByText(/Returning to lobby in \d+ seconds/)).toBeInTheDocument();
  });

  test('handles missing statistics gracefully', () => {
    const playersWithoutStats = mockPlayers.map(p => ({ ...p, turns_won: undefined, perfect_rounds: undefined }));
    
    renderComponent({ players: playersWithoutStats });
    
    // Should show "No turns won" for all players
    const noTurnsWonElements = screen.getAllByText('No turns won');
    expect(noTurnsWonElements).toHaveLength(4);
  });

  test('handles missing winner gracefully', () => {
    renderComponent({ winner: null });
    
    expect(screen.getByText('Unknown')).toBeInTheDocument();
  });

  test('sorts players by score correctly', () => {
    renderComponent();
    
    const playerNames = screen.getAllByText(/Alice|Bob|Charlie|Diana/);
    // First occurrence of each name should be in score order
    expect(playerNames[0]).toHaveTextContent('Alice'); // 58 points
    expect(playerNames[2]).toHaveTextContent('Bob');   // 45 points
    expect(playerNames[4]).toHaveTextContent('Diana'); // 38 points
    expect(playerNames[6]).toHaveTextContent('Charlie'); // 32 points
  });
});