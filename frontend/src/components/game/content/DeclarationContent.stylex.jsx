import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, motion, layout, shadows, gradients } from '../../../design-system/tokens.stylex';
import { PlayerAvatar, PieceTray } from '../shared';

// Animations
const slideInFromBottom = stylex.keyframes({
  '0%': {
    transform: 'translateY(100%)',
    opacity: 0,
  },
  '100%': {
    transform: 'translateY(0)',
    opacity: 1,
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

// DeclarationContent styles
const styles = stylex.create({
  gameStatusSection: {
    padding: spacing.lg,
    overflowY: 'auto',
    flex: 1,
  },
  
  playersList: {
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.md,
  },
  
  playerRow: {
    display: 'flex',
    alignItems: 'center',
    padding: spacing.md,
    borderRadius: layout.radiusLg,
    backgroundColor: colors.white,
    boxShadow: shadows.sm,
    transition: `all ${motion.durationBase} ${motion.easeInOut}`,
  },
  
  playerRowCurrentTurn: {
    backgroundColor: 'rgba(37, 99, 235, 0.05)',
    borderLeft: `4px solid ${colors.primary}`,
    animation: `${pulse} 2s ${motion.easeInOut} infinite`,
  },
  
  playerRowDeclared: {
    opacity: 0.8,
    backgroundColor: colors.gray50,
  },
  
  playerInfo: {
    flex: 1,
    marginLeft: spacing.md,
  },
  
  playerName: {
    fontSize: typography.textBase,
    fontWeight: typography.weightMedium,
    color: colors.gray800,
  },
  
  playerStatus: {
    marginLeft: 'auto',
  },
  
  declaredValue: {
    width: '48px',
    height: '48px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: layout.radiusFull,
    background: gradients.primary,
    color: colors.white,
    fontSize: typography.textXl,
    fontWeight: typography.weightBold,
    boxShadow: shadows.md,
  },
  
  statusBadge: {
    padding: `${spacing.xs} ${spacing.md}`,
    borderRadius: layout.radiusFull,
    fontSize: typography.textSm,
    fontWeight: typography.weightMedium,
    transition: `all ${motion.durationBase} ${motion.easeInOut}`,
  },
  
  statusCurrent: {
    backgroundColor: colors.primary,
    color: colors.white,
  },
  
  statusPending: {
    backgroundColor: colors.warning,
    color: colors.white,
  },
  
  statusWaiting: {
    backgroundColor: colors.gray200,
    color: colors.gray600,
  },
  
  panel: {
    position: 'fixed',
    bottom: '-200px',
    left: 0,
    right: 0,
    backgroundColor: colors.white,
    borderTopLeftRadius: layout.radiusXl,
    borderTopRightRadius: layout.radiusXl,
    boxShadow: shadows.xl,
    padding: spacing.xl,
    transition: `transform ${motion.durationBase} ${motion.easeOut}`,
    zIndex: 40,
  },
  
  panelShow: {
    transform: 'translateY(-200px)',
    animation: `${slideInFromBottom} 0.3s ${motion.easeOut}`,
  },
  
  options: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: spacing.md,
    marginBottom: spacing.lg,
  },
  
  option: {
    aspectRatio: '1',
    borderRadius: layout.radiusLg,
    border: `2px solid ${colors.gray300}`,
    backgroundColor: colors.white,
    fontSize: typography.text2xl,
    fontWeight: typography.weightBold,
    color: colors.gray700,
    cursor: 'pointer',
    transition: `all ${motion.durationBase} ${motion.easeInOut}`,
    
    ':hover': {
      borderColor: colors.primary,
      backgroundColor: colors.primaryLight,
      transform: 'scale(1.05)',
    },
  },
  
  optionSelected: {
    borderColor: colors.primary,
    backgroundColor: colors.primary,
    color: colors.white,
    transform: 'scale(1.1)',
    boxShadow: shadows.md,
  },
  
  optionDisabled: {
    opacity: 0.4,
    cursor: 'not-allowed',
    backgroundColor: colors.gray100,
    
    ':hover': {
      borderColor: colors.gray300,
      backgroundColor: colors.gray100,
      transform: 'scale(1)',
    },
  },
  
  actions: {
    display: 'flex',
    gap: spacing.md,
    justifyContent: 'center',
  },
  
  actionBtn: {
    padding: `${spacing.sm} ${spacing.xl}`,
    borderRadius: layout.radiusMd,
    fontSize: typography.textBase,
    fontWeight: typography.weightMedium,
    border: 'none',
    cursor: 'pointer',
    transition: `all ${motion.durationBase} ${motion.easeInOut}`,
  },
  
  primaryBtn: {
    background: gradients.primary,
    color: colors.white,
    
    ':hover': {
      transform: 'translateY(-2px)',
      boxShadow: shadows.md,
    },
    
    ':disabled': {
      opacity: 0.5,
      cursor: 'not-allowed',
      transform: 'none',
    },
  },
  
  secondaryBtn: {
    backgroundColor: colors.gray200,
    color: colors.gray700,
    
    ':hover': {
      backgroundColor: colors.gray300,
    },
  },
});

/**
 * DeclarationContent Component
 *
 * Displays the declaration phase with:
 * - Players list showing declaration status
 * - Declaration panel with number selection (0-8)
 * - Validation for total sum and consecutive zeros
 * - Player's hand display at bottom
 */
const DeclarationContent = ({
  myHand = [],
  players = [],
  currentPlayer = '',
  myName = '',
  declarations = {},
  totalDeclared = 0,
  consecutiveZeros = 0,
  redealMultiplier = 1,
  onDeclare,
}) => {
  const [selectedValue, setSelectedValue] = useState(null);
  const [showPanel, setShowPanel] = useState(false);

  // Check if it's my turn
  const isMyTurn = currentPlayer === myName;

  // Show panel when it's my turn
  useEffect(() => {
    if (isMyTurn) {
      setShowPanel(true);
    } else {
      setShowPanel(false);
      setSelectedValue(null);
    }
  }, [isMyTurn]);

  // Calculate restrictions
  const getRestrictions = () => {
    const restrictions = {
      message: 'Declare your target pile count',
      disabledValues: [],
    };

    // Check if player is last to declare
    const declaredCount = Object.keys(declarations).length;
    const isLastPlayer = declaredCount === players.length - 1;

    if (isLastPlayer) {
      // Total cannot equal 8
      const remainingForEight = 8 - totalDeclared;
      if (remainingForEight >= 0 && remainingForEight <= 8) {
        restrictions.disabledValues.push(remainingForEight);
        restrictions.message = 'The total number cannot be 8';
      }
    }

    // Check consecutive zeros (player declared 0 twice in a row)
    if (consecutiveZeros >= 2) {
      restrictions.disabledValues.push(0);
      restrictions.message = 'No third consecutive 0';
    }

    return restrictions;
  };

  const restrictions = getRestrictions();

  // Get player status
  const getPlayerStatus = (player) => {
    // Players are now always objects
    const playerName = player.name;

    if (declarations[playerName] !== undefined) {
      return {
        type: 'declared',
        value: declarations[playerName],
      };
    } else if (playerName === currentPlayer) {
      return {
        type: 'current',
        text: 'Declaring',
      };
    } else {
      // Check if this player will declare after current player
      const currentIndex = players.findIndex((p) => p.name === currentPlayer);
      const playerIndex = players.findIndex((p) => p.name === playerName);

      if (
        currentIndex !== -1 &&
        playerIndex !== -1 &&
        playerIndex === currentIndex + 1
      ) {
        return {
          type: 'pending',
          text: 'Next',
        };
      }

      return {
        type: 'waiting',
        text: 'Waiting',
      };
    }
  };

  // Handle declaration selection
  const handleSelectValue = (value) => {
    if (!restrictions.disabledValues.includes(value)) {
      setSelectedValue(value);
    }
  };

  // Handle confirm
  const handleConfirm = () => {
    if (selectedValue !== null && onDeclare) {
      onDeclare(selectedValue);
    }
  };

  // Handle clear
  const handleClear = () => {
    setSelectedValue(null);
  };

  // Get status badge style
  const getStatusBadgeStyle = (type) => {
    switch (type) {
      case 'current':
        return styles.statusCurrent;
      case 'pending':
        return styles.statusPending;
      case 'waiting':
      default:
        return styles.statusWaiting;
    }
  };

  return (
    <>
      {/* Game status section */}
      <div {...stylex.props(styles.gameStatusSection)}>
        {/* Players list */}
        <div {...stylex.props(styles.playersList)}>
          {players.map((player) => {
            // Debug logging to understand data structure
            console.log(
              '🎨 Declaration player data:',
              player.name,
              'avatar_color:',
              player.avatar_color,
              'is_bot:',
              player.is_bot,
              'full player:',
              player
            );

            // Players should now always be objects with is_bot property
            const playerName = player.name;
            const displayName = playerName;

            const status = getPlayerStatus(player);
            const isCurrentTurn = playerName === currentPlayer;
            const isDeclared = status.type === 'declared';

            return (
              <div
                key={playerName}
                {...stylex.props(
                  styles.playerRow,
                  isCurrentTurn && styles.playerRowCurrentTurn,
                  isDeclared && styles.playerRowDeclared
                )}
              >
                <PlayerAvatar
                  name={displayName}
                  isBot={player.is_bot}
                  isThinking={isCurrentTurn && player.is_bot}
                  avatarColor={player.avatar_color}
                  size="large"
                />
                <div {...stylex.props(styles.playerInfo)}>
                  <div {...stylex.props(styles.playerName)}>
                    {displayName}
                    {playerName === myName ? ' (You)' : ''}
                  </div>
                </div>
                <div {...stylex.props(styles.playerStatus)}>
                  {status.type === 'declared' ? (
                    <div {...stylex.props(styles.declaredValue)}>
                      {status.value}
                    </div>
                  ) : (
                    <div {...stylex.props(
                      styles.statusBadge,
                      getStatusBadgeStyle(status.type)
                    )}>
                      {status.text}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Declaration panel - sliding tray */}
      <div {...stylex.props(
        styles.panel,
        showPanel && styles.panelShow
      )}>
        <div {...stylex.props(styles.options)}>
          {[0, 1, 2, 3, 4, 5, 6, 7, 8].map((value) => {
            const isDisabled = restrictions.disabledValues.includes(value);
            const isSelected = selectedValue === value;

            return (
              <button
                key={value}
                {...stylex.props(
                  styles.option,
                  isSelected && styles.optionSelected,
                  isDisabled && styles.optionDisabled
                )}
                onClick={() => handleSelectValue(value)}
                disabled={isDisabled}
              >
                {value}
              </button>
            );
          })}
        </div>

        <div {...stylex.props(styles.actions)}>
          <button
            {...stylex.props(styles.actionBtn, styles.primaryBtn)}
            onClick={handleConfirm}
            disabled={selectedValue === null}
          >
            Confirm
          </button>
          <button 
            {...stylex.props(styles.actionBtn, styles.secondaryBtn)}
            onClick={handleClear}
          >
            Clear
          </button>
        </div>
      </div>

      {/* Hand section - always visible at bottom */}
      <PieceTray pieces={myHand} showValues />
    </>
  );
};

DeclarationContent.propTypes = {
  myHand: PropTypes.array,
  players: PropTypes.array,
  currentPlayer: PropTypes.string,
  myName: PropTypes.string,
  declarations: PropTypes.object,
  totalDeclared: PropTypes.number,
  consecutiveZeros: PropTypes.number,
  redealMultiplier: PropTypes.number,
  onDeclare: PropTypes.func,
};

export default DeclarationContent;