/**
 * Test for Round Start UI with Red General Piece Display
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import RoundStartContent from '../components/game/content/RoundStartContent';

describe('RoundStartContent with Red General', () => {
  test('displays red general piece when starter has general red', () => {
    const { container } = render(
      <RoundStartContent
        roundNumber={1}
        starter="Alice"
        starterReason="has_general_red"
      />
    );

    // Check that player name is displayed
    expect(screen.getByText('Alice')).toBeInTheDocument();
    
    // Check that text reason is NOT displayed
    expect(screen.queryByText('has the General Red piece')).not.toBeInTheDocument();
    
    // Check that general piece container exists
    const generalPieceContainer = container.querySelector('.rs-general-piece');
    expect(generalPieceContainer).toBeInTheDocument();
    
    // Check that GamePiece component is rendered
    const gamePiece = container.querySelector('.game-piece');
    expect(gamePiece).toBeInTheDocument();
    expect(gamePiece).toHaveClass('game-piece--large');
  });

  test('displays text reason for other starter reasons', () => {
    render(
      <RoundStartContent
        roundNumber={2}
        starter="Bob"
        starterReason="won_last_turn"
      />
    );

    // Check that player name is displayed
    expect(screen.getByText('Bob')).toBeInTheDocument();
    
    // Check that text reason IS displayed
    expect(screen.getByText('won the last turn')).toBeInTheDocument();
    
    // Check that general piece container does NOT exist
    const generalPieceContainer = screen.queryByText('.rs-general-piece');
    expect(generalPieceContainer).not.toBeInTheDocument();
  });
});