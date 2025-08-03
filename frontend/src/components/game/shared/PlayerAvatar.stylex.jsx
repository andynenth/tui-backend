// PlayerAvatar component with StyleX
import React from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, shadows, layout, motion, typography } from '../../../design-system/tokens.stylex';

// SVG imports
import BotIcon from '../../../assets/avatars/bot.svg';
import HumanIcon from '../../../assets/avatars/human.svg';

// Animation keyframes
const thinking = stylex.keyframes({
  '0%, 100%': {
    transform: 'scale(1)',
    opacity: 1,
  },
  '50%': {
    transform: 'scale(0.95)',
    opacity: 0.7,
  },
});

const pulse = stylex.keyframes({
  '0%, 100%': {
    boxShadow: `0 0 0 0 ${colors.secondary}`,
  },
  '50%': {
    boxShadow: `0 0 0 8px rgba(124, 58, 237, 0.1)`,
  },
});

const disconnectPulse = stylex.keyframes({
  '0%, 100%': {
    opacity: 0.5,
  },
  '50%': {
    opacity: 1,
  },
});

const styles = stylex.create({
  wrapper: {
    position: 'relative',
    display: 'inline-block',
  },
  
  avatar: {
    borderRadius: layout.radiusFull,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.surface,
    border: `2px solid ${colors.border}`,
    overflow: 'hidden',
    position: 'relative',
    transition: motion.transitionBase,
    boxShadow: shadows.md,
    
    ':hover': {
      transform: 'scale(1.05)',
      boxShadow: shadows.lg,
    },
  },
  
  // Size variants
  sizeMini: {
    width: '24px',
    height: '24px',
    fontSize: typography.textXs,
  },
  
  sizeSmall: {
    width: '32px',
    height: '32px',
    fontSize: typography.textSm,
  },
  
  sizeMedium: {
    width: '40px',
    height: '40px',
    fontSize: typography.textMd,
  },
  
  sizeLarge: {
    width: '56px',
    height: '56px',
    fontSize: typography.textLg,
  },
  
  // Theme variants
  themeDefault: {
    backgroundColor: colors.surface,
  },
  
  themeYellow: {
    backgroundColor: colors.pieceGold,
    border: `2px solid ${colors.warning}`,
  },
  
  // Bot styles
  bot: {
    backgroundColor: colors.secondary,
    backgroundImage: `linear-gradient(135deg, ${colors.secondary} 0%, ${colors.secondaryHover} 100%)`,
    border: `2px solid ${colors.secondaryActive}`,
  },
  
  // Color variants for human players
  colorRed: {
    backgroundColor: colors.pieceRed,
    border: `2px solid ${colors.danger}`,
  },
  
  colorBlue: {
    backgroundColor: colors.slotPlayer,
    border: `2px solid ${colors.primary}`,
  },
  
  colorGreen: {
    backgroundColor: colors.success,
    border: `2px solid ${colors.successDark}`,
  },
  
  colorYellow: {
    backgroundColor: colors.pieceGold,
    border: `2px solid ${colors.warning}`,
  },
  
  colorPurple: {
    backgroundColor: colors.slotBot,
    border: `2px solid ${colors.secondary}`,
  },
  
  colorGray: {
    backgroundColor: colors.gray500,
    border: `2px solid ${colors.gray600}`,
  },
  
  // States
  thinkingState: {
    animation: `${thinking} 1.5s ${motion.easeInOut} infinite`,
    ':after': {
      content: '""',
      position: 'absolute',
      inset: 0,
      borderRadius: layout.radiusFull,
      animation: `${pulse} 2s ${motion.easeInOut} infinite`,
    },
  },
  
  disconnected: {
    opacity: 0.5,
    filter: 'grayscale(100%)',
    animation: `${disconnectPulse} 2s ${motion.easeInOut} infinite`,
  },
  
  icon: {
    width: '70%',
    height: '70%',
    objectFit: 'contain',
  },
  
  // Badges
  badge: {
    position: 'absolute',
    backgroundColor: colors.textLight,
    borderRadius: layout.radiusFull,
    fontSize: typography.textXs,
    fontWeight: typography.weightBold,
    padding: '2px 6px',
    boxShadow: shadows.sm,
    zIndex: 1,
  },
  
  aiBadge: {
    bottom: '-4px',
    right: '-4px',
    backgroundColor: colors.secondary,
    color: colors.textLight,
    border: `2px solid ${colors.textLight}`,
  },
  
  disconnectBadge: {
    top: '-4px',
    right: '-4px',
    backgroundColor: colors.danger,
    color: colors.textLight,
    fontSize: '10px',
    width: '16px',
    height: '16px',
    padding: 0,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  
  // Initials text (fallback when no icon)
  initials: {
    fontWeight: typography.weightBold,
    color: colors.textLight,
    textTransform: 'uppercase',
  },
});

const PlayerAvatar = ({
  name,
  isBot = false,
  isThinking = false,
  className = '',
  size = 'medium',
  theme = 'default',
  isDisconnected = false,
  showAIBadge = false,
  avatarColor = null,
}) => {
  // Debug logging
  if (process.env.NODE_ENV === 'development') {
    console.log('🎨 PlayerAvatar received:', { name, isBot, avatarColor });
  }
  
  // Get size style
  const getSizeStyle = () => {
    const sizeMap = {
      'mini': styles.sizeMini,
      'small': styles.sizeSmall,
      'medium': styles.sizeMedium,
      'large': styles.sizeLarge,
    };
    return sizeMap[size] || styles.sizeMedium;
  };
  
  // Get theme style
  const getThemeStyle = () => {
    return theme === 'yellow' ? styles.themeYellow : styles.themeDefault;
  };
  
  // Get color style for human players
  const getColorStyle = () => {
    if (!isBot && avatarColor) {
      const colorMap = {
        'red': styles.colorRed,
        'blue': styles.colorBlue,
        'green': styles.colorGreen,
        'yellow': styles.colorYellow,
        'purple': styles.colorPurple,
        'gray': styles.colorGray,
        '1': styles.colorRed,
        '2': styles.colorBlue,
        '3': styles.colorGreen,
        '4': styles.colorYellow,
      };
      const colorStyle = colorMap[avatarColor];
      if (process.env.NODE_ENV === 'development' && colorStyle) {
        console.log(`🎨 PlayerAvatar ${name} color style applied`);
      }
      return colorStyle;
    }
    return null;
  };
  
  // Get initials for fallback display
  const getInitials = () => {
    if (!name) return '?';
    const parts = name.split(' ');
    if (parts.length >= 2) {
      return parts[0][0] + parts[1][0];
    }
    return name.substring(0, 2);
  };
  
  // Render bot avatar
  if (isBot) {
    return (
      <div {...stylex.props(styles.wrapper)}>
        <div
          {...stylex.props(
            styles.avatar,
            getSizeStyle(),
            getThemeStyle(),
            styles.bot,
            isThinking && styles.thinkingState,
            isDisconnected && styles.disconnected,
            className && { className }
          )}
        >
          <img 
            src={BotIcon} 
            alt="Bot" 
            {...stylex.props(styles.icon)}
          />
        </div>
        {showAIBadge && (
          <div {...stylex.props(styles.badge, styles.aiBadge)}>
            AI
          </div>
        )}
      </div>
    );
  }
  
  // Render human avatar
  return (
    <div {...stylex.props(styles.wrapper)}>
      <div
        {...stylex.props(
          styles.avatar,
          getSizeStyle(),
          getThemeStyle(),
          getColorStyle(),
          isDisconnected && styles.disconnected,
          className && { className }
        )}
      >
        {HumanIcon ? (
          <img 
            src={HumanIcon} 
            alt={name}
            {...stylex.props(styles.icon)}
          />
        ) : (
          <span {...stylex.props(styles.initials)}>
            {getInitials()}
          </span>
        )}
      </div>
      {isDisconnected && (
        <div {...stylex.props(styles.badge, styles.disconnectBadge)}>
          ●
        </div>
      )}
    </div>
  );
};

PlayerAvatar.propTypes = {
  name: PropTypes.string.isRequired,
  isBot: PropTypes.bool,
  isThinking: PropTypes.bool,
  className: PropTypes.string,
  size: PropTypes.oneOf(['mini', 'small', 'medium', 'large']),
  theme: PropTypes.oneOf(['default', 'yellow']),
  isDisconnected: PropTypes.bool,
  showAIBadge: PropTypes.bool,
  avatarColor: PropTypes.string,
};

export default PlayerAvatar;