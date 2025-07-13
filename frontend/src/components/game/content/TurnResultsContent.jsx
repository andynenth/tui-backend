import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { GamePiece, FooterTimer } from '../shared';
import { determinePiecesToReveal, calculateRevealDelay } from '../../../utils/playTypeMatching';
import { getPlayType } from '../../../utils/gameValidation';

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
  starterPlayType = '',
  starterName = '',
  onContinue
}) => {
  const [flippedPieces, setFlippedPieces] = useState(new Set());
  
  // Determine starter play type if not provided
  const effectiveStarterPlayType = starterPlayType || (() => {
    const starterPlay = playerPlays.find(p => p.playerName === starterName || p.playerName === winner);
    const calculatedType = starterPlay ? getPlayType(starterPlay.pieces) : '';
    console.log('[TurnResultsContent] Calculating starter play type:', {
      starterPlayType,
      starterName,
      winner,
      starterPlay,
      calculatedType
    });
    return calculatedType;
  })();
  
  // Animate pieces on mount
  useEffect(() => {
    // Start with all pieces hidden
    const timer = setTimeout(() => {
      // Build playerPieces object for utility function
      const playerPiecesMap = {};
      playerPlays.forEach(play => {
        playerPiecesMap[play.playerName] = play.pieces;
      });
      
      // Determine which pieces to reveal
      console.log('[TurnResultsContent] Determining pieces to reveal:', {
        effectiveStarterPlayType,
        starterName,
        winner,
        playerPiecesMap
      });
      
      const piecesToReveal = determinePiecesToReveal(
        playerPiecesMap,
        effectiveStarterPlayType,
        starterName || winner
      );
      
      console.log('[TurnResultsContent] Pieces to reveal:', piecesToReveal);
      setFlippedPieces(piecesToReveal);
    }, 200); // Small delay before starting animation
    
    return () => clearTimeout(timer);
  }, [playerPlays, effectiveStarterPlayType, starterName, winner]);
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
  
  // Get color class based on pile count vs declaration
  const getPileColorClass = (captured, declared) => {
    if (captured === 0 && declared === 0) return 'pile-status-none';
    if (captured === declared && declared > 0) return 'pile-status-perfect';
    if (captured > declared) return 'pile-status-over';
    return 'pile-status-under';
  };
  
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
                  <div className={`tr-player-piles ${getPileColorClass(play.player?.captured_piles || 0, play.player?.declared || 0)}`}>
                    {play.player?.captured_piles || 0}/{play.player?.declared || 0} piles
                  </div>
                </div>
                <div className={`tr-played-pieces ${useTwoRows ? 'two-rows' : ''}`}>
                  {pieceCount === 0 ? (
                    <span className="tr-pass-indicator">Passed</span>
                  ) : useTwoRows ? (
                    // For >3 pieces, split into two rows
                    <>
                      <div className="pieces-row">
                        {play.pieces.slice(0, Math.ceil(pieceCount / 2)).map((piece, idx) => {
                          const pieceId = `${play.playerName}-${idx}`;
                          const isFlipped = flippedPieces.has(pieceId);
                          const isInvalidPlay = !isFlipped && flippedPieces.size > 0;
                          const animationDelay = calculateRevealDelay(play.playerName, playerPlays.map(p => ({ name: p.playerName }))) / 1000;
                          
                          return (
                            <GamePiece
                              key={idx}
                              piece={piece}
                              size="small"
                              flippable
                              flipped={isFlipped}
                              className={`tr-played-piece ${isInvalidPlay ? 'invalid-play' : ''}`}
                              animationDelay={isFlipped ? animationDelay : undefined}
                            />
                          );
                        })}
                      </div>
                      <div className="pieces-row">
                        {play.pieces.slice(Math.ceil(pieceCount / 2)).map((piece, idx) => {
                          const actualIdx = idx + Math.ceil(pieceCount / 2);
                          const pieceId = `${play.playerName}-${actualIdx}`;
                          const isFlipped = flippedPieces.has(pieceId);
                          const isInvalidPlay = !isFlipped && flippedPieces.size > 0;
                          const animationDelay = calculateRevealDelay(play.playerName, playerPlays.map(p => ({ name: p.playerName }))) / 1000;
                          
                          return (
                            <GamePiece
                              key={actualIdx}
                              piece={piece}
                              size="small"
                              flippable
                              flipped={isFlipped}
                              className={`tr-played-piece ${isInvalidPlay ? 'invalid-play' : ''}`}
                              animationDelay={isFlipped ? animationDelay : undefined}
                            />
                          );
                        })}
                      </div>
                    </>
                  ) : (
                    // For ≤3 pieces, single row with larger size
                    play.pieces.map((piece, idx) => {
                      const pieceId = `${play.playerName}-${idx}`;
                      const isFlipped = flippedPieces.has(pieceId);
                      const isInvalidPlay = !isFlipped && flippedPieces.size > 0;
                      const animationDelay = calculateRevealDelay(play.playerName, playerPlays.map(p => ({ name: p.playerName }))) / 1000;
                      
                      return (
                        <GamePiece
                          key={idx}
                          piece={piece}
                          size="medium"
                          flippable
                          flipped={isFlipped}
                          className={`tr-played-piece ${isInvalidPlay ? 'invalid-play' : ''}`}
                          animationDelay={isFlipped ? animationDelay : undefined}
                        />
                      );
                    })
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
    pieces: PropTypes.array,
    player: PropTypes.object
  })),
  myName: PropTypes.string,
  turnNumber: PropTypes.number,
  roundNumber: PropTypes.number,
  isLastTurn: PropTypes.bool,
  nextStarter: PropTypes.string,
  starterPlayType: PropTypes.string,
  starterName: PropTypes.string,
  onContinue: PropTypes.func
};

export default TurnResultsContent;