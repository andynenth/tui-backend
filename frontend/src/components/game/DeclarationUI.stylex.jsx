/**
 * 🎯 **DeclarationUI Component** - Declaration Phase Interface with StyleX
 *
 * Features:
 * ✅ Uses new StyleX components for consistent UI
 * ✅ Maps game state to content props
 * ✅ Handles declaration actions
 * ✅ Type-safe styling with StyleX
 */

import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
import PlayerAvatar from './shared/PlayerAvatar.stylex';
import PieceTray from './shared/PieceTray.stylex';
import Button from '../Button.stylex';
import { colors, spacing, shadows, layout, motion, typography } from '../../design-system/tokens.stylex';

// Animation keyframes
const slideIn = stylex.keyframes({
  '0%': {
    opacity: 0,
    transform: 'translateY(20px)',
  },
  '100%': {
    opacity: 1,
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

const fadeIn = stylex.keyframes({
  '0%': {
    opacity: 0,
  },
  '100%': {
    opacity: 1,
  },
});

const styles = stylex.create({
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.lg,
    padding: spacing.lg,
    minHeight: '100%',
  },
  
  // Game status section
  gameStatusSection: {
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.lg,
    animation: `${fadeIn} ${motion.durationNormal} ${motion.easeOut}`,
  },
  
  // Players list
  playersList: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: spacing.md,
    justifyContent: 'center',
    padding: spacing.md,
    backgroundColor: colors.surface,
    borderRadius: layout.radiusLg,
    boxShadow: shadows.sm,
  },
  
  playerItem: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: spacing.xs,
    padding: spacing.sm,
    borderRadius: layout.radiusMd,
    transition: motion.transitionBase,
    minWidth: '80px',
  },
  
  playerItemCurrent: {
    backgroundColor: colors.primary,
    color: colors.textLight,
    animation: `${pulse} 2s ${motion.easeInOut} infinite`,
  },
  
  playerItemDeclared: {
    backgroundColor: colors.success,
    color: colors.textLight,
  },
  
  playerItemPending: {
    backgroundColor: colors.warning,
    color: colors.textDark,
  },
  
  playerItemWaiting: {
    backgroundColor: colors.gray100,
    color: colors.gray600,
  },
  
  playerName: {
    fontSize: typography.textSm,
    fontWeight: typography.weightMedium,
    marginTop: spacing.xs,
    textAlign: 'center',
  },
  
  playerStatus: {
    fontSize: typography.textXs,
    opacity: 0.9,
  },
  
  declarationValue: {
    fontSize: typography.textLg,
    fontWeight: typography.weightBold,
    backgroundColor: colors.surface,
    color: colors.textDark,
    borderRadius: layout.radiusFull,
    width: '32px',
    height: '32px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: spacing.xs,
  },
  
  // Declaration panel
  declarationPanel: {
    backgroundColor: colors.surface,
    borderRadius: layout.radiusLg,
    padding: spacing.xl,
    boxShadow: shadows.lg,
    animation: `${slideIn} ${motion.durationNormal} ${motion.easeOut}`,
  },
  
  panelTitle: {
    fontSize: typography.textLg,
    fontWeight: typography.weightBold,
    color: colors.textDark,
    marginBottom: spacing.md,
    textAlign: 'center',
  },
  
  panelMessage: {
    fontSize: typography.textMd,
    color: colors.gray600,
    marginBottom: spacing.lg,
    textAlign: 'center',
  },
  
  // Number grid
  numberGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: spacing.sm,
    marginBottom: spacing.lg,
  },
  
  numberButton: {
    width: '60px',
    height: '60px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: typography.textXl,
    fontWeight: typography.weightBold,
    borderRadius: layout.radiusMd,
    border: `2px solid ${colors.border}`,
    backgroundColor: colors.surface,
    color: colors.textDark,
    cursor: 'pointer',
    transition: motion.transitionBase,
    
    ':hover': {
      backgroundColor: colors.primary,
      color: colors.textLight,
      transform: 'scale(1.05)',
    },
  },
  
  numberButtonSelected: {
    backgroundColor: colors.primary,
    color: colors.textLight,
    borderColor: colors.primaryDark,
    animation: `${pulse} 1s ${motion.easeInOut} infinite`,
  },
  
  numberButtonDisabled: {
    backgroundColor: colors.gray100,
    color: colors.gray400,
    cursor: 'not-allowed',
    opacity: 0.5,
    
    ':hover': {
      backgroundColor: colors.gray100,
      color: colors.gray400,
      transform: 'none',
    },
  },
  
  // Selected display
  selectedDisplay: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.md,
    padding: spacing.md,
    backgroundColor: colors.gray50,
    borderRadius: layout.radiusMd,
    marginBottom: spacing.lg,
    minHeight: '60px',
  },
  
  selectedLabel: {
    fontSize: typography.textMd,
    color: colors.gray600,
  },
  
  selectedValue: {
    fontSize: typography.textXxl,
    fontWeight: typography.weightBold,
    color: colors.primary,
  },
  
  // Actions
  panelActions: {
    display: 'flex',
    gap: spacing.md,
    justifyContent: 'center',
  },
  
  // Total counter
  totalCounter: {
    position: 'absolute',
    top: spacing.md,
    right: spacing.md,
    backgroundColor: colors.surface,
    padding: `${spacing.sm} ${spacing.md}`,
    borderRadius: layout.radiusFull,
    boxShadow: shadows.md,
    display: 'flex',
    alignItems: 'center',
    gap: spacing.sm,
  },
  
  totalLabel: {
    fontSize: typography.textSm,
    color: colors.gray600,
  },
  
  totalValue: {
    fontSize: typography.textLg,
    fontWeight: typography.weightBold,
    color: colors.primary,
  },
  
  // Hand tray section
  handTraySection: {
    marginTop: 'auto',
    borderTop: `1px solid ${colors.border}`,
    paddingTop: spacing.lg,
  },
  
  // Warning message
  warningMessage: {
    backgroundColor: colors.warning,
    color: colors.textDark,
    padding: spacing.sm,
    borderRadius: layout.radiusMd,
    fontSize: typography.textSm,
    textAlign: 'center',
    fontWeight: typography.weightMedium,
  },
});

/**
 * DeclarationUI - Declaration phase with integrated content
 */
export function DeclarationUI({
  // Data props
  myHand = [],
  declarations = {},
  players = [],
  currentTotal = 0,
  
  // State props
  currentPlayer = '',
  myName = '',
  consecutiveZeros = 0,
  redealMultiplier = 1,
  
  // Action props
  onDeclare,
  
  // Additional props
  className = '',
}) {
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
      const remainingForEight = 8 - currentTotal;
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
      setSelectedValue(null);
    }
  };
  
  // Handle clear
  const handleClear = () => {
    setSelectedValue(null);
  };
  
  // Get player item style based on status
  const getPlayerItemStyle = (status) => {
    const typeMap = {
      'current': styles.playerItemCurrent,
      'declared': styles.playerItemDeclared,
      'pending': styles.playerItemPending,
      'waiting': styles.playerItemWaiting,
    };
    return typeMap[status.type] || styles.playerItemWaiting;
  };
  
  return (
    <div {...stylex.props(styles.container, className && { className })}>
      {/* Total counter */}
      <div {...stylex.props(styles.totalCounter)}>
        <span {...stylex.props(styles.totalLabel)}>Total:</span>
        <span {...stylex.props(styles.totalValue)}>{currentTotal}</span>
      </div>
      
      {/* Game status section */}
      <div {...stylex.props(styles.gameStatusSection)}>
        {/* Players list */}
        <div {...stylex.props(styles.playersList)}>
          {players.map((player) => {
            const status = getPlayerStatus(player);
            
            return (
              <div
                key={player.name}
                {...stylex.props(
                  styles.playerItem,
                  getPlayerItemStyle(status)
                )}
              >
                <PlayerAvatar
                  name={player.name}
                  isBot={player.is_bot}
                  avatarColor={player.avatar_color}
                  size="medium"
                />
                <div {...stylex.props(styles.playerName)}>
                  {player.name}
                </div>
                {status.type === 'declared' ? (
                  <div {...stylex.props(styles.declarationValue)}>
                    {status.value}
                  </div>
                ) : (
                  <div {...stylex.props(styles.playerStatus)}>
                    {status.text}
                  </div>
                )}
              </div>
            );
          })}
        </div>
        
        {/* Declaration panel - only show when it's my turn */}
        {showPanel && isMyTurn && (
          <div {...stylex.props(styles.declarationPanel)}>
            <h3 {...stylex.props(styles.panelTitle)}>
              Your Declaration
            </h3>
            
            {restrictions.disabledValues.length > 0 && (
              <div {...stylex.props(styles.warningMessage)}>
                {restrictions.message}
              </div>
            )}
            
            <p {...stylex.props(styles.panelMessage)}>
              Choose number of piles you expect to win
            </p>
            
            {/* Selected display */}
            <div {...stylex.props(styles.selectedDisplay)}>
              {selectedValue !== null ? (
                <>
                  <span {...stylex.props(styles.selectedLabel)}>Selected:</span>
                  <span {...stylex.props(styles.selectedValue)}>
                    {selectedValue}
                  </span>
                </>
              ) : (
                <span {...stylex.props(styles.selectedLabel)}>
                  Select a number below
                </span>
              )}
            </div>
            
            {/* Number grid */}
            <div {...stylex.props(styles.numberGrid)}>
              {[0, 1, 2, 3, 4, 5, 6, 7, 8].map((value) => {
                const isDisabled = restrictions.disabledValues.includes(value);
                const isSelected = selectedValue === value;
                
                return (
                  <button
                    key={value}
                    {...stylex.props(
                      styles.numberButton,
                      isSelected && styles.numberButtonSelected,
                      isDisabled && styles.numberButtonDisabled
                    )}
                    onClick={() => handleSelectValue(value)}
                    disabled={isDisabled}
                  >
                    {value}
                  </button>
                );
              })}
            </div>
            
            {/* Actions */}
            <div {...stylex.props(styles.panelActions)}>
              <Button
                onClick={handleConfirm}
                variant="primary"
                disabled={selectedValue === null}
              >
                Confirm
              </Button>
              <Button
                onClick={handleClear}
                variant="secondary"
                disabled={selectedValue === null}
              >
                Clear
              </Button>
            </div>
          </div>
        )}
      </div>
      
      {/* Player's hand tray */}
      <div {...stylex.props(styles.handTraySection)}>
        <PieceTray
          pieces={myHand}
          variant="fixed"
          showValues={true}
          label="Your Hand"
        />
      </div>
    </div>
  );
}

DeclarationUI.propTypes = {
  // Data props
  myHand: PropTypes.array,
  declarations: PropTypes.object,
  players: PropTypes.array,
  currentTotal: PropTypes.number,
  
  // State props
  currentPlayer: PropTypes.string,
  myName: PropTypes.string,
  consecutiveZeros: PropTypes.number,
  redealMultiplier: PropTypes.number,
  
  // Action props
  onDeclare: PropTypes.func,
  
  // Additional props
  className: PropTypes.string,
};

DeclarationUI.defaultProps = {
  myHand: [],
  declarations: {},
  players: [],
  currentTotal: 0,
  currentPlayer: '',
  myName: '',
  consecutiveZeros: 0,
  redealMultiplier: 1,
  onDeclare: null,
  className: '',
};

export default DeclarationUI;