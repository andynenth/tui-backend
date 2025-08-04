// frontend/src/components/PlayerSlot.stylex.jsx

import React from 'react';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, layout, shadows, motion } from '../design-system/tokens.stylex';
import Button from './Button.stylex';

// Animations
const pulse = stylex.keyframes({
  '0%, 100%': {
    opacity: 1,
  },
  '50%': {
    opacity: 0.7,
  },
});

// PlayerSlot styles
const styles = stylex.create({
  slot: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.md,
    borderRadius: layout.radiusMd,
    borderWidth: '2px',
    borderStyle: 'solid',
    minHeight: '120px',
    transition: `all ${motion.durationBase} ${motion.easeOut}`,
    transformOrigin: 'center',
    ':hover': {
      boxShadow: shadows.lg,
      transform: 'scale(1.05)',
    },
  },
  
  emptySlot: {
    borderStyle: 'dashed',
    borderColor: colors.gray300,
    backgroundImage: `linear-gradient(135deg, ${colors.gray50} 0%, ${colors.gray100} 100%)`,
    ':hover': {
      borderColor: colors.gray400,
      backgroundImage: `linear-gradient(135deg, ${colors.gray100} 0%, ${colors.gray200} 100%)`,
    },
  },
  
  hostSlot: {
    borderColor: colors.warning,
    backgroundImage: `linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)`,
    boxShadow: '0 10px 15px -3px rgba(251, 191, 36, 0.2)',
    outline: `2px solid rgba(251, 191, 36, 0.5)`,
    outlineOffset: '2px',
  },
  
  currentPlayerSlot: {
    borderColor: colors.primary,
    backgroundImage: `linear-gradient(135deg, ${colors.primaryLight} 0%, #dbeafe 100%)`,
    boxShadow: '0 10px 15px -3px rgba(59, 130, 246, 0.2)',
    outline: `4px solid rgba(59, 130, 246, 0.5)`,
    outlineOffset: '2px',
    animation: `${pulse} 2s ${motion.easeInOut} infinite`,
  },
  
  botSlot: {
    borderColor: '#a855f7',
    backgroundImage: 'linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%)',
    boxShadow: '0 10px 15px -3px rgba(168, 85, 247, 0.2)',
  },
  
  normalSlot: {
    borderColor: colors.gray400,
    backgroundImage: `linear-gradient(135deg, ${colors.white} 0%, ${colors.gray50} 100%)`,
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
  },
  
  content: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: spacing.sm,
    width: '100%',
  },
  
  emptyContent: {
    gap: spacing.md,
  },
  
  slotLabel: {
    fontSize: typography.textSm,
    color: colors.gray500,
    fontWeight: typography.weightMedium,
  },
  
  emptyLabel: {
    fontSize: typography.textXs,
    color: colors.gray400,
  },
  
  buttonContainer: {
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.sm,
    width: '100%',
  },
  
  playerInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.sm,
  },
  
  icon: {
    fontSize: typography.textLg,
  },
  
  nameContainer: {
    textAlign: 'center',
  },
  
  playerName: {
    fontWeight: typography.weightMedium,
    fontSize: typography.textSm,
    maxWidth: '100px',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  
  slotNumber: {
    fontSize: typography.textXs,
    color: colors.gray500,
  },
  
  youBadge: {
    fontSize: typography.textXs,
    fontWeight: typography.weightBold,
    color: colors.primaryDark,
    backgroundColor: colors.primaryLight,
    paddingTop: spacing.xs,
    paddingBottom: spacing.xs,
    paddingLeft: spacing.sm,
    paddingRight: spacing.sm,
    borderRadius: layout.radiusSm,
  },
  
  scoreBadge: {
    fontSize: typography.textXs,
    color: colors.gray600,
    backgroundColor: colors.gray100,
    paddingTop: spacing.xs,
    paddingBottom: spacing.xs,
    paddingLeft: spacing.sm,
    paddingRight: spacing.sm,
    borderRadius: layout.radiusSm,
  },
  
  actionButtons: {
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.xs,
    width: '100%',
  },
});

/**
 * PlayerSlot Component
 *
 * Displays a player slot in the game lobby
 * Shows player info, host status, and slot actions
 */
const PlayerSlot = ({
  slotId,
  occupant,
  isHost = false,
  isCurrentPlayer = false,
  canModify = false,
  playerName = null,
  score = null,
  onJoin,
  onAddBot,
  onRemove,
  className = '',
}) => {
  const getSlotStyle = () => {
    if (!occupant) {
      return [styles.slot, styles.emptySlot];
    }
    if (isHost) {
      return [styles.slot, styles.hostSlot];
    }
    if (isCurrentPlayer) {
      return [styles.slot, styles.currentPlayerSlot];
    }
    if (occupant.is_bot || occupant.isBot) {
      return [styles.slot, styles.botSlot];
    }
    return [styles.slot, styles.normalSlot];
  };

  const renderSlotContent = () => {
    if (!occupant) {
      return (
        <div {...stylex.props(styles.content, styles.emptyContent)}>
          <div {...stylex.props(styles.slotLabel)}>Slot {slotId}</div>
          <div {...stylex.props(styles.emptyLabel)}>Empty</div>

          <div {...stylex.props(styles.buttonContainer)}>
            {onJoin && (
              <Button size="sm" fullWidth onClick={() => onJoin(slotId)}>
                Join Slot
              </Button>
            )}
            {onAddBot && canModify && (
              <Button
                variant="outline"
                size="sm"
                fullWidth
                onClick={() => onAddBot(slotId)}
              >
                Add Bot
              </Button>
            )}
          </div>
        </div>
      );
    }

    const displayName = occupant.name || playerName || 'Unknown';
    const isBot = occupant.is_bot || occupant.isBot;

    return (
      <div {...stylex.props(styles.content)}>
        {/* Player info header */}
        <div {...stylex.props(styles.playerInfo)}>
          {isHost && (
            <span {...stylex.props(styles.icon)} title="Host">
              👑
            </span>
          )}
          {isBot && (
            <span {...stylex.props(styles.icon)} title="Bot">
              🤖
            </span>
          )}
          <div {...stylex.props(styles.nameContainer)}>
            <div
              {...stylex.props(styles.playerName)}
              title={displayName}
            >
              {displayName}
            </div>
            <div {...stylex.props(styles.slotNumber)}>Slot {slotId}</div>
          </div>
          {isCurrentPlayer && (
            <span {...stylex.props(styles.youBadge)}>
              YOU
            </span>
          )}
        </div>

        {/* Score display if available */}
        {typeof score === 'number' && (
          <div {...stylex.props(styles.scoreBadge)}>
            Score: {score}
          </div>
        )}

        {/* Action buttons for host/moderator */}
        {canModify && onRemove && !isCurrentPlayer && (
          <div {...stylex.props(styles.actionButtons)}>
            <Button
              variant="danger"
              size="sm"
              fullWidth
              onClick={() => onRemove(slotId)}
            >
              {isBot ? 'Remove Bot' : 'Kick Player'}
            </Button>
            {!isBot && onAddBot && (
              <Button
                variant="ghost"
                size="sm"
                fullWidth
                onClick={() => onAddBot(slotId)}
              >
                Replace with Bot
              </Button>
            )}
          </div>
        )}
      </div>
    );
  };

  // Apply slot styles
  const slotProps = stylex.props(...getSlotStyle());
  
  // During migration, allow combining with existing CSS classes
  const combinedSlotProps = className 
    ? { ...slotProps, className: `${slotProps.className || ''} ${className}`.trim() }
    : slotProps;

  return (
    <div {...combinedSlotProps}>
      {renderSlotContent()}
    </div>
  );
};

export default PlayerSlot;