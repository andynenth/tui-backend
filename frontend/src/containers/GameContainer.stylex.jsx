import React from 'react';
import * as stylex from '@stylexjs/stylex';

const styles = stylex.create({
  container: {
    width: '100%',
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: '#f8f9fa',
  },
  content: {
    flex: 1,
    padding: '20px',
  },
});

export const GameContainer = ({ roomId, onNavigateToLobby, children }) => {
  return (
    <div {...stylex.props(styles.container)}>
      <div {...stylex.props(styles.content)}>
        <h2>Game Room: {roomId}</h2>
        <button onClick={onNavigateToLobby}>Back to Lobby</button>
        {children}
      </div>
    </div>
  );
};

export default GameContainer;