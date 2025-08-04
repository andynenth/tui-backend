import React, { useState, useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, motion, layout, shadows, gradients } from '../../../design-system/tokens.stylex';
import { formatPlayType } from '../../../utils/playTypeFormatter';
import { getPlayType } from '../../../utils/gameValidation';
import {
  determinePiecesToReveal,
  calculateRevealDelay,
} from '../../../utils/playTypeMatching';
import { PlayerAvatar, GamePiece, PieceTray } from '../shared';
import { TIMING } from '../../../constants';

// Animations
const slideUp = stylex.keyframes({
  '0%': {
    transform: 'translateY(100%)',
  },
  '100%': {
    transform: 'translateY(0)',
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

// TurnContent styles
const styles = stylex.create({
  turnIndicator: {
    position: 'absolute',
    top: '1rem',
    right: '1rem',
    padding: `'0.25rem' '0.5rem'`,
    borderRadius: '9999px',
    fontSize: '0.875rem',
    fontWeight: '700',
    backgroundColor: '#ffffff',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    zIndex: 10,
  },
  
  pileStatusNone: {
    color: '#6c757d',
    borderColor: '#dee2e6',
  },
  
  pileStatusPerfect: {
    color: '#198754',
    borderColor: '#198754',
    backgroundColor: 'rgba(16, 185, 129, 0.1)',
  },
  
  pileStatusOver: {
    color: '#ffc107',
    borderColor: '#ffc107',
    backgroundColor: 'rgba(245, 158, 11, 0.1)',
  },
  
  pileStatusUnder: {
    color: '#dc3545',
    borderColor: '#dc3545',
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
  },
  
  tableSection: {
    flex: 1,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '1.5rem',
    position: 'relative',
  },
  
  tableLayout: {
    position: 'relative',
    width: '100%',
    maxWidth: '400px',
    aspectRatio: '1',
  },
  
  centralTable: {
    position: 'absolute',
    top: '25%',
    left: '25%',
    right: '25%',
    bottom: '25%',
    backgroundColor: '#8B4513',
    borderRadius: '0.5rem',
    boxShadow: `'0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)', inset 0 2px 4px rgba(0,0,0,0.2)`,
    overflow: 'hidden',
  },
  
  woodGrain: {
    position: 'absolute',
    inset: 0,
    opacity: 0.3,
    background: 'repeating-linear-gradient(90deg, #6B3410 0px, #8B4513 3px, #6B3410 6px)',
  },
  
  playerPiecesArea: {
    position: 'absolute',
    display: 'flex',
    flexWrap: 'wrap',
    gap: '0.25rem',
    padding: '0.5rem',
    alignItems: 'center',
    justifyContent: 'center',
  },
  
  piecesAreaTop: {
    top: '10%',
    left: '30%',
    right: '30%',
  },
  
  piecesAreaBottom: {
    bottom: '10%',
    left: '30%',
    right: '30%',
  },
  
  piecesAreaLeft: {
    left: '10%',
    top: '30%',
    bottom: '30%',
    flexDirection: 'column',
  },
  
  piecesAreaRight: {
    right: '10%',
    top: '30%',
    bottom: '30%',
    flexDirection: 'column',
  },
  
  singleLine: {
    flexWrap: 'nowrap',
  },
  
  playerSummaryBar: {
    position: 'absolute',
    backgroundColor: '#ffffff',
    borderRadius: '0.375rem',
    padding: '0.5rem',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    transition: `all '300ms' 'cubic-bezier(0.4, 0, 0.2, 1)'`,
  },
  
  summaryBarTop: {
    top: 0,
    left: '50%',
    transform: 'translateX(-50%)',
  },
  
  summaryBarLeft: {
    left: 0,
    top: '50%',
    transform: 'translateY(-50%)',
    flexDirection: 'column',
  },
  
  summaryBarRight: {
    right: 0,
    top: '50%',
    transform: 'translateY(-50%)',
    flexDirection: 'column',
  },
  
  summaryBarActive: {
    backgroundColor: '#e7f1ff',
    borderColor: '#0d6efd',
    animation: `${pulse} 2s 'cubic-bezier(0.4, 0, 0.2, 1)' infinite`,
  },
  
  summaryBarPlayed: {
    opacity: 0.7,
  },
  
  summaryContent: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.25rem',
  },
  
  playerNameShort: {
    fontSize: '0.875rem',
    fontWeight: '500',
    color: '#495057',
  },
  
  playerStatsCompact: {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.xxs,
    fontSize: '0.875rem',
  },
  
  statNumber: {
    fontWeight: '700',
  },
  
  statSeparator: {
    color: '#ced4da',
  },
  
  statusIcons: {
    display: 'flex',
    gap: '2px',
  },
  
  statusIcon: {
    width: '4px',
    height: '12px',
    backgroundColor: '#ced4da',
    borderRadius: layout.radiusXs,
  },
  
  confirmPanel: {
    position: 'fixed',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: '#ffffff',
    borderTopLeftRadius: '1rem',
    borderTopRightRadius: '1rem',
    boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    padding: '1.5rem',
    transform: 'translateY(100%)',
    transition: `transform '300ms' 'cubic-bezier(0, 0, 0.2, 1)'`,
    zIndex: 40,
  },
  
  confirmPanelShow: {
    transform: 'translateY(0)',
    animation: `${slideUp} 0.3s 'cubic-bezier(0, 0, 0.2, 1)'`,
  },
  
  selectionInfo: {
    marginBottom: '1rem',
    textAlign: 'center',
  },
  
  selectionCount: {
    fontSize: '1rem',
    color: '#495057',
    fontWeight: '500',
  },
  
  actionButtons: {
    display: 'flex',
    gap: '1rem',
    justifyContent: 'center',
  },
  
  actionButton: {
    padding: `'0.5rem' '2rem'`,
    borderRadius: '0.375rem',
    fontSize: '1rem',
    fontWeight: '500',
    border: 'none',
    cursor: 'pointer',
    transition: `all '300ms' 'cubic-bezier(0.4, 0, 0.2, 1)'`,
  },
  
  primaryButton: {
    background: gradients.primary,
    color: '#ffffff',
    
    ':hover': {
      transform: 'translateY(-2px)',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    },
    
    ':disabled': {
      opacity: 0.5,
      cursor: 'not-allowed',
      transform: 'none',
    },
  },
  
  secondaryButton: {
    backgroundColor: '#e9ecef',
    color: '#495057',
    
    ':hover': {
      backgroundColor: '#dee2e6',
    },
  },
  
  invalidPlay: {
    opacity: 0.5,
    filter: 'grayscale(1)',
  },
});

/**
 * TurnContent Component
 *
 * Displays the turn phase with:
 * - Circular table layout with player positions
 * - Player summary bars with stats
 * - Current pile in center with flip animations
 * - Player pieces around table
 * - Sliding confirm panel
 * - Play/Pass actions
 */
const TurnContent = ({
  myHand = [],
  players = [],
  currentPlayer = ',
  myName = ',
  currentPile = [],
  requiredPieceCount = 0,
  turnNumber = 1,
  playerPieces = {}, // { playerName: pieces[] }
  lastWinner = ',
  playType = ', // e.g., "Pair", "Straight", "Five of a Kind"
  playerStats = {}, // { playerName: { pilesWon: 0, declared: 0 } }
  playerHandSizes = {}, // { playerName: handSize }
  onPlayPieces,
  onPass,
}) => {
  const [selectedPieces, setSelectedPieces] = useState([]);
  const [showConfirmPanel, setShowConfirmPanel] = useState(false);
  const [flippedPieces, setFlippedPieces] = useState(new Set());
  const hasFlippedThisTurn = useRef(false);

  // Check if it's my turn
  const isMyTurn = currentPlayer === myName;

  // Get my player index
  const myIndex = players.findIndex((p) => p.name === myName);

  // Get player position relative to me (always at bottom)
  const getRelativePosition = (playerName) => {
    const playerIndex = players.findIndex((p) => p.name === playerName);
    if (playerIndex === -1) return 'bottom';

    // Calculate relative position with me always at bottom
    const relativeIndex = (playerIndex - myIndex + 4) % 4;
    const positions = ['bottom', 'right', 'top', 'left'];
    return positions[relativeIndex];
  };

  // Update confirm panel visibility when pieces are selected
  useEffect(() => {
    setShowConfirmPanel(selectedPieces.length > 0 && isMyTurn);
  }, [selectedPieces, isMyTurn]);

  // Last-player detection and selective flip animation
  useEffect(() => {
    // Count how many players have played
    const playedCount = Object.keys(playerPieces).filter(
      (player) => playerPieces[player]?.length > 0
    ).length;

    // Check if this is the final play
    const isLastPlay =
      playedCount === players.length && !hasFlippedThisTurn.current;

    if (isLastPlay) {
      hasFlippedThisTurn.current = true;

      // Start flip timer after last player plays
      const timer = setTimeout(() => {
        console.log('[TurnContent] Determining pieces to reveal:', {
          playType,
          lastWinner,
          playerPieces,
        });

        // Determine which pieces to reveal based on play type matching
        const piecesToReveal = determinePiecesToReveal(
          playerPieces,
          playType,
          lastWinner // The starter is the last winner
        );

        console.log('[TurnContent] Pieces to reveal:', piecesToReveal);
        setFlippedPieces(piecesToReveal);
      }, TIMING.TURN_FLIP_DELAY);

      return () => clearTimeout(timer);
    }
  }, [playerPieces, players.length, playType, lastWinner]);

  // Reset flip state when turn changes
  useEffect(() => {
    hasFlippedThisTurn.current = false;
    setFlippedPieces(new Set());
  }, [turnNumber]);

  // Handle piece selection
  const handlePieceSelect = (piece, index) => {
    if (!isMyTurn) return;

    const pieceId = `${index}-${piece.kind}-${piece.color}`;

    setSelectedPieces((prev) => {
      // Check if already selected (toggle off)
      if (prev.some((p) => p.id === pieceId)) {
        return prev.filter((p) => p.id !== pieceId);
      }

      // New selection
      // IMPORTANT: Use piece.originalIndex if available (for sorted hands)
      const originalIndex =
        piece.originalIndex !== undefined ? piece.originalIndex : index;
      const newPiece = {
        ...piece,
        id: pieceId,
        index: originalIndex,
        displayIndex: index,
      };

      // If required count is set and we're at the limit
      if (requiredPieceCount > 0 && prev.length >= requiredPieceCount) {
        // Replace selection with just the new piece
        return [newPiece];
      }

      // If first player (no required count), limit to 6 pieces
      if (requiredPieceCount === 0 && prev.length >= 6) {
        // Don't allow more than 6
        return prev;
      }

      // Add to selection
      return [...prev, newPiece];
    });
  };

  // Clear selection
  const clearSelection = () => {
    setSelectedPieces([]);
  };

  // Check if can play
  const canPlay = () => {
    if (!isMyTurn) {
      return false;
    }

    const isStarter = requiredPieceCount === 0 || requiredPieceCount === null;

    if (isStarter) {
      // For starters, must have at least 1 piece and valid play type
      if (selectedPieces.length === 0) return false;
      if (selectedPieces.length === 1) return true; // Single piece is always valid
      return getPlayType(selectedPieces) !== null; // Multi-piece must be valid
    }

    // For followers, must match exact count
    return selectedPieces.length === requiredPieceCount;
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

  // Get color style based on pile count vs declaration
  const getPileColorStyle = (captured, declared) => {
    if (captured === 0 && declared === 0) return styles.pileStatusNone;
    if (captured === declared && declared > 0) return styles.pileStatusPerfect;
    if (captured > declared) return styles.pileStatusOver;
    return styles.pileStatusUnder;
  };

  // Get position style
  const getPositionStyle = (position) => {
    switch (position) {
      case 'top':
        return styles.piecesAreaTop;
      case 'bottom':
        return styles.piecesAreaBottom;
      case 'left':
        return styles.piecesAreaLeft;
      case 'right':
        return styles.piecesAreaRight;
      default:
        return styles.piecesAreaBottom;
    }
  };

  // Get summary bar position style
  const getSummaryBarStyle = (position) => {
    switch (position) {
      case 'top':
        return styles.summaryBarTop;
      case 'left':
        return styles.summaryBarLeft;
      case 'right':
        return styles.summaryBarRight;
      default:
        return null;
    }
  };

  // Get turn requirement message
  const getTurnRequirement = () => {
    if (!isMyTurn) {
      return { type: 'waiting', text: `Waiting for ${currentPlayer} to play` };
    }

    if (requiredPieceCount === 0) {
      return { type: 'active', text: 'Play any number of pieces or pass' };
    }

    return {
      type: 'active',
      text: `Must play exactly ${requiredPieceCount} piece${requiredPieceCount > 1 ? 's' : '}`,
    };
  };

  const requirement = getTurnRequirement();
  const myStats = getPlayerStats(myName);

  return (
    <>
      {/* Turn indicator */}
      <div {...stylex.props(
        styles.turnIndicator,
        getPileColorStyle(myStats.pilesWon, myStats.declared)
      )}>
        {myStats.pilesWon}/{myStats.declared}
      </div>

      {/* Table section */}
      <div {...stylex.props(styles.tableSection)}>
        <div {...stylex.props(styles.tableLayout)}>
          {/* Central table */}
          <div {...stylex.props(styles.centralTable)}>
            {/* Wood grain texture layer */}
            <div {...stylex.props(styles.woodGrain)} />

            {/* Player pieces areas around table */}
            {players.map((player) => {
              const position = getRelativePosition(player.name);
              const pieces = playerPieces[player.name] || [];
              const hasPlayed = pieces.length > 0;

              return (
                hasPlayed && (
                  <div
                    key={player.name}
                    {...stylex.props(
                      styles.playerPiecesArea,
                      getPositionStyle(position),
                      pieces.length <= 3 && styles.singleLine
                    )}
                  >
                    {pieces.map((piece, idx) => {
                      const pieceId = `${player.name}-${idx}`;
                      const isFlipped = flippedPieces.has(pieceId);
                      const isInvalidPlay =
                        !isFlipped && hasFlippedThisTurn.current;
                      const animationDelay =
                        calculateRevealDelay(player.name, players) / 1000; // Convert to seconds

                      return (
                        <GamePiece
                          key={idx}
                          piece={piece}
                          size="mini"
                          variant="table"
                          flippable
                          flipped={isFlipped}
                          className={isInvalidPlay ? 'invalid-play' : '}
                          animationDelay={
                            isFlipped ? animationDelay : undefined
                          }
                        />
                      );
                    })}
                  </div>
                )
              );
            })}
          </div>

          {/* Player summary bars */}
          {players.map((player) => {
            const position = getRelativePosition(player.name);
            const isActive = player.name === currentPlayer;
            const hasPlayed = (playerPieces[player.name] || []).length > 0;
            const stats = getPlayerStats(player.name);
            const piecesInHand = playerHandSizes[player.name] || 0;
            const isCurrentUser = player.name === myName;

            // Skip bottom player (current user)
            if (position === 'bottom') return null;

            const summaryBarPositionStyle = getSummaryBarStyle(position);

            return (
              <div
                key={player.name}
                {...stylex.props(
                  styles.playerSummaryBar,
                  summaryBarPositionStyle,
                  isActive && styles.summaryBarActive,
                  hasPlayed && styles.summaryBarPlayed
                )}
              >
                <div {...stylex.props(styles.summaryContent)}>
                  <PlayerAvatar
                    name={player.name}
                    isBot={player.is_bot}
                    isThinking={isActive && player.is_bot}
                    avatarColor={player.avatar_color}
                    size="mini"
                  />
                  <span {...stylex.props(styles.playerNameShort)}>
                    {player.name}
                  </span>
                  <div {...stylex.props(styles.playerStatsCompact)}>
                    <span {...stylex.props(
                      styles.statNumber,
                      getPileColorStyle(stats.pilesWon, stats.declared)
                    )}>
                      {stats.pilesWon}
                    </span>
                    <span {...stylex.props(styles.statSeparator)}>/</span>
                    <span {...stylex.props(styles.statNumber)}>
                      {stats.declared}
                    </span>
                  </div>
                </div>
                {/* Status icons showing pieces in hand */}
                <div {...stylex.props(styles.statusIcons)}>
                  {[...Array(Math.min(piecesInHand, 8))].map((_, i) => (
                    <span key={i} {...stylex.props(styles.statusIcon)} />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Confirm Selection Panel - Sliding Tray */}
      <div {...stylex.props(
        styles.confirmPanel,
        showConfirmPanel && styles.confirmPanelShow
      )}>
        <div {...stylex.props(styles.selectionInfo)}>
          <div {...stylex.props(styles.selectionCount)}>
            {(() => {
              const isStarter =
                requiredPieceCount === 0 || requiredPieceCount === null;

              // Starter logic
              if (isStarter) {
                if (selectedPieces.length >= 2) {
                  const playType = getPlayType(selectedPieces);
                  return playType
                    ? `✓ Valid ${formatPlayType(playType)}`
                    : "That's not a valid play";
                }

                return 'As starter, your play must be valid';
              }

              // Follower logic
              const defaultText = `Must play exactly ${requiredPieceCount} piece${requiredPieceCount > 1 ? 's' : '}`;

              // Check if exact count is selected
              if (selectedPieces.length === requiredPieceCount) {
                // Single piece - always ready
                if (requiredPieceCount === 1) {
                  return '✓ Ready to play';
                }

                // Multiple pieces - check validity
                const selectedPlayType = getPlayType(selectedPieces);

                if (selectedPlayType) {
                  // Check if the selected play type matches the starter's play type
                  if (selectedPlayType === playType) {
                    return `✓ Your ${formatPlayType(selectedPlayType)} can compete this turn`;
                  } else {
                    return `⚠️ Your ${formatPlayType(selectedPlayType)} cannot compete against ${formatPlayType(playType)}`;
                  }
                } else {
                  // Use the actual play type from the starter if available
                  const starterPlayType = playType || 'combination';
                  return `⚠️ Not a ${formatPlayType(starterPlayType)} - play to forfeit turn`;
                }
              }

              // Default follower text
              return defaultText;
            })()}
          </div>
        </div>

        <div {...stylex.props(styles.actionButtons)}>
          <button
            {...stylex.props(styles.actionButton, styles.primaryButton)}
            onClick={handlePlay}
            disabled={!canPlay()}
          >
            Play Pieces
          </button>
          <button
            {...stylex.props(styles.actionButton, styles.secondaryButton)}
            onClick={clearSelection}
          >
            Clear
          </button>
        </div>
      </div>

      {/* Hand section - always visible at bottom */}
      <PieceTray
        pieces={myHand}
        variant={isMyTurn ? 'active' : 'default'}
        showValues
        onPieceClick={isMyTurn ? handlePieceSelect : null}
        selectedPieces={selectedPieces}
      />
    </>
  );
};

TurnContent.propTypes = {
  myHand: PropTypes.array,
  players: PropTypes.array,
  currentPlayer: PropTypes.string,
  myName: PropTypes.string,
  currentPile: PropTypes.array,
  requiredPieceCount: PropTypes.number,
  turnNumber: PropTypes.number,
  playerPieces: PropTypes.object,
  lastWinner: PropTypes.string,
  playType: PropTypes.string,
  playerStats: PropTypes.object,
  playerHandSizes: PropTypes.object,
  onPlayPieces: PropTypes.func,
  onPass: PropTypes.func,
};

export default TurnContent;