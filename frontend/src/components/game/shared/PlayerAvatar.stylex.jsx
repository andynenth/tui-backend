import React from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, motion, shadows, layout } from '../../../design-system/tokens.stylex';
import { animations } from '../../../design-system/utils.stylex';

// SVG imports
import BotIcon from '../../../assets/avatars/bot.svg';
import HumanIcon from '../../../assets/avatars/human.svg';

// Define thinking animation
const thinkingAnimation = stylex.keyframes({
  '0%, 100%': {
    transform: 'scale(1)',
    opacity: 1,
  },
  '50%': {
    transform: 'scale(1.05)',
    opacity: 0.8,
  },
});

// Avatar styles
const styles = stylex.create({
  wrapper: {
    position: 'relative',
    display: 'inline-block',
  },
  
  avatar: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: layout.radiusFull,
    backgroundColor: colors.gray200,
    border: `2px solid ${colors.gray300}`,
    overflow: 'hidden',
    transition: `all ${motion.durationBase} ${motion.easeInOut}`,
  },
  
  // Sizes
  mini: {
    width: '24px',
    height: '24px',
  },
  
  small: {
    width: '32px',
    height: '32px',
  },
  
  medium: {
    width: '48px',
    height: '48px',
  },
  
  large: {
    width: '64px',
    height: '64px',
  },
  
  // Themes
  yellow: {
    backgroundColor: colors.warning,
    borderColor: colors.warningDark,
  },
  
  // Bot specific
  bot: {
    backgroundColor: 'rgba(13, 110, 253, 0.1)',
    borderColor: colors.primary,
  },
  
  // States
  thinking: {
    animation: `${thinkingAnimation} 1.5s ${motion.easeInOut} infinite`,
  },
  
  disconnected: {
    opacity: 0.5,
    filter: 'grayscale(100%)',
  },
  
  // Avatar colors (for human players)
  colorRed: {
    backgroundColor: 'rgba(220, 53, 69, 0.1)',
    borderColor: colors.danger,
  },
  
  colorBlue: {
    backgroundColor: 'rgba(13, 110, 253, 0.1)',
    borderColor: colors.primary,
  },
  
  colorGreen: {
    backgroundColor: 'rgba(40, 167, 69, 0.1)',
    borderColor: colors.success,
  },
  
  colorYellow: {
    backgroundColor: 'rgba(255, 193, 7, 0.1)',
    borderColor: colors.warning,
  },
  
  colorPurple: {
    backgroundColor: 'rgba(124, 58, 237, 0.1)',
    borderColor: '#7c3aed',
  },
  
  colorOrange: {
    backgroundColor: 'rgba(255, 152, 0, 0.1)',
    borderColor: colors.warningDark,
  },
  
  // Icon styles
  icon: {
    width: '70%',
    height: '70%',
    objectFit: 'contain',
  },
  
  // Badge styles
  badge: {
    position: 'absolute',
    fontSize: typography.textXs,
    fontWeight: typography.weightBold,
    padding: `${spacing.xxs} ${spacing.xs}`,
    borderRadius: layout.radiusSm,
    border: '1px solid',
  },
  
  aiBadge: {
    bottom: '-4px',
    right: '-4px',
    backgroundColor: colors.primary,
    color: colors.white,
    borderColor: colors.primaryDark,
  },
  
  disconnectBadge: {
    top: '-4px',
    right: '-4px',
    backgroundColor: colors.danger,
    color: colors.white,
    borderColor: colors.dangerDark,
    fontSize: '10px',
    padding: spacing.xxs,
    borderRadius: layout.radiusFull,
    width: '16px',
    height: '16px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
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
  console.log('🎨 PlayerAvatar received:', { name, isBot, avatarColor });
  
  // Get color style
  const getColorStyle = () => {
    if (!isBot && avatarColor) {
      const colorMap = {
        'red': styles.colorRed,
        'blue': styles.colorBlue,
        'green': styles.colorGreen,
        'yellow': styles.colorYellow,
        'purple': styles.colorPurple,
        'orange': styles.colorOrange,
      };
      console.log(`🎨 PlayerAvatar ${name} color:`, avatarColor);
      return colorMap[avatarColor] || null;
    }
    return null;
  };

  // Apply avatar styles
  const avatarProps = stylex.props(
    styles.avatar,
    styles[size],
    theme === 'yellow' && styles.yellow,
    isBot && styles.bot,
    isThinking && styles.thinking,
    isDisconnected && styles.disconnected,
    getColorStyle()
  );

  // During migration, allow combining with existing CSS classes
  const combinedAvatarProps = className 
    ? { ...avatarProps, className: `${avatarProps.className || ''} ${className}`.trim() }
    : avatarProps;

  // Render bot avatar
  if (isBot) {
    return (
      <div {...stylex.props(styles.wrapper)}>
        <div {...combinedAvatarProps}>
          <img 
            src={BotIcon} 
            alt="Bot" 
            {...stylex.props(styles.icon)}
          />
        </div>
        {showAIBadge && (
          <div {...stylex.props(styles.badge, styles.aiBadge)}>AI</div>
        )}
      </div>
    );
  }

  // Render human avatar
  return (
    <div {...stylex.props(styles.wrapper)}>
      <div {...combinedAvatarProps}>
        <img 
          src={HumanIcon} 
          alt={name} 
          {...stylex.props(styles.icon)}
        />
      </div>
      {isDisconnected && (
        <div {...stylex.props(styles.badge, styles.disconnectBadge)}>
          🔴
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