import React, { useState, useEffect } from 'react';
import { useGameState } from '../../hooks/useGameState';
import { networkService } from '../../services/NetworkService';

/**
 * Debug overlay to track state synchronization issues
 * Shows current round, phase, and connection status
 */
const StateDebugOverlay = () => {
  const gameState = useGameState();
  const [lastUpdate, setLastUpdate] = useState(Date.now());
  const [messageLog, setMessageLog] = useState([]);
  const [isMinimized, setIsMinimized] = useState(false);

  useEffect(() => {
    // Update timestamp when state changes
    setLastUpdate(Date.now());
  }, [gameState.currentRound, gameState.phase]);

  useEffect(() => {
    // Listen for phase_change events
    const handlePhaseChange = (event) => {
      const { data } = event.detail;
      setMessageLog((prev) => [
        {
          time: new Date().toISOString(),
          type: 'phase_change',
          phase: data.phase,
          round: data.round,
          hasRound: 'round' in data,
        },
        ...prev.slice(0, 9), // Keep last 10 messages
      ]);
    };

    const handleReconnect = (event) => {
      setMessageLog((prev) => [
        {
          time: new Date().toISOString(),
          type: 'reconnected',
          roomId: event.detail.roomId,
        },
        ...prev.slice(0, 9),
      ]);
    };

    networkService.addEventListener('phase_change', handlePhaseChange);
    networkService.addEventListener('reconnected', handleReconnect);

    return () => {
      networkService.removeEventListener('phase_change', handlePhaseChange);
      networkService.removeEventListener('reconnected', handleReconnect);
    };
  }, []);

  const timeSinceUpdate = Math.floor((Date.now() - lastUpdate) / 1000);
  const isStale = timeSinceUpdate > 30;

  if (isMinimized) {
    return (
      <div
        className="debug-overlay-minimized"
        onClick={() => setIsMinimized(false)}
        style={{
          position: 'fixed',
          top: '10px',
          right: '10px',
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          color: 'white',
          padding: '5px 10px',
          borderRadius: '5px',
          cursor: 'pointer',
          zIndex: 9999,
          fontSize: '12px',
        }}
      >
        🐛 Debug
      </div>
    );
  }

  return (
    <div
      className="debug-overlay"
      style={{
        position: 'fixed',
        top: '10px',
        right: '10px',
        backgroundColor: 'rgba(0, 0, 0, 0.9)',
        color: 'white',
        padding: '15px',
        borderRadius: '10px',
        maxWidth: '300px',
        zIndex: 9999,
        fontSize: '12px',
        fontFamily: 'monospace',
        border: isStale ? '2px solid red' : '1px solid #333',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
        <h3 style={{ margin: 0 }}>🐛 State Debug</h3>
        <button
          onClick={() => setIsMinimized(true)}
          style={{
            background: 'none',
            border: 'none',
            color: 'white',
            cursor: 'pointer',
            fontSize: '16px',
          }}
        >
          ×
        </button>
      </div>

      <div style={{ marginBottom: '10px' }}>
        <div>
          <strong>Round:</strong> {gameState.currentRound}
        </div>
        <div>
          <strong>Phase:</strong> {gameState.phase}
        </div>
        <div>
          <strong>Connected:</strong>{' '}
          <span style={{ color: gameState.isConnected ? '#4ade80' : '#ef4444' }}>
            {gameState.isConnected ? 'Yes' : 'No'}
          </span>
        </div>
        <div>
          <strong>Last Update:</strong>{' '}
          <span style={{ color: isStale ? '#ef4444' : '#4ade80' }}>
            {timeSinceUpdate}s ago
          </span>
        </div>
        {isStale && (
          <div style={{ color: '#ef4444', marginTop: '5px' }}>
            ⚠️ State may be stale!
          </div>
        )}
      </div>

      <div>
        <strong>Recent Events:</strong>
        <div
          style={{
            maxHeight: '150px',
            overflowY: 'auto',
            marginTop: '5px',
            fontSize: '10px',
          }}
        >
          {messageLog.map((msg, idx) => (
            <div
              key={idx}
              style={{
                padding: '2px 0',
                borderBottom: '1px solid #333',
                color: msg.type === 'reconnected' ? '#fbbf24' : '#94a3b8',
              }}
            >
              <div>{msg.time.split('T')[1].split('.')[0]}</div>
              <div>
                {msg.type}: {msg.phase || msg.roomId}
                {msg.hasRound !== undefined && (
                  <span> (round: {msg.hasRound ? msg.round : 'missing'})</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      <button
        onClick={() => {
          console.log('Current Game State:', gameState);
          console.log('Message Log:', messageLog);
        }}
        style={{
          marginTop: '10px',
          width: '100%',
          padding: '5px',
          backgroundColor: '#1e40af',
          color: 'white',
          border: 'none',
          borderRadius: '5px',
          cursor: 'pointer',
        }}
      >
        Log Full State
      </button>
    </div>
  );
};

export default StateDebugOverlay;