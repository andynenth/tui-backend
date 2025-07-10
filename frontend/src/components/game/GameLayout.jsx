import React from 'react';
import PropTypes from 'prop-types';

/**
 * GameLayout Component
 * 
 * Provides consistent layout wrapper for all game phases:
 * - Fixed 9:16 aspect ratio container
 * - Round indicator badge
 * - Multiplier badge (when applicable)
 * - Phase header with title/subtitle
 * - Content area for phase-specific content
 */
const GameLayout = ({ 
  children, 
  phase, 
  roundNumber = 1, 
  showMultiplier = false,
  multiplierValue = 2,
  // Additional props for turn phase
  playType = '',
  currentPlayer = '',
  turnRequirement = null
}) => {
  // Get phase title and subtitle based on current phase
  const getPhaseInfo = () => {
    switch (phase) {
      case 'preparation':
        return {
          title: 'Preparation Phase',
          subtitle: 'Dealing cards to all players'
        };
      case 'declaration':
        return {
          title: 'Declaration',
          subtitle: 'Choose your target piles'
        };
      case 'turn':
        return {
          title: playType || 'Turn Phase',
          subtitle: currentPlayer ? `Round ${roundNumber} • ${currentPlayer}'s Turn` : 'Play your pieces strategically'
        };
      case 'turn_results':
        return {
          title: 'Turn Results',
          subtitle: 'See who won this turn'
        };
      case 'scoring':
        return {
          title: 'Scoring',
          subtitle: 'Round complete'
        };
      case 'game_over':
        return {
          title: 'Game Over',
          subtitle: 'Final results'
        };
      default:
        return {
          title: 'Loading',
          subtitle: 'Please wait...'
        };
    }
  };

  const { title, subtitle } = getPhaseInfo();
  
  return (
    <div className="gl-game-container">
      {/* Round indicator */}
      <div className="gl-round-indicator">
        Round {roundNumber}
      </div>

      {/* Multiplier badge (shown conditionally) */}
      <div className={`gl-multiplier-badge ${showMultiplier ? 'show' : ''}`}>
        {multiplierValue}x Multiplier
      </div>

      {/* Phase header */}
      <div className="gl-phase-header">
        <h1 className={`gl-phase-title ${phase === 'turn' && playType ? 'turn-play-type' : ''}`}>{title}</h1>
        <p className="gl-phase-subtitle">{subtitle}</p>
      </div>

      {/* Content section */}
      <div className="gl-content-section">
        {children}
      </div>
    </div>
  );
};

GameLayout.propTypes = {
  children: PropTypes.node.isRequired,
  phase: PropTypes.oneOf([
    'preparation',
    'declaration',
    'turn',
    'turn_results',
    'scoring',
    'game_over'
  ]).isRequired,
  roundNumber: PropTypes.number,
  showMultiplier: PropTypes.bool,
  multiplierValue: PropTypes.number,
  playType: PropTypes.string,
  currentPlayer: PropTypes.string,
  turnRequirement: PropTypes.shape({
    type: PropTypes.string,
    text: PropTypes.string
  })
};

export default GameLayout;