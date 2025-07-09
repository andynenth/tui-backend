import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import PlayerAvatar from '../shared/PlayerAvatar';

/**
 * ScoringContent Component
 * 
 * Displays the scoring phase with:
 * - Player score cards with detailed scoring breakdown
 * - Declared vs actual piles
 * - Hit/penalty calculation
 * - Bonus points
 * - Multiplier display
 * - Total scores
 * - Auto-countdown timer
 */
const ScoringContent = ({
  players = [],
  scores = [], // Array of score objects
  roundNumber = 1,
  redealMultiplier = 1,
  myName = '',
  onContinue
}) => {
  const [countdown, setCountdown] = useState(5);
  
  // Auto-countdown timer
  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          clearInterval(timer);
          if (onContinue) {
            onContinue();
          }
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    
    return () => clearInterval(timer);
  }, [onContinue]);
  
  // Get score class based on value
  const getScoreClass = (value) => {
    if (value > 0) return 'positive';
    if (value < 0) return 'negative';
    return 'neutral';
  };
  
  // Format score display
  const formatScore = (value) => {
    if (value > 0) return `+${value}`;
    return value.toString();
  };
  
  // Get target color class
  const getTargetClass = (score) => {
    if (score.declared === 0 && score.actual === 0) return 'value-blue';
    if (score.declared === score.actual) return 'value-positive'; // Green for hits
    return 'value-negative'; // Red for misses
  };

  // Get result class - special handling for zero/zero
  const getResultClass = (score) => {
    // Special case: 0/0 shows as blue
    if (score.declared === 0 && score.actual === 0) return 'value-blue';
    if (score.hit) return 'value-positive';
    return 'value-negative';
  };
  
  // Get bonus class - special handling for zero/zero
  const getBonusClass = (score) => {
    // Special case: 0/0 bonus is blue
    if (score.declared === 0 && score.actual === 0) return 'value-blue';
    if (score.bonus > 0) return 'value-positive';
    return 'value-neutral';
  };

  // Get round score class - special handling for zero/zero
  const getRoundScoreClass = (score) => {
    if (score.declared === 0 && score.actual === 0) return 'value-blue';
    if (score.roundScore > 0) return 'value-positive';
    if (score.roundScore < 0) return 'value-negative';
    return 'value-neutral';
  };
  
  return (
    <>
      
      {/* Scoring section */}
      <div className="sc-scoring-section">
        {scores.map((score, index) => {
          const player = players.find(p => p.name === score.playerName) || { name: score.playerName };
          
          return (
            <div key={player.name} className="sc-score-card">
              {/* Top row - player and total */}
              <div className="sc-top-row">
                <div className="sc-player-info">
                  <PlayerAvatar 
                    name={player.name}
                    className="sc-player-avatar"
                    size="medium"
                  />
                  <div className="sc-player-name">
                    {player.name}{player.name === myName ? ' (You)' : ''}
                  </div>
                </div>
                
                <div className="sc-total-score">
                  <span className="sc-total-label">Total:</span>
                  <span className="sc-total-value neutral">
                    {score.totalScore}
                  </span>
                </div>
              </div>
              
              {/* Bottom row - scoring details */}
              <div className="sc-bottom-row">
                {/* Target */}
                <div className="sc-stat sc-target">
                  <span className="sc-stat-label">Target</span>
                  <span className={`sc-target-value ${getTargetClass(score)}`}>
                    {score.declared}/{score.actual}
                  </span>
                </div>
                
                {/* Hit/Penalty */}
                <div className="sc-stat">
                  <span className="sc-stat-label">{score.hit ? 'Hit' : 'Penalty'}</span>
                  <span className={`sc-stat-value ${getResultClass(score)}`}>
                    {formatScore(score.hitValue)}
                  </span>
                </div>
                
                {/* Bonus */}
                <div className="sc-stat">
                  <span className="sc-stat-label">Bonus</span>
                  <span className={`sc-stat-value ${getBonusClass(score)}`}>
                    {formatScore(score.bonus)}
                  </span>
                </div>
                
                {/* Multiplier if applicable */}
                {score.multiplier > 1 && (
                  <div className="sc-stat">
                    <span className="sc-stat-label">Mult</span>
                    <span className="sc-multiplier">
                      ×{score.multiplier}
                    </span>
                  </div>
                )}
                
                {/* Round score */}
                <div className="sc-stat">
                  <span className="sc-stat-label">Score</span>
                  <span className={`sc-stat-value ${getRoundScoreClass(score)}`}>
                    {formatScore(score.roundScore)}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
      
      {/* Continue section */}
      <div className="sc-continue-section">
        <div className="sc-continue-info">
          <div className="sc-next-round">Starting Round {roundNumber + 1}</div>
          <div className="sc-auto-continue">
            Continuing in <span className="sc-countdown">{countdown}</span> seconds
          </div>
        </div>
      </div>
    </>
  );
};

ScoringContent.propTypes = {
  players: PropTypes.array,
  scores: PropTypes.arrayOf(PropTypes.shape({
    playerName: PropTypes.string,
    declared: PropTypes.number,
    actual: PropTypes.number,
    hit: PropTypes.bool,
    hitValue: PropTypes.number,
    bonus: PropTypes.number,
    multiplier: PropTypes.number,
    roundScore: PropTypes.number,
    totalScore: PropTypes.number
  })),
  roundNumber: PropTypes.number,
  redealMultiplier: PropTypes.number,
  myName: PropTypes.string,
  onContinue: PropTypes.func
};

export default ScoringContent;