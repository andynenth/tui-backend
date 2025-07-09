import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { PlayerAvatar, GamePiece } from '../shared';

/**
 * TurnResultsContent Component
 * 
 * Displays the turn results with:
 * - Winner announcement with crown animation
 * - Winning pieces display
 * - All players' played pieces
 * - Auto-advance countdown timer
 * - Next turn/round information
 */
const TurnResultsContent = ({
  winner = '',
  winningPieces = [],
  playerPlays = [], // [{ playerName, pieces }]
  myName = '',
  turnNumber = 1,
  roundNumber = 1,
  isLastTurn = false,
  nextStarter = '',
  onContinue
}) => {
  const [countdown, setCountdown] = useState(5);
  
  // Auto-advance timer
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
  
  
  // Get next phase text
  const getNextPhaseText = () => {
    if (isLastTurn) {
      return {
        starter: `${nextStarter} will start Round ${roundNumber + 1}`,
        continue: `Starting Round ${roundNumber + 1} in`
      };
    } else {
      return {
        starter: `${nextStarter} will start Turn ${turnNumber + 1}`,
        continue: 'Continuing in'
      };
    }
  };
  
  const nextPhase = getNextPhaseText();
  
  return (
    <>
      {/* Winner announcement */}
      <div className="tr-winner-section">
        <div className="tr-winner-announcement">
          <div className="tr-crown-icon">👑</div>
          <div className="tr-winner-name">{winner} Wins!</div>
          
          {/* Winning play display */}
          {winningPieces.length > 0 && (
            <div className="tr-winning-play">
              <div className="tr-play-label">Winning Play</div>
              <div className="tr-winning-pieces">
                {winningPieces.map((piece, idx) => (
                  <GamePiece
                    key={idx}
                    piece={piece}
                    size="small"
                    className="tr-mini-piece"
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* Players summary */}
      <div className="tr-players-summary">
        <div className="tr-player-list">
          {(() => {
            // Filter out the winner - simple string comparison
            if (!winner) {
              // No winner provided, showing all players
              return playerPlays.map((play, index) => (
                <div key={play.playerName} className="tr-player-row">
                  <PlayerAvatar 
                    name={play.playerName}
                    className="tr-player-avatar"
                    size="medium"
                  />
                  <div className="tr-player-info">
                    <div className="tr-player-name">
                      {play.playerName}{play.playerName === myName ? ' (You)' : ''}
                    </div>
                  </div>
                  <div className="tr-played-pieces">
                    {play.pieces.length === 0 ? (
                      <span className="tr-pass-indicator">Passed</span>
                    ) : (
                      play.pieces.map((piece, idx) => (
                        <GamePiece
                          key={idx}
                          piece={piece}
                          size="mini"
                          className="tr-played-piece"
                        />
                      ))
                    )}
                  </div>
                </div>
              ));
            }
            
            // Filter out the winner
            const nonWinnerPlays = playerPlays.filter(play => play.playerName !== winner);
            
            // Find winner's index in original order
            const winnerIndex = playerPlays.findIndex(play => play.playerName === winner);
            
            // Reorder starting from player after winner
            const reorderedPlays = [];
            if (winnerIndex !== -1 && nonWinnerPlays.length > 0) {
              // Start from the player after the winner
              for (let i = 0; i < playerPlays.length - 1; i++) {
                const index = (winnerIndex + 1 + i) % playerPlays.length;
                const play = playerPlays[index];
                if (play.playerName !== winner) {
                  reorderedPlays.push(play);
                }
              }
            } else {
              // Fallback to original order without winner
              reorderedPlays.push(...nonWinnerPlays);
            }
            
            return reorderedPlays.map((play, index) => (
              <div key={play.playerName} className="tr-player-row">
                <PlayerAvatar 
                  name={play.playerName}
                  className="tr-player-avatar"
                  size="medium"
                />
                <div className="tr-player-info">
                  <div className="tr-player-name">
                    {play.playerName}{play.playerName === myName ? ' (You)' : ''}
                  </div>
                </div>
                <div className="tr-played-pieces">
                  {play.pieces.length === 0 ? (
                    <span className="tr-pass-indicator">Passed</span>
                  ) : (
                    play.pieces.map((piece, idx) => (
                      <GamePiece
                        key={idx}
                        piece={piece}
                        size="mini"
                        className="tr-played-piece"
                      />
                    ))
                  )}
                </div>
              </div>
            ));
          })()}
        </div>
      </div>
      
      {/* Next turn info */}
      <div className="tr-next-turn-info">
        <div className="tr-next-starter">{nextPhase.starter}</div>
        <div className="tr-auto-continue">
          {nextPhase.continue}
          <span className="tr-countdown">{countdown}</span>
          seconds
        </div>
      </div>
    </>
  );
};

TurnResultsContent.propTypes = {
  winner: PropTypes.string,
  winningPieces: PropTypes.array,
  playerPlays: PropTypes.arrayOf(PropTypes.shape({
    playerName: PropTypes.string,
    pieces: PropTypes.array
  })),
  myName: PropTypes.string,
  turnNumber: PropTypes.number,
  roundNumber: PropTypes.number,
  isLastTurn: PropTypes.bool,
  nextStarter: PropTypes.string,
  onContinue: PropTypes.func
};

export default TurnResultsContent;