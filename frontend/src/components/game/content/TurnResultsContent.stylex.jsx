import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, motion, layout, shadows, gradients } from '../../../design-system/tokens.stylex';
import { GamePiece, FooterTimer } from '../shared';
import {
  determinePiecesToReveal,
  calculateRevealDelay,
} from '../../../utils/playTypeMatching';
import { getPlayType } from '../../../utils/gameValidation';
import { TIMING } from '../../../constants';

// Animations
const fadeIn = stylex.keyframes({
  '0%': {
    opacity: 0,
    transform: 'scale(0.9)',
  },
  '100%': {
    opacity: 1,
    transform: 'scale(1)',
  },
});

const crownBounce = stylex.keyframes({
  '0%, 100%': {
    transform: 'translateY(0)',
  },
  '50%': {
    transform: 'translateY(-10px)',
  },
});

// TurnResultsContent styles
const styles = stylex.create({
  playersSummary: {
    padding: '1.5rem',
    flex: 1,
    overflowY: 'auto',
  },
  
  playerList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
  },
  
  playerRow: {
    display: 'flex',
    alignItems: 'center',
    padding: '1rem',
    borderRadius: '0.5rem',
    backgroundColor: '#ffffff',
    boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    transition: `all '300ms' 'cubic-bezier(0.4, 0, 0.2, 1)'`,
    animation: `${fadeIn} 0.3s 'cubic-bezier(0, 0, 0.2, 1)'`,
  },
  
  winner: {
    background: gradients.gold,
    borderLeftWidth: '4px',
    borderLeftStyle: 'solid',
    borderLeftColor: '#ffc107',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    position: 'relative',
    
    '::before': {
      content: '"👑"',
      position: 'absolute',
      top: '-15px',
      left: '20px',
      fontSize: '24px',
      animation: `${crownBounce} 2s 'cubic-bezier(0.4, 0, 0.2, 1)' infinite`,
    },
  },
  
  playerInfo: {
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.xxs,
    minWidth: '100px',
  },
  
  playerName: {
    fontSize: '1rem',
    fontWeight: '500',
    color: '#343a40',
  },
  
  playerPiles: {
    fontSize: '0.875rem',
    color: '#6c757d',
  },
  
  pileStatusNone: {
    color: '#6c757d',
  },
  
  pileStatusPerfect: {
    color: '#198754',
    fontWeight: '700',
  },
  
  pileStatusOver: {
    color: '#ffc107',
  },
  
  pileStatusUnder: {
    color: '#dc3545',
  },
  
  playedPieces: {
    flex: 1,
    display: 'flex',
    gap: '0.5rem',
    justifyContent: 'flex-end',
    alignItems: 'center',
    flexWrap: 'wrap',
  },
  
  twoRows: {
    flexDirection: 'column',
    alignItems: 'flex-end',
  },
  
  piecesRow: {
    display: 'flex',
    gap: '0.25rem',
  },
  
  passIndicator: {
    padding: `'0.25rem' '1rem'`,
    backgroundColor: '#e9ecef',
    borderRadius: '9999px',
    fontSize: '0.875rem',
    color: '#6c757d',
    fontStyle: 'italic',
  },
  
  playedPiece: {
    transition: `all '300ms' 'cubic-bezier(0.4, 0, 0.2, 1)'`,
  },
  
  invalidPlay: {
    opacity: 0.5,
    filter: 'grayscale(1)',
  },
  
  nextTurnInfo: {
    padding: '1.5rem',
    borderTopWidth: '1px',
    borderTopStyle: 'solid',
    borderTopColor: '#e9ecef',
    backgroundColor: '#f8f9fa',
    textAlign: 'center',
  },
  
  nextStarter: {
    fontSize: '1.125rem',
    fontWeight: '500',
    color: '#495057',
    marginBottom: '1rem',
  },
  
  autoContinue: {
    display: 'flex',
    justifyContent: 'center',
  },
});

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
  winner = ',
  winningPieces = [],
  playerPlays = [], // [{ playerName, pieces }]
  myName = ',
  turnNumber = 1,
  roundNumber = 1,
  isLastTurn = false,
  nextStarter = ',
  starterPlayType = ',
  starterName = ',
  onContinue,
}) => {
  const [flippedPieces, setFlippedPieces] = useState(new Set());

  // Determine starter play type if not provided
  const effectiveStarterPlayType =
    starterPlayType ||
    (() => {
      const starterPlay = playerPlays.find(
        (p) => p.playerName === starterName || p.playerName === winner
      );
      const calculatedType = starterPlay ? getPlayType(starterPlay.pieces) : ';
      console.log('[TurnResultsContent] Calculating starter play type:', {
        starterPlayType,
        starterName,
        winner,
        starterPlay,
        calculatedType,
      });
      return calculatedType;
    })();

  // Animate pieces on mount
  useEffect(() => {
    // Start with all pieces hidden
    const timer = setTimeout(() => {
      // Build playerPieces object for utility function
      const playerPiecesMap = {};
      playerPlays.forEach((play) => {
        playerPiecesMap[play.playerName] = play.pieces;
      });

      // Determine which pieces to reveal
      console.log('[TurnResultsContent] Determining pieces to reveal:', {
        effectiveStarterPlayType,
        starterName,
        winner,
        playerPiecesMap,
      });

      const piecesToReveal = determinePiecesToReveal(
        playerPiecesMap,
        effectiveStarterPlayType,
        starterName || winner
      );

      console.log('[TurnResultsContent] Pieces to reveal:', piecesToReveal);
      setFlippedPieces(piecesToReveal);
    }, TIMING.TURN_RESULTS_REVEAL_DELAY); // Small delay before starting animation

    return () => clearTimeout(timer);
  }, [playerPlays, effectiveStarterPlayType, starterName, winner]);
  
  // Get next phase text
  const getNextPhaseText = () => {
    if (isLastTurn) {
      return {
        starter: `${nextStarter} will start Round ${roundNumber + 1}`,
        continue: `Starting Round ${roundNumber + 1} in`,
      };
    } else {
      return {
        starter: `${nextStarter} will start Turn ${turnNumber + 1}`,
        continue: 'Continuing in',
      };
    }
  };

  const nextPhase = getNextPhaseText();

  // Get color style based on pile count vs declaration
  const getPileColorStyle = (captured, declared) => {
    if (captured === 0 && declared === 0) return styles.pileStatusNone;
    if (captured === declared && declared > 0) return styles.pileStatusPerfect;
    if (captured > declared) return styles.pileStatusOver;
    return styles.pileStatusUnder;
  };

  return (
    <>
      {/* Players summary - Show all 4 players with winner highlighted */}
      <div {...stylex.props(styles.playersSummary)}>
        <div {...stylex.props(styles.playerList)}>
          {playerPlays.map((play) => {
            const isWinner = play.playerName === winner;
            const pieceCount = play.pieces.length;
            const useTwoRows = pieceCount > 3;

            return (
              <div
                key={play.playerName}
                {...stylex.props(
                  styles.playerRow,
                  isWinner && styles.winner
                )}
              >
                <div {...stylex.props(styles.playerInfo)}>
                  <div {...stylex.props(styles.playerName)}>
                    {play.playerName}
                  </div>
                  <div {...stylex.props(
                    styles.playerPiles,
                    getPileColorStyle(
                      play.player?.captured_piles || 0,
                      play.player?.declared || 0
                    )
                  )}>
                    {play.player?.captured_piles || 0}/
                    {play.player?.declared || 0} piles
                  </div>
                </div>
                <div {...stylex.props(
                  styles.playedPieces,
                  useTwoRows && styles.twoRows
                )}>
                  {pieceCount === 0 ? (
                    <span {...stylex.props(styles.passIndicator)}>
                      Passed
                    </span>
                  ) : useTwoRows ? (
                    // For >3 pieces, split into two rows
                    <>
                      <div {...stylex.props(styles.piecesRow)}>
                        {play.pieces
                          .slice(0, Math.ceil(pieceCount / 2))
                          .map((piece, idx) => {
                            const pieceId = `${play.playerName}-${idx}`;
                            const isFlipped = flippedPieces.has(pieceId);
                            const isInvalidPlay =
                              !isFlipped && flippedPieces.size > 0;
                            const animationDelay =
                              calculateRevealDelay(
                                play.playerName,
                                playerPlays.map((p) => ({ name: p.playerName }))
                              ) / 1000;

                            return (
                              <div
                                key={idx}
                                {...stylex.props(
                                  styles.playedPiece,
                                  isInvalidPlay && styles.invalidPlay
                                )}
                              >
                                <GamePiece
                                  piece={piece}
                                  size="small"
                                  flippable
                                  flipped={isFlipped}
                                  animationDelay={
                                    isFlipped ? animationDelay : undefined
                                  }
                                />
                              </div>
                            );
                          })}
                      </div>
                      <div {...stylex.props(styles.piecesRow)}>
                        {play.pieces
                          .slice(Math.ceil(pieceCount / 2))
                          .map((piece, idx) => {
                            const actualIdx = idx + Math.ceil(pieceCount / 2);
                            const pieceId = `${play.playerName}-${actualIdx}`;
                            const isFlipped = flippedPieces.has(pieceId);
                            const isInvalidPlay =
                              !isFlipped && flippedPieces.size > 0;
                            const animationDelay =
                              calculateRevealDelay(
                                play.playerName,
                                playerPlays.map((p) => ({ name: p.playerName }))
                              ) / 1000;

                            return (
                              <div
                                key={actualIdx}
                                {...stylex.props(
                                  styles.playedPiece,
                                  isInvalidPlay && styles.invalidPlay
                                )}
                              >
                                <GamePiece
                                  piece={piece}
                                  size="small"
                                  flippable
                                  flipped={isFlipped}
                                  animationDelay={
                                    isFlipped ? animationDelay : undefined
                                  }
                                />
                              </div>
                            );
                          })}
                      </div>
                    </>
                  ) : (
                    // For ≤3 pieces, single row with larger size
                    play.pieces.map((piece, idx) => {
                      const pieceId = `${play.playerName}-${idx}`;
                      const isFlipped = flippedPieces.has(pieceId);
                      const isInvalidPlay =
                        !isFlipped && flippedPieces.size > 0;
                      const animationDelay =
                        calculateRevealDelay(
                          play.playerName,
                          playerPlays.map((p) => ({ name: p.playerName }))
                        ) / 1000;

                      return (
                        <div
                          key={idx}
                          {...stylex.props(
                            styles.playedPiece,
                            isInvalidPlay && styles.invalidPlay
                          )}
                        >
                          <GamePiece
                            piece={piece}
                            size="medium"
                            flippable
                            flipped={isFlipped}
                            animationDelay={
                              isFlipped ? animationDelay : undefined
                            }
                          />
                        </div>
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
      <div {...stylex.props(styles.nextTurnInfo)}>
        <div {...stylex.props(styles.nextStarter)}>
          {nextPhase.starter}
        </div>
        <div {...stylex.props(styles.autoContinue)}>
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
  playerPlays: PropTypes.arrayOf(
    PropTypes.shape({
      playerName: PropTypes.string,
      pieces: PropTypes.array,
      player: PropTypes.object,
    })
  ),
  myName: PropTypes.string,
  turnNumber: PropTypes.number,
  roundNumber: PropTypes.number,
  isLastTurn: PropTypes.bool,
  nextStarter: PropTypes.string,
  starterPlayType: PropTypes.string,
  starterName: PropTypes.string,
  onContinue: PropTypes.func,
};

export default TurnResultsContent;