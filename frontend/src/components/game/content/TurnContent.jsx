import React, { useState, useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
import { formatPlayType } from '../../../utils/playTypeFormatter';
import { getPlayType } from '../../../utils/gameValidation';
import {
  determinePiecesToReveal,
  calculateRevealDelay,
} from '../../../utils/playTypeMatching';
import { PlayerAvatar, GamePiece, PieceTray } from '../shared';

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
  currentPlayer = '',
  myName = '',
  currentPile = [],
  requiredPieceCount = 0,
  turnNumber = 1,
  playerPieces = {}, // { playerName: pieces[] }
  lastWinner = '',
  playType = '', // e.g., "Pair", "Straight", "Five of a Kind"
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
      }, 800);

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
    if (requiredPieceCount === 0 || requiredPieceCount === null) {
      return selectedPieces.length > 0;
    }
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

  // Get color class based on pile count vs declaration
  const getPileColorClass = (captured, declared) => {
    if (captured === 0 && declared === 0) return 'pile-status-none';
    if (captured === declared && declared > 0) return 'pile-status-perfect';
    if (captured > declared) return 'pile-status-over';
    return 'pile-status-under';
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
      text: `Must play exactly ${requiredPieceCount} piece${requiredPieceCount > 1 ? 's' : ''}`,
    };
  };

  const requirement = getTurnRequirement();

  return (
    <>
      {/* Turn indicator */}
      <div
        className={`turn-indicator ${getPileColorClass(getPlayerStats(myName).pilesWon, getPlayerStats(myName).declared)}`}
      >
        {getPlayerStats(myName).pilesWon}/{getPlayerStats(myName).declared}
      </div>

      {/* Table section */}
      <div className="turn-table-section">
        <div className="turn-table-layout">
          {/* Central table */}
          <div className="turn-central-table">
            {/* Player pieces areas around table */}
            {players.map((player) => {
              const position = getRelativePosition(player.name);
              const pieces = playerPieces[player.name] || [];
              const hasPlayed = pieces.length > 0;

              return (
                hasPlayed && (
                  <div
                    key={player.name}
                    className={`turn-player-pieces-area ${position} ${pieces.length <= 3 ? 'single-line' : ''}`}
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
                          className={isInvalidPlay ? 'invalid-play' : ''}
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

            return (
              <div
                key={player.name}
                className={`turn-player-summary-bar ${position} ${isActive ? 'active' : ''} ${hasPlayed ? 'played' : ''} ${isCurrentUser ? 'current-user' : ''}`}
              >
                <div className="turn-player-summary-content">
                  <PlayerAvatar
                    name={player.name}
                    className="turn-player-avatar-small"
                    size="small"
                  />
                  <span className="turn-player-name-short">{player.name}</span>
                  <div className="turn-player-stats-compact">
                    <span
                      className={`turn-stat-number ${getPileColorClass(stats.pilesWon, stats.declared)}`}
                    >
                      {stats.pilesWon}
                    </span>
                    <span className="turn-stat-separator">/</span>
                    <span className="turn-stat-number">{stats.declared}</span>
                  </div>
                </div>
                {/* Status icons showing pieces in hand */}
                <div className="turn-status-icons">
                  {[...Array(Math.min(piecesInHand, 8))].map((_, i) => (
                    <span key={i} className="turn-status-icon"></span>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Confirm Selection Panel - Sliding Tray */}
      <div className={`turn-confirm-panel ${showConfirmPanel ? 'show' : ''}`}>
        <div className="turn-selection-info">
          <div className="turn-selection-count">
            {(() => {
              const isStarter =
                requiredPieceCount === 0 || requiredPieceCount === null;

              // Starter logic
              if (isStarter) {
                if (selectedPieces.length >= 2) {
                  const playType = getPlayType(selectedPieces);
                  return playType
                    ? `✓ Valid ${formatPlayType(playType)}`
                    : 'As starter, your play must be valid';
                }

                return 'As starter, your play must be valid';
              }

              // Follower logic
              const defaultText = `Must play exactly ${requiredPieceCount} piece${requiredPieceCount > 1 ? 's' : ''}`;

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

        <div className="turn-action-buttons">
          <button className="turn-action-button" onClick={handlePlay}>
            Play Pieces
          </button>
          <button
            className="turn-action-button secondary"
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
