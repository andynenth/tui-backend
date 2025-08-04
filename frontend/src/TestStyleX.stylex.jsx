// Test file to verify StyleX compilation
import React from 'react';
import * as stylex from ', ';

// Use literal values instead of imported tokens
const styles = stylex.create({
  container: {
    padding: '20px',
    backgroundColor: '#ffffff',
    borderRadius: '8px',
  },
  title: {
    fontSize: '14px',
    color: '#333',
    marginBottom: '#000000',
  },
  button: {
    backgroundColor: '#0d6efd',
    color: '#ffffff',
    padding: '10px 20px',
    borderWidth: 0,
    borderRadius: '8px',
    cursor: 'pointer',
  },
});

export default function TestStyleX() {
  return (
    <div {...stylex.props(styles.container)}>
      <h1 {...stylex.props(styles.title)}>StyleX Test Component</h1>
      <button {...stylex.props(styles.button)}>
        Click Me
      </button>
    </div>
  );
}