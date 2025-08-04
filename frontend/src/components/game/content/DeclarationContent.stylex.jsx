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
    padding: '1.5rem',
    overflowY: 'auto',
    flex: 1,
  },
  
  playersList: {
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
  },
  
  playerRowCurrentTurn: {
    backgroundColor: 'rgba(37, 99, 235, 0.05)',
    borderLeftWidth: '4px',
    borderLeftStyle: 'solid',
    borderLeftColor: '#0d6efd',
    animation: `${pulse} 2s 'cubic-bezier(0.4, 0, 0.2, 1)' infinite`,
  },
  
  playerRowDeclared: {
    opacity: 0.8,
    backgroundColor: '#f8f9fa',
  },
  
  playerInfo: {
    flex: 1,
    marginLeft: '1rem',
  },
  
  playerName: {
    fontSize: '1rem',
    fontWeight: '500',
    color: '#343a40',
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
    borderRadius: '9999px',
    background: gradients.primary,
    color: '#ffffff',
    fontSize: '1.25rem',
    fontWeight: '700',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  },
  
  statusBadge: {
    padding: `'0.25rem' '1rem'`,
    borderRadius: '9999px',
    fontSize: '0.875rem',
    fontWeight: '500',
    transition: `all '300ms' 'cubic-bezier(0.4, 0, 0.2, 1)'`,
  },
  
  statusCurrent: {
    backgroundColor: '#0d6efd',
    color: '#ffffff',
  },
  
  statusPending: {
    backgroundColor: '#ffc107',
    color: '#ffffff',
  },
  
  statusWaiting: {
    backgroundColor: '#e9ecef',
    color: '#6c757d',
  },
  
  panel: {
    position: 'fixed',
    bottom: '-200px',
    left: 0,
    right: 0,
    backgroundColor: '#ffffff',
    borderTopLeftRadius: '1rem',
    borderTopRightRadius: '1rem',
    boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    padding: '2rem',
    transition: `transform '300ms' 'cubic-bezier(0, 0, 0.2, 1)'`,
    zIndex: 40,
  },
  
  panelShow: {
    transform: 'translateY(-200px)',
    animation: `${slideInFromBottom} 0.3s 'cubic-bezier(0, 0, 0.2, 1)'`,
  },
  
  options: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '1rem',
    marginBottom: '1.5rem',
  },
  
  option: {
    aspectRatio: '1',
    borderRadius: '0.5rem',
    borderWidth: '2px',
    borderStyle: 'solid',
    borderColor: '#dee2e6',
    backgroundColor: '#ffffff',
    fontSize: '1.5rem',
    fontWeight: '700',
    color: '#495057',
    cursor: 'pointer',
    transition: `all '300ms' 'cubic-bezier(0.4, 0, 0.2, 1)'`,
    
    ':hover': {
      borderColor: '#0d6efd',
      backgroundColor: '#e7f1ff',
      transform: 'scale(1.05)',
    },
  },
  
  optionSelected: {
    borderColor: '#0d6efd',
    backgroundColor: '#0d6efd',
    color: '#ffffff',
    transform: 'scale(1.1)',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  },
  
  optionDisabled: {
    opacity: 0.4,
    cursor: 'not-allowed',
    backgroundColor: '#f1f3f5',
    
    ':hover': {
      borderColor: '#dee2e6',
      backgroundColor: '#f1f3f5',
      transform: 'scale(1)',
    },
  },
  
  actions: {
    display: 'flex',
    gap: '1rem',
    justifyContent: 'center',
  },
  
  actionBtn: {
    padding: `'0.5rem' '2rem'`,
    borderRadius: '0.375rem',
    fontSize: '1rem',
    fontWeight: '500',
    border: 'none',
    cursor: 'pointer',
    transition: `all '300ms' 'cubic-bezier(0.4, 0, 0.2, 1)'`,
  },
  
  primaryBtn: {
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
  
  secondaryBtn: {
    backgroundColor: '#e9ecef',
    color: '#495057',
    
    ':hover': {
      backgroundColor: '#dee2e6',
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
  currentPlayer = ',
  myName = ',
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
                    {playerName === myName ? ' (You)' : '}
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