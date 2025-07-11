import React from 'react';
import PropTypes from 'prop-types';
import { GamePiece, FooterTimer } from '../shared';

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
      {/* Players summary - Show all 4 players with winner highlighted */}
      <div className="tr-players-summary">
        <div className="tr-player-list">
          {playerPlays.map((play) => {
            const isWinner = play.playerName === winner;
            const pieceCount = play.pieces.length;
            const useTwoRows = pieceCount > 3;
            
            return (
              <div 
                key={play.playerName} 
                className={`tr-player-row ${isWinner ? 'winner' : ''}`}
              >
                <div className="tr-player-info">
                  <div className="tr-player-name">
                    {play.playerName}
                  </div>
                </div>
                <div className={`tr-played-pieces ${useTwoRows ? 'two-rows' : ''}`}>
                  {pieceCount === 0 ? (
                    <span className="tr-pass-indicator">Passed</span>
                  ) : useTwoRows ? (
                    // For >3 pieces, split into two rows
                    <>
                      <div className="pieces-row">
                        {play.pieces.slice(0, Math.ceil(pieceCount / 2)).map((piece, idx) => (
                          <GamePiece
                            key={idx}
                            piece={piece}
                            size="small"
                            className="tr-played-piece"
                          />
                        ))}
                      </div>
                      <div className="pieces-row">
                        {play.pieces.slice(Math.ceil(pieceCount / 2)).map((piece, idx) => (
                          <GamePiece
                            key={idx + Math.ceil(pieceCount / 2)}
                            piece={piece}
                            size="small"
                            className="tr-played-piece"
                          />
                        ))}
                      </div>
                    </>
                  ) : (
                    // For ≤3 pieces, single row with larger size
                    play.pieces.map((piece, idx) => (
                      <GamePiece
                        key={idx}
                        piece={piece}
                        size="medium"
                        className="tr-played-piece"
                      />
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
      
      {/* Next turn info */}
      <div className="tr-next-turn-info">
        <div className="tr-next-starter">{nextPhase.starter}</div>
        <div className="tr-auto-continue">
          <FooterTimer
            prefix={nextPhase.continue}
            onComplete={onContinue}
            variant="inline"
          />
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