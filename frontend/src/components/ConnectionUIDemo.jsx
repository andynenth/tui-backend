// frontend/src/components/ConnectionUIDemo.jsx

import React, { useState } from 'react';
import PlayerAvatar from './game/shared/PlayerAvatar';
import ConnectionIndicator from './ConnectionIndicator';

const ConnectionUIDemo = () => {
  const [connectionStates, setConnectionStates] = useState({
    Alice: { status: 'connected', isBot: false },
    Bob: { status: 'disconnected', isBot: true },
    Charlie: { status: 'reconnecting', isBot: false },
    David: { status: 'connected', isBot: false }
  });

  const toggleConnection = (playerName) => {
    setConnectionStates(prev => {
      const current = prev[playerName];
      let newStatus = current.status;
      let newIsBot = current.isBot;

      if (current.status === 'connected') {
        newStatus = 'disconnected';
        newIsBot = true;
      } else if (current.status === 'disconnected') {
        newStatus = 'reconnecting';
        newIsBot = false;
      } else {
        newStatus = 'connected';
        newIsBot = false;
      }

      return {
        ...prev,
        [playerName]: { status: newStatus, isBot: newIsBot }
      };
    });
  };

  const disconnectedPlayers = Object.entries(connectionStates)
    .filter(([_, state]) => state.status === 'disconnected')
    .map(([name]) => name);

  return (
    <div style={{ padding: '20px', backgroundColor: '#f5f5f5', minHeight: '100vh' }}>
      <h1>Connection Status UI Demo</h1>
      
      <section style={{ marginBottom: '40px' }}>
        <h2>Connection Indicator</h2>
        <ConnectionIndicator 
          isConnected={true}
          disconnectedPlayers={disconnectedPlayers}
          showAIStatus={true}
        />
      </section>

      <section>
        <h2>Player Avatars with Connection Status</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '40px', maxWidth: '600px' }}>
          {Object.entries(connectionStates).map(([playerName, state]) => (
            <div key={playerName} style={{ 
              backgroundColor: 'white', 
              padding: '20px', 
              borderRadius: '8px',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
            }}>
              <h3>{playerName}</h3>
              <div style={{ marginBottom: '20px' }}>
                <PlayerAvatar
                  name={playerName}
                  isBot={state.isBot}
                  isDisconnected={state.status !== 'connected'}
                  connectionStatus={state.status}
                  showConnectionStatus={true}
                  showDisconnectOverlay={false}
                  size="large"
                />
              </div>
              <button 
                onClick={() => toggleConnection(playerName)}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#3b82f6',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Toggle Connection
              </button>
              <p style={{ marginTop: '10px', fontSize: '14px', color: '#666' }}>
                Status: {state.status}
                {state.isBot && ' (AI Playing)'}
              </p>
            </div>
          ))}
        </div>
      </section>

      <section style={{ marginTop: '40px' }}>
        <h2>Avatar with Overlay Demo</h2>
        <div style={{ 
          display: 'inline-block', 
          position: 'relative',
          backgroundColor: 'white',
          padding: '40px',
          borderRadius: '8px'
        }}>
          <PlayerAvatar
            name="Demo Player"
            isBot={true}
            isDisconnected={true}
            connectionStatus="disconnected"
            showConnectionStatus={true}
            showDisconnectOverlay={true}
            size="large"
          />
        </div>
      </section>
    </div>
  );
};

export default ConnectionUIDemo;