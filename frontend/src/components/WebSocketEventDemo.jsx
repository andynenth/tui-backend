// frontend/src/components/WebSocketEventDemo.jsx

import React, { useEffect, useState } from 'react';
import { 
  NetworkServiceIntegration,
  initializeNetworkWithDisconnectHandling 
} from '../services/NetworkServiceIntegration';
import ToastContainer from './ToastContainer';
import ConnectionIndicator from './ConnectionIndicator';
import PlayerAvatar from './game/shared/PlayerAvatar';

const WebSocketEventDemo = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [roomId] = useState('demo-room');
  const [events, setEvents] = useState([]);
  const [disconnectedPlayers, setDisconnectedPlayers] = useState([]);

  useEffect(() => {
    // Initialize with custom handlers
    const handlers = {
      onPlayerDisconnected: (data) => {
        console.log('Demo: Player disconnected', data);
        setEvents(prev => [...prev, { type: 'disconnect', data, time: new Date() }]);
        setDisconnectedPlayers(prev => [...prev, data.player_name]);
      },
      onPlayerReconnected: (data) => {
        console.log('Demo: Player reconnected', data);
        setEvents(prev => [...prev, { type: 'reconnect', data, time: new Date() }]);
        setDisconnectedPlayers(prev => prev.filter(name => name !== data.player_name));
      },
    };

    // Initialize network with disconnect handling
    initializeNetworkWithDisconnectHandling(roomId, handlers)
      .then(() => {
        setIsConnected(true);
        console.log('Connected to demo room');
      })
      .catch(err => {
        console.error('Failed to connect:', err);
        setIsConnected(false);
      });

    // Cleanup
    return () => {
      NetworkServiceIntegration.cleanup();
    };
  }, [roomId]);

  const simulateDisconnect = (playerName) => {
    NetworkServiceIntegration.sendTestDisconnectEvent(playerName);
  };

  const simulateReconnect = (playerName) => {
    NetworkServiceIntegration.sendTestReconnectEvent(playerName);
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>WebSocket Event Integration Demo</h1>
      
      <section style={{ marginBottom: '20px' }}>
        <h2>Connection Status</h2>
        <ConnectionIndicator 
          isConnected={isConnected}
          disconnectedPlayers={disconnectedPlayers}
          showAIStatus={true}
        />
      </section>

      <section style={{ marginBottom: '20px' }}>
        <h2>Test Players</h2>
        <div style={{ display: 'flex', gap: '20px' }}>
          {['Alice', 'Bob', 'Charlie'].map(name => (
            <div key={name} style={{ textAlign: 'center' }}>
              <PlayerAvatar
                name={name}
                isDisconnected={disconnectedPlayers.includes(name)}
                showConnectionStatus={true}
                size="large"
              />
              <h3>{name}</h3>
              <button onClick={() => simulateDisconnect(name)}>
                Disconnect
              </button>
              {' '}
              <button onClick={() => simulateReconnect(name)}>
                Reconnect
              </button>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2>Event Log</h2>
        <div style={{ 
          maxHeight: '200px', 
          overflow: 'auto',
          border: '1px solid #ccc',
          padding: '10px',
          fontSize: '12px'
        }}>
          {events.map((event, idx) => (
            <div key={idx}>
              [{event.time.toLocaleTimeString()}] {event.type}: {event.data.player_name}
            </div>
          ))}
        </div>
      </section>

      <ToastContainer position="top-right" />
    </div>
  );
};

export default WebSocketEventDemo;
