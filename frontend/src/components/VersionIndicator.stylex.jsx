// frontend/src/components/VersionIndicator.stylex.jsx

import React from 'react';
import * as stylex from '@stylexjs/stylex';

const styles = stylex.create({
  indicator: {
    position: 'fixed',
    top: '4px',
    right: '4px',
    backgroundColor: '#6c40ff',
    color: '#ffffff',
    padding: '4px 8px',
    borderRadius: '8px',
    fontSize: '12px',
    fontWeight: '600',
    zIndex: 9999,
    boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
  },
});

export default function VersionIndicator() {
  return (
    <div {...stylex.props(styles.indicator)}>
      StyleX ✨
    </div>
  );
}