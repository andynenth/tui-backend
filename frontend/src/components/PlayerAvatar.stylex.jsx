import React from 'react';
import * as stylex from '@stylexjs/stylex';

const styles = stylex.create({
  avatar: {
    width: '32px',
    height: '32px',
    borderRadius: '50%',
    backgroundColor: '#dee2e6',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '14px',
    fontWeight: '600',
    color: '#495057',
  },
  mini: {
    width: '24px',
    height: '24px',
    fontSize: '12px',
  },
  small: {
    width: '32px',
    height: '32px',
    fontSize: '14px',
  },
  bot: {
    backgroundColor: '#f3e5ff',
    color: '#6b21a8',
  },
});

export const PlayerAvatar = ({ name, isBot, size = 'small', theme }) => {
  const initial = name ? name[0].toUpperCase() : '?';
  
  return (
    <div {...stylex.props(
      styles.avatar,
      size === 'mini' && styles.mini,
      size === 'small' && styles.small,
      isBot && styles.bot
    )}>
      {isBot ? '🤖' : initial}
    </div>
  );
};

export default PlayerAvatar;