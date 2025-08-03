/**
 * 🏆 **TurnResultsUI Component** - Turn Results Interface with StyleX
 *
 * Features:
 * ✅ Winner announcement with animations
 * ✅ All players' played pieces display
 * ✅ Piece flip animations for reveals
 * ✅ Auto-advance countdown timer
 * ✅ StyleX for optimized styling
 */

import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
import GamePiece from './shared/GamePiece.stylex';
import FooterTimer from './shared/FooterTimer.stylex';
import PlayerAvatar from './shared/PlayerAvatar.stylex';
import {
  determinePiecesToReveal,
  calculateRevealDelay,
} from '../../utils/playTypeMatching';
import { getPlayType } from '../../utils/gameValidation';
import { formatPlayType } from '../../utils/playTypeFormatter';
import { TIMING } from '../../constants';
import { colors, spacing, shadows, layout, motion, typography } from '../../design-system/tokens.stylex';

// Animation keyframes
const fadeIn = stylex.keyframes({
  '0%': {
    opacity: 0,
    transform: 'translateY(20px)',
  },
  '100%': {
    opacity: 1,
    transform: 'translateY(0)',
  },
});

const crownBounce = stylex.keyframes({
  '0%, 100%': {
    transform: 'translateY(0) rotate(0deg)',
  },
  '25%': {
    transform: 'translateY(-10px) rotate(-5deg)',
  },
  '75%': {
    transform: 'translateY(-10px) rotate(5deg)',
  },
});

const pulse = stylex.keyframes({
  '0%, 100%': {
    transform: 'scale(1)',
    opacity: 1,
  },
  '50%': {
    transform: 'scale(1.05)',
    opacity: 0.9,
  },
});

const slideUp = stylex.keyframes({
  '0%': {
    opacity: 0,
    transform: 'translateY(100%)',
  },
  '100%': {
    opacity: 1,
    transform: 'translateY(0)',
  },
});

const styles = stylex.create({
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    backgroundColor: colors.background,
    position: 'relative',
  },
  
  // Header section
  header: {
    padding: spacing.xl,
    textAlign: 'center',
    backgroundColor: colors.surface,
    borderBottom: `1px solid ${colors.border}`,
    boxShadow: shadows.sm,
  },
  
  winnerAnnouncement: {
    fontSize: typography.headingLg,
    fontWeight: typography.weightBold,
    color: colors.primary,
    marginBottom: spacing.md,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.md,
    animation: `${fadeIn} ${motion.durationNormal} ${motion.easeOut}`,
  },
  
  crown: {
    fontSize: '2rem',
    animation: `${crownBounce} 2s ${motion.easeInOut} infinite`,
  },
  
  turnInfo: {
    fontSize: typography.textMd,
    color: colors.gray600,
  },
  
  // Players summary section
  playersSummary: {
    flex: 1,
    overflowY: 'auto',
    padding: spacing.lg,
  },
  
  playerList: {
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.md,
    maxWidth: '800px',
    margin: '0 auto',
  },
  
  // Player row
  playerRow: {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.lg,
    padding: spacing.lg,
    backgroundColor: colors.surface,
    borderRadius: layout.radiusMd,
    boxShadow: shadows.sm,
    transition: motion.transitionBase,
    animation: `${slideUp} ${motion.durationNormal} ${motion.easeOut}`,
  },
  
  playerRowWinner: {
    backgroundColor: colors.successLight,
    borderColor: colors.success,
    borderWidth: '2px',
    borderStyle: 'solid',
    boxShadow: shadows.md,
    animation: `${pulse} 2s ${motion.easeInOut} infinite`,
  },
  
  // Player info
  playerInfo: {
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.xs,
    minWidth: '150px',
  },
  
  playerHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.sm,
  },
  
  playerName: {
    fontSize: typography.textMd,
    fontWeight: typography.weightMedium,
    color: colors.textDark,
  },
  
  winnerBadge: {
    backgroundColor: colors.success,
    color: colors.textLight,
    padding: `${spacing.xs} ${spacing.sm}`,
    borderRadius: layout.radiusFull,
    fontSize: typography.textXs,
    fontWeight: typography.weightBold,
    textTransform: 'uppercase',
  },
  
  playerStats: {
    display: 'flex',
    gap: spacing.md,
    fontSize: typography.textSm,
  },
  
  statItem: {
    display: 'flex',
    gap: spacing.xs,
    alignItems: 'center',
  },
  
  // Pile status colors
  pileStatusNone: {
    color: colors.gray500,
  },
  
  pileStatusPerfect: {
    color: colors.success,
    fontWeight: typography.weightBold,
  },
  
  pileStatusOver: {
    color: colors.warning,
  },
  
  pileStatusUnder: {
    color: colors.danger,
  },
  
  // Played pieces
  playedPieces: {
    flex: 1,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'flex-end',
    gap: spacing.sm,
    flexWrap: 'wrap',
  },
  
  playedPiecesTwoRows: {
    flexDirection: 'column',
    alignItems: 'flex-end',
  },
  
  piecesRow: {
    display: 'flex',
    gap: spacing.xs,
  },
  
  passIndicator: {
    padding: `${spacing.sm} ${spacing.md}`,
    backgroundColor: colors.gray100,
    color: colors.gray600,
    borderRadius: layout.radiusMd,
    fontSize: typography.textSm,
    fontStyle: 'italic',
  },
  
  playedPiece: {
    transition: `transform ${motion.durationFast} ${motion.easeOut}`,
    
    ':hover': {
      transform: 'translateY(-4px)',
    },
  },
  
  invalidPlay: {
    opacity: 0.5,
    filter: 'grayscale(1)',
  },
  
  // Play type badge
  playTypeBadge: {
    backgroundColor: colors.primary,
    color: colors.textLight,
    padding: `${spacing.xs} ${spacing.sm}`,
    borderRadius: layout.radiusFull,
    fontSize: typography.textXs,
    fontWeight: typography.weightMedium,
    textTransform: 'uppercase',
  },
  
  // Next turn info
  nextTurnInfo: {
    padding: spacing.xl,
    backgroundColor: colors.surface,
    borderTop: `1px solid ${colors.border}`,
    textAlign: 'center',
    boxShadow: shadows.sm,
  },
  
  nextStarter: {
    fontSize: typography.textLg,
    fontWeight: typography.weightMedium,
    color: colors.textDark,
    marginBottom: spacing.md,
  },
  
  autoContinue: {
    display: 'flex',
    justifyContent: 'center',
  },
  
  // Summary bar
  summaryBar: {
    display: 'flex',
    justifyContent: 'space-around',
    padding: spacing.md,
    backgroundColor: colors.surfaceLight,
    borderTop: `1px solid ${colors.border}`,
  },
  
  summaryItem: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: spacing.xs,
  },
  
  summaryLabel: {
    fontSize: typography.textXs,
    color: colors.gray600,
  },
  
  summaryValue: {
    fontSize: typography.textMd,
    fontWeight: typography.weightBold,
    color: colors.primary,
  },
});

/**
 * TurnResultsUI - Turn results display with StyleX
 */
export function TurnResultsUI({
  // Data props
  winner = '',
  winningPlay = null,
  playerPiles = {},
  players = [],
  turnNumber = 1,
  roundNumber = 1,
  nextStarter = '',
  playerName = '',
  isLastTurn = false,
  currentTurnPlays = [],
  
  // Action props
  onContinue,
  
  // Additional props
  className = '',
}) {
  const [flippedPieces, setFlippedPieces] = useState(new Set());
  
  // Extract winning pieces
  const winningPieces = winningPlay?.pieces || [];
  
  // Build player plays array
  const playerPlays = players.map((player) => {
    const turnPlay = currentTurnPlays.find(
      (play) => play.player === player.name
    );
    return {
      playerName: player.name,
      player,
      pieces: turnPlay?.pieces || turnPlay?.cards || [],
      playType: turnPlay?.playType || turnPlay?.play_type,
      isValid: turnPlay?.isValid,
    };
  });
  
  // Find starter info
  const starterPlay = currentTurnPlays.find(
    (play) => play.isStarter || play.player === winningPlay?.starter
  );
  const starterName = starterPlay?.player || winner;
  const starterPlayType = starterPlay?.playType || starterPlay?.play_type || winningPlay?.type || '';
  
  // Determine effective starter play type
  const effectiveStarterPlayType = starterPlayType || (() => {
    const starterPlayerPlay = playerPlays.find(
      (p) => p.playerName === starterName || p.playerName === winner
    );
    return starterPlayerPlay ? getPlayType(starterPlayerPlay.pieces) : '';
  })();
  
  // Animate pieces on mount
  useEffect(() => {
    const timer = setTimeout(() => {
      const playerPiecesMap = {};
      playerPlays.forEach((play) => {
        playerPiecesMap[play.playerName] = play.pieces;
      });
      
      const piecesToReveal = determinePiecesToReveal(
        playerPiecesMap,
        effectiveStarterPlayType,
        starterName || winner
      );
      
      setFlippedPieces(piecesToReveal);
    }, TIMING.TURN_RESULTS_REVEAL_DELAY);
    
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
  
  // Get pile status style
  const getPileStatusStyle = (captured, declared) => {
    if (captured === 0 && declared === 0) return styles.pileStatusNone;
    if (captured === declared && declared > 0) return styles.pileStatusPerfect;
    if (captured > declared) return styles.pileStatusOver;
    return styles.pileStatusUnder;
  };
  
  // Calculate total plays and passes
  const totalPlays = playerPlays.filter(p => p.pieces.length > 0).length;
  const totalPasses = playerPlays.filter(p => p.pieces.length === 0).length;
  
  return (
    <div {...stylex.props(styles.container, className && { className })}>
      {/* Header with winner announcement */}
      <div {...stylex.props(styles.header)}>
        <div {...stylex.props(styles.winnerAnnouncement)}>
          <span {...stylex.props(styles.crown)}>👑</span>
          <span>{winner} wins Turn {turnNumber}!</span>
          <span {...stylex.props(styles.crown)}>👑</span>
        </div>
        <div {...stylex.props(styles.turnInfo)}>
          Round {roundNumber} • Turn {turnNumber}
          {effectiveStarterPlayType && (
            <span> • {formatPlayType(effectiveStarterPlayType)}</span>
          )}
        </div>
      </div>
      
      {/* Players summary */}
      <div {...stylex.props(styles.playersSummary)}>
        <div {...stylex.props(styles.playerList)}>
          {playerPlays.map((play, index) => {
            const isWinner = play.playerName === winner;
            const pieceCount = play.pieces.length;
            const useTwoRows = pieceCount > 3;
            const player = play.player;
            const capturedPiles = playerPiles[play.playerName] || player?.captured_piles || 0;
            const declaredPiles = player?.declared || 0;
            
            return (
              <div
                key={play.playerName}
                {...stylex.props(
                  styles.playerRow,
                  isWinner && styles.playerRowWinner
                )}
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                {/* Player info */}
                <div {...stylex.props(styles.playerInfo)}>
                  <div {...stylex.props(styles.playerHeader)}>
                    <PlayerAvatar
                      name={play.playerName}
                      isBot={player?.is_bot}
                      avatarColor={player?.avatar_color}
                      size="small"
                    />
                    <span {...stylex.props(styles.playerName)}>
                      {play.playerName}
                    </span>
                    {isWinner && (
                      <span {...stylex.props(styles.winnerBadge)}>Winner</span>
                    )}
                  </div>
                  <div {...stylex.props(styles.playerStats)}>
                    <div {...stylex.props(styles.statItem)}>
                      <span>📦</span>
                      <span {...stylex.props(getPileStatusStyle(capturedPiles, declaredPiles))}>
                        {capturedPiles}/{declaredPiles}
                      </span>
                    </div>
                    {play.playType && (
                      <span {...stylex.props(styles.playTypeBadge)}>
                        {formatPlayType(play.playType)}
                      </span>
                    )}
                  </div>
                </div>
                
                {/* Played pieces */}
                <div {...stylex.props(
                  styles.playedPieces,
                  useTwoRows && styles.playedPiecesTwoRows
                )}>
                  {pieceCount === 0 ? (
                    <span {...stylex.props(styles.passIndicator)}>Passed</span>
                  ) : useTwoRows ? (
                    // Two rows for >3 pieces
                    <>
                      <div {...stylex.props(styles.piecesRow)}>
                        {play.pieces
                          .slice(0, Math.ceil(pieceCount / 2))
                          .map((piece, idx) => {
                            const pieceId = `${play.playerName}-${idx}`;
                            const isFlipped = flippedPieces.has(pieceId);
                            const isInvalidPlay = !isFlipped && flippedPieces.size > 0;
                            const animationDelay = calculateRevealDelay(
                              play.playerName,
                              players
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
                                  variant="table"
                                  flipped={isFlipped}
                                  animationDelay={isFlipped ? animationDelay : undefined}
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
                            const isInvalidPlay = !isFlipped && flippedPieces.size > 0;
                            const animationDelay = calculateRevealDelay(
                              play.playerName,
                              players
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
                                  variant="table"
                                  flipped={isFlipped}
                                  animationDelay={isFlipped ? animationDelay : undefined}
                                />
                              </div>
                            );
                          })}
                      </div>
                    </>
                  ) : (
                    // Single row for ≤3 pieces
                    play.pieces.map((piece, idx) => {
                      const pieceId = `${play.playerName}-${idx}`;
                      const isFlipped = flippedPieces.has(pieceId);
                      const isInvalidPlay = !isFlipped && flippedPieces.size > 0;
                      const animationDelay = calculateRevealDelay(
                        play.playerName,
                        players
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
                            variant="table"
                            flipped={isFlipped}
                            animationDelay={isFlipped ? animationDelay : undefined}
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
      
      {/* Summary bar */}
      <div {...stylex.props(styles.summaryBar)}>
        <div {...stylex.props(styles.summaryItem)}>
          <span {...stylex.props(styles.summaryLabel)}>Round</span>
          <span {...stylex.props(styles.summaryValue)}>{roundNumber}</span>
        </div>
        <div {...stylex.props(styles.summaryItem)}>
          <span {...stylex.props(styles.summaryLabel)}>Turn</span>
          <span {...stylex.props(styles.summaryValue)}>{turnNumber}</span>
        </div>
        <div {...stylex.props(styles.summaryItem)}>
          <span {...stylex.props(styles.summaryLabel)}>Plays</span>
          <span {...stylex.props(styles.summaryValue)}>{totalPlays}</span>
        </div>
        <div {...stylex.props(styles.summaryItem)}>
          <span {...stylex.props(styles.summaryLabel)}>Passes</span>
          <span {...stylex.props(styles.summaryValue)}>{totalPasses}</span>
        </div>
      </div>
      
      {/* Next turn info */}
      <div {...stylex.props(styles.nextTurnInfo)}>
        <div {...stylex.props(styles.nextStarter)}>{nextPhase.starter}</div>
        <div {...stylex.props(styles.autoContinue)}>
          <FooterTimer
            prefix={nextPhase.continue}
            onComplete={onContinue}
            variant="inline"
          />
        </div>
      </div>
    </div>
  );
}

TurnResultsUI.propTypes = {
  // Data props
  winner: PropTypes.string,
  winningPlay: PropTypes.shape({
    pieces: PropTypes.array,
    value: PropTypes.number,
    type: PropTypes.string,
    pilesWon: PropTypes.number,
    starter: PropTypes.string,
  }),
  playerPiles: PropTypes.object,
  players: PropTypes.array,
  turnNumber: PropTypes.number,
  roundNumber: PropTypes.number,
  nextStarter: PropTypes.string,
  playerName: PropTypes.string,
  isLastTurn: PropTypes.bool,
  currentTurnPlays: PropTypes.array,
  
  // Actions
  onContinue: PropTypes.func,
  
  // Additional props
  className: PropTypes.string,
};

export default TurnResultsUI;