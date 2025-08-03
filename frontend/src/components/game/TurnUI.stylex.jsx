/**
 * 🎲 **TurnUI Component** - Turn Phase Interface with StyleX
 *
 * Features:
 * ✅ Circular table layout with animations
 * ✅ Player pieces and stats display
 * ✅ Current pile with flip animations
 * ✅ Play/Pass actions with validation
 * ✅ StyleX for optimized styling
 */

import React, { useState, useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
import { formatPlayType } from '../../utils/playTypeFormatter';
import { getPlayType } from '../../utils/gameValidation';
import {
  determinePiecesToReveal,
  calculateRevealDelay,
} from '../../utils/playTypeMatching';
import PlayerAvatar from './shared/PlayerAvatar.stylex';
import GamePiece from './shared/GamePiece.stylex';
import PieceTray from './shared/PieceTray.stylex';
import Button from '../Button.stylex';
import { TIMING } from '../../constants';
import { colors, spacing, shadows, layout, motion, typography } from '../../design-system/tokens.stylex';

// Animation keyframes
const fadeIn = stylex.keyframes({
  '0%': {
    opacity: 0,
  },
  '100%': {
    opacity: 1,
  },
});

const slideUp = stylex.keyframes({
  '0%': {
    transform: 'translateY(100%)',
    opacity: 0,
  },
  '100%': {
    transform: 'translateY(0)',
    opacity: 1,
  },
});

const rotate = stylex.keyframes({
  '0%': {
    transform: 'rotate(0deg)',
  },
  '100%': {
    transform: 'rotate(360deg)',
  },
});

const pulse = stylex.keyframes({
  '0%, 100%': {
    transform: 'scale(1)',
  },
  '50%': {
    transform: 'scale(1.05)',
  },
});

const styles = stylex.create({
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    position: 'relative',
    backgroundColor: colors.background,
  },
  
  // Table area
  tableArea: {
    flex: 1,
    position: 'relative',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.xl,
    minHeight: '400px',
  },
  
  // Circular table
  table: {
    position: 'relative',
    width: '400px',
    height: '400px',
    backgroundColor: colors.surface,
    borderRadius: layout.radiusFull,
    boxShadow: shadows.xl,
    backgroundImage: `radial-gradient(circle, ${colors.surface} 0%, ${colors.surfaceHover} 100%)`,
    animation: `${fadeIn} ${motion.durationNormal} ${motion.easeOut}`,
    
    '@media (max-width: 640px)': {
      width: '300px',
      height: '300px',
    },
  },
  
  // Center pile area
  centerPile: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: spacing.sm,
  },
  
  pileContainer: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: spacing.xs,
    maxWidth: '200px',
    justifyContent: 'center',
    padding: spacing.md,
    backgroundColor: 'rgba(255, 255, 255, 0.5)',
    borderRadius: layout.radiusMd,
    minHeight: '80px',
  },
  
  playTypeLabel: {
    fontSize: typography.textSm,
    fontWeight: typography.weightBold,
    color: colors.primary,
    textTransform: 'uppercase',
    padding: `${spacing.xs} ${spacing.sm}`,
    backgroundColor: colors.surface,
    borderRadius: layout.radiusFull,
    boxShadow: shadows.sm,
  },
  
  // Player positions
  playerSlot: {
    position: 'absolute',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: spacing.sm,
    transition: motion.transitionBase,
  },
  
  playerBottom: {
    bottom: '-60px',
    left: '50%',
    transform: 'translateX(-50%)',
  },
  
  playerTop: {
    top: '-60px',
    left: '50%',
    transform: 'translateX(-50%)',
  },
  
  playerLeft: {
    left: '-60px',
    top: '50%',
    transform: 'translateY(-50%)',
  },
  
  playerRight: {
    right: '-60px',
    top: '50%',
    transform: 'translateY(-50%)',
  },
  
  // Player info
  playerInfo: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: spacing.xs,
    padding: spacing.sm,
    backgroundColor: colors.surface,
    borderRadius: layout.radiusMd,
    boxShadow: shadows.sm,
    minWidth: '100px',
  },
  
  playerInfoActive: {
    backgroundColor: colors.primary,
    color: colors.textLight,
    animation: `${pulse} 2s ${motion.easeInOut} infinite`,
  },
  
  playerName: {
    fontSize: typography.textSm,
    fontWeight: typography.weightMedium,
  },
  
  playerStats: {
    display: 'flex',
    gap: spacing.md,
    fontSize: typography.textXs,
  },
  
  statItem: {
    display: 'flex',
    gap: spacing.xs,
    alignItems: 'center',
  },
  
  statValue: {
    fontWeight: typography.weightBold,
  },
  
  // Player pieces area
  playerPiecesArea: {
    position: 'absolute',
    display: 'flex',
    gap: spacing.xs,
    flexWrap: 'wrap',
    maxWidth: '120px',
    justifyContent: 'center',
  },
  
  playerPiecesBottom: {
    bottom: '20px',
    left: '50%',
    transform: 'translateX(-50%)',
  },
  
  playerPiecesTop: {
    top: '20px',
    left: '50%',
    transform: 'translateX(-50%)',
  },
  
  playerPiecesLeft: {
    left: '20px',
    top: '50%',
    transform: 'translateY(-50%)',
  },
  
  playerPiecesRight: {
    right: '20px',
    top: '50%',
    transform: 'translateY(-50%)',
  },
  
  // Summary bar
  summaryBar: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: spacing.md,
    backgroundColor: colors.surface,
    borderTop: `1px solid ${colors.border}`,
    boxShadow: shadows.sm,
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
    fontSize: typography.textLg,
    fontWeight: typography.weightBold,
    color: colors.primary,
  },
  
  // Status colors
  pileStatusNone: {
    color: colors.gray500,
  },
  
  pileStatusPerfect: {
    color: colors.success,
  },
  
  pileStatusOver: {
    color: colors.warning,
  },
  
  pileStatusUnder: {
    color: colors.danger,
  },
  
  // Hand section
  handSection: {
    borderTop: `1px solid ${colors.border}`,
    backgroundColor: colors.background,
    padding: spacing.lg,
  },
  
  // Confirm panel
  confirmPanel: {
    position: 'fixed',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: colors.surface,
    boxShadow: shadows.xl,
    padding: spacing.lg,
    transform: 'translateY(100%)',
    transition: `transform ${motion.durationFast} ${motion.easeOut}`,
    zIndex: layout.zDropdown,
  },
  
  confirmPanelShow: {
    transform: 'translateY(0)',
    animation: `${slideUp} ${motion.durationFast} ${motion.easeOut}`,
  },
  
  confirmContent: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    maxWidth: '600px',
    margin: '0 auto',
  },
  
  selectedInfo: {
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.xs,
  },
  
  selectedCount: {
    fontSize: typography.textLg,
    fontWeight: typography.weightBold,
    color: colors.textDark,
  },
  
  selectedPlayType: {
    fontSize: typography.textSm,
    color: colors.gray600,
  },
  
  confirmActions: {
    display: 'flex',
    gap: spacing.md,
  },
  
  // Turn indicator
  turnIndicator: {
    position: 'absolute',
    top: spacing.md,
    left: spacing.md,
    backgroundColor: colors.primary,
    color: colors.textLight,
    padding: `${spacing.sm} ${spacing.md}`,
    borderRadius: layout.radiusFull,
    fontSize: typography.textSm,
    fontWeight: typography.weightBold,
    boxShadow: shadows.md,
  },
  
  // Pass button for non-starters
  passButton: {
    position: 'absolute',
    bottom: spacing.xl,
    right: spacing.xl,
    zIndex: layout.zDropdown,
  },
});

/**
 * TurnUI - Turn phase with integrated content
 */
export function TurnUI({
  // Game state data
  myHand = [],
  players = [],
  currentPlayer = '',
  playerName = '',
  currentPile = [],
  requiredPieceCount = 0,
  turnNumber = 1,
  piecesWonCount = {},
  previousWinner = '',
  currentTurnPlays = [],
  playType = '',
  declarationData = {},
  playerHandSizes = {},
  
  // State flags
  canPlayAnyCount = false,
  
  // Action props
  onPlayPieces,
  onPass,
  
  // Additional props
  className = '',
}) {
  const [selectedPieces, setSelectedPieces] = useState([]);
  const [showConfirmPanel, setShowConfirmPanel] = useState(false);
  const [flippedPieces, setFlippedPieces] = useState(new Set());
  const hasFlippedThisTurn = useRef(false);
  
  // Check if it's my turn
  const isMyTurn = currentPlayer === playerName;
  
  // Get my player index
  const myIndex = players.findIndex((p) => p.name === playerName);
  
  // Build player pieces from turn plays
  const playerPieces = {};
  currentTurnPlays.forEach((play) => {
    if (play.player && (play.pieces || play.cards)) {
      playerPieces[play.player] = play.pieces || play.cards;
    }
  });
  
  // Extract play type
  const currentPlayType = playType || (() => {
    const validPlays = currentTurnPlays.filter(play => play.isValid !== false);
    if (validPlays.length > 0) {
      const lastPlay = validPlays[validPlays.length - 1];
      return lastPlay.playType || lastPlay.play_type || '';
    }
    return '';
  })();
  
  // Build player stats
  const playerStats = {};
  players.forEach((player) => {
    playerStats[player.name] = {
      pilesWon: piecesWonCount[player.name] || 0,
      declared: declarationData[player.name] || 0,
    };
  });
  
  // Use current pile or derive from plays
  const pile = currentPile.length > 0
    ? currentPile
    : currentTurnPlays.reduce(
        (acc, play) => [...acc, ...(play.pieces || play.cards || [])],
        []
      );
  
  // Determine required count
  const required = canPlayAnyCount ? 0 : requiredPieceCount;
  
  // Get player position relative to me
  const getRelativePosition = (playerName) => {
    const playerIndex = players.findIndex((p) => p.name === playerName);
    if (playerIndex === -1) return 'bottom';
    
    const relativeIndex = (playerIndex - myIndex + 4) % 4;
    const positions = ['bottom', 'right', 'top', 'left'];
    return positions[relativeIndex];
  };
  
  // Get position styles
  const getPlayerSlotStyle = (position) => {
    const positionMap = {
      'bottom': styles.playerBottom,
      'top': styles.playerTop,
      'left': styles.playerLeft,
      'right': styles.playerRight,
    };
    return positionMap[position] || styles.playerBottom;
  };
  
  const getPlayerPiecesStyle = (position) => {
    const positionMap = {
      'bottom': styles.playerPiecesBottom,
      'top': styles.playerPiecesTop,
      'left': styles.playerPiecesLeft,
      'right': styles.playerPiecesRight,
    };
    return positionMap[position] || styles.playerPiecesBottom;
  };
  
  // Update confirm panel visibility
  useEffect(() => {
    setShowConfirmPanel(selectedPieces.length > 0 && isMyTurn);
  }, [selectedPieces, isMyTurn]);
  
  // Handle piece selection
  const handlePieceSelect = (piece, index) => {
    if (!isMyTurn) return;
    
    const pieceId = `${index}-${piece.kind}-${piece.color}`;
    
    setSelectedPieces((prev) => {
      if (prev.some((p) => p.id === pieceId)) {
        return prev.filter((p) => p.id !== pieceId);
      }
      
      const originalIndex = piece.originalIndex !== undefined ? piece.originalIndex : index;
      const newPiece = {
        ...piece,
        id: pieceId,
        index: originalIndex,
        displayIndex: index,
      };
      
      if (required > 0 && prev.length >= required) {
        return [newPiece];
      }
      
      if (required === 0 && prev.length >= 6) {
        return prev;
      }
      
      return [...prev, newPiece];
    });
  };
  
  // Clear selection
  const clearSelection = () => {
    setSelectedPieces([]);
  };
  
  // Check if can play
  const canPlay = () => {
    if (!isMyTurn) return false;
    
    const isStarter = required === 0 || required === null;
    
    if (isStarter) {
      if (selectedPieces.length === 0) return false;
      if (selectedPieces.length === 1) return true;
      return getPlayType(selectedPieces) !== null;
    }
    
    return selectedPieces.length === required;
  };
  
  // Handle play
  const handlePlay = () => {
    if (canPlay() && onPlayPieces) {
      const pieceIndices = selectedPieces.map((p) => p.index);
      onPlayPieces(pieceIndices);
      setSelectedPieces([]);
    }
  };
  
  // Handle pass
  const handlePass = () => {
    if (isMyTurn && onPass) {
      onPass();
      setSelectedPieces([]);
    }
  };
  
  // Get player stats with defaults
  const getPlayerStats = (playerName) => {
    return playerStats[playerName] || { pilesWon: 0, declared: 0 };
  };
  
  // Get pile status color
  const getPileColorStyle = (captured, declared) => {
    if (captured === 0 && declared === 0) return styles.pileStatusNone;
    if (captured === declared && declared > 0) return styles.pileStatusPerfect;
    if (captured > declared) return styles.pileStatusOver;
    return styles.pileStatusUnder;
  };
  
  return (
    <div {...stylex.props(styles.container, className && { className })}>
      {/* Turn indicator */}
      <div {...stylex.props(styles.turnIndicator)}>
        Turn {turnNumber}
      </div>
      
      {/* Table area */}
      <div {...stylex.props(styles.tableArea)}>
        <div {...stylex.props(styles.table)}>
          {/* Center pile */}
          <div {...stylex.props(styles.centerPile)}>
            {currentPlayType && (
              <div {...stylex.props(styles.playTypeLabel)}>
                {formatPlayType(currentPlayType)}
              </div>
            )}
            <div {...stylex.props(styles.pileContainer)}>
              {pile.map((piece, index) => (
                <GamePiece
                  key={`pile-${index}`}
                  piece={piece}
                  size="small"
                  variant="table"
                  flipped={flippedPieces.has(`${piece.player}-${index}`)}
                />
              ))}
            </div>
          </div>
          
          {/* Player slots */}
          {players.map((player) => {
            const position = getRelativePosition(player.name);
            const stats = getPlayerStats(player.name);
            const isActive = currentPlayer === player.name;
            const pieces = playerPieces[player.name] || [];
            
            return (
              <div key={player.name}>
                {/* Player info */}
                <div {...stylex.props(
                  styles.playerSlot,
                  getPlayerSlotStyle(position)
                )}>
                  <div {...stylex.props(
                    styles.playerInfo,
                    isActive && styles.playerInfoActive
                  )}>
                    <PlayerAvatar
                      name={player.name}
                      isBot={player.is_bot}
                      avatarColor={player.avatar_color}
                      size="medium"
                      isThinking={isActive && player.is_bot}
                    />
                    <div {...stylex.props(styles.playerName)}>
                      {player.name}
                    </div>
                    <div {...stylex.props(styles.playerStats)}>
                      <div {...stylex.props(styles.statItem)}>
                        <span>📦</span>
                        <span {...stylex.props(
                          styles.statValue,
                          getPileColorStyle(stats.pilesWon, stats.declared)
                        )}>
                          {stats.pilesWon}/{stats.declared}
                        </span>
                      </div>
                      <div {...stylex.props(styles.statItem)}>
                        <span>🃏</span>
                        <span {...stylex.props(styles.statValue)}>
                          {playerHandSizes[player.name] || 0}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* Player pieces */}
                {pieces.length > 0 && (
                  <div {...stylex.props(
                    styles.playerPiecesArea,
                    getPlayerPiecesStyle(position)
                  )}>
                    {pieces.map((piece, idx) => (
                      <GamePiece
                        key={`${player.name}-piece-${idx}`}
                        piece={piece}
                        size="mini"
                        variant="table"
                        flipped={flippedPieces.has(`${player.name}-${idx}`)}
                      />
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
        
        {/* Pass button for non-starters */}
        {isMyTurn && required > 0 && (
          <div {...stylex.props(styles.passButton)}>
            <Button
              onClick={handlePass}
              variant="secondary"
              size="large"
            >
              Pass
            </Button>
          </div>
        )}
      </div>
      
      {/* Summary bar */}
      <div {...stylex.props(styles.summaryBar)}>
        <div {...stylex.props(styles.summaryItem)}>
          <span {...stylex.props(styles.summaryLabel)}>Round</span>
          <span {...stylex.props(styles.summaryValue)}>{turnNumber}</span>
        </div>
        <div {...stylex.props(styles.summaryItem)}>
          <span {...stylex.props(styles.summaryLabel)}>Current Player</span>
          <span {...stylex.props(styles.summaryValue)}>{currentPlayer}</span>
        </div>
        <div {...stylex.props(styles.summaryItem)}>
          <span {...stylex.props(styles.summaryLabel)}>Last Winner</span>
          <span {...stylex.props(styles.summaryValue)}>{previousWinner || '—'}</span>
        </div>
      </div>
      
      {/* Hand section */}
      <div {...stylex.props(styles.handSection)}>
        <PieceTray
          pieces={myHand}
          variant={isMyTurn ? 'active' : 'default'}
          onPieceClick={isMyTurn ? handlePieceSelect : null}
          selectedPieces={selectedPieces}
          showValues={true}
          label="Your Hand"
        />
      </div>
      
      {/* Confirm panel */}
      <div {...stylex.props(
        styles.confirmPanel,
        showConfirmPanel && styles.confirmPanelShow
      )}>
        <div {...stylex.props(styles.confirmContent)}>
          <div {...stylex.props(styles.selectedInfo)}>
            <div {...stylex.props(styles.selectedCount)}>
              {selectedPieces.length} piece{selectedPieces.length !== 1 ? 's' : ''} selected
            </div>
            {selectedPieces.length > 1 && (
              <div {...stylex.props(styles.selectedPlayType)}>
                Play type: {formatPlayType(getPlayType(selectedPieces) || 'Invalid')}
              </div>
            )}
          </div>
          <div {...stylex.props(styles.confirmActions)}>
            <Button
              onClick={handlePlay}
              variant="primary"
              disabled={!canPlay()}
            >
              Play
            </Button>
            <Button
              onClick={clearSelection}
              variant="secondary"
            >
              Clear
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

TurnUI.propTypes = {
  // Game state
  myHand: PropTypes.array,
  players: PropTypes.array,
  currentPlayer: PropTypes.string,
  playerName: PropTypes.string,
  currentPile: PropTypes.array,
  requiredPieceCount: PropTypes.number,
  turnNumber: PropTypes.number,
  piecesWonCount: PropTypes.object,
  previousWinner: PropTypes.string,
  currentTurnPlays: PropTypes.array,
  playType: PropTypes.string,
  declarationData: PropTypes.object,
  playerHandSizes: PropTypes.object,
  
  // State flags
  canPlayAnyCount: PropTypes.bool,
  
  // Action props
  onPlayPieces: PropTypes.func,
  onPass: PropTypes.func,
  
  // Additional props
  className: PropTypes.string,
};

export default TurnUI;