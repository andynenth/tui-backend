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
    padding: '1rem',
    borderRadius: '0.375rem',
    borderWidth: '2px',
    borderStyle: 'solid',
    minHeight: '120px',
    transition: `all '300ms' 'cubic-bezier(0, 0, 0.2, 1)'`,
    transformOrigin: 'center',
    ':hover': {
      boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
      transform: 'scale(1.05)',
    },
  },
  
  emptySlot: {
    borderStyle: 'dashed',
    borderColor: '#dee2e6',
    backgroundImage: `linear-gradient(135deg, '#f8f9fa' 0%, '#f1f3f5' 100%)`,
    ':hover': {
      borderColor: '#ced4da',
      backgroundImage: `linear-gradient(135deg, '#f1f3f5' 0%, '#e9ecef' 100%)`,
    },
  },
  
  hostSlot: {
    borderColor: '#ffc107',
    backgroundImage: `linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)`,
    boxShadow: '0 10px 15px -3px rgba(251, 191, 36, 0.2)',
    outline: `2px solid rgba(251, 191, 36, 0.5)`,
    outlineOffset: '2px',
  },
  
  currentPlayerSlot: {
    borderColor: '#0d6efd',
    backgroundImage: `linear-gradient(135deg, '#e7f1ff' 0%, #dbeafe 100%)`,
    boxShadow: '0 10px 15px -3px rgba(59, 130, 246, 0.2)',
    outline: `4px solid rgba(59, 130, 246, 0.5)`,
    outlineOffset: '2px',
    animation: `${pulse} 2s 'cubic-bezier(0.4, 0, 0.2, 1)' infinite`,
  },
  
  botSlot: {
    borderColor: '#a855f7',
    backgroundImage: 'linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%)',
    boxShadow: '0 10px 15px -3px rgba(168, 85, 247, 0.2)',
  },
  
  normalSlot: {
    borderColor: '#ced4da',
    backgroundImage: `linear-gradient(135deg, '#ffffff' 0%, '#f8f9fa' 100%)`,
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
  },
  
  content: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '0.5rem',
    width: '100%',
  },
  
  emptyContent: {
    gap: '1rem',
  },
  
  slotLabel: {
    fontSize: '0.875rem',
    color: '#adb5bd',
    fontWeight: '500',
  },
  
  emptyLabel: {
    fontSize: '0.75rem',
    color: '#ced4da',
  },
  
  buttonContainer: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
    width: '100%',
  },
  
  playerInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
  },
  
  icon: {
    fontSize: '1.125rem',
  },
  
  nameContainer: {
    textAlign: 'center',
  },
  
  playerName: {
    fontWeight: '500',
    fontSize: '0.875rem',
    maxWidth: '100px',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  
  slotNumber: {
    fontSize: '0.75rem',
    color: '#adb5bd',
  },
  
  youBadge: {
    fontSize: '0.75rem',
    fontWeight: '700',
    color: '#0056b3',
    backgroundColor: '#e7f1ff',
    paddingTop: '0.25rem',
    paddingBottom: '0.25rem',
    paddingLeft: '0.5rem',
    paddingRight: '0.5rem',
    borderRadius: '0.125rem',
  },
  
  scoreBadge: {
    fontSize: '0.75rem',
    color: '#6c757d',
    backgroundColor: '#f1f3f5',
    paddingTop: '0.25rem',
    paddingBottom: '0.25rem',
    paddingLeft: '0.5rem',
    paddingRight: '0.5rem',
    borderRadius: '0.125rem',
  },
  
  actionButtons: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.25rem',
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