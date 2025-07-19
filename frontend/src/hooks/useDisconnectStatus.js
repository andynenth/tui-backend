// frontend/src/hooks/useDisconnectStatus.js

import { useState, useEffect, useCallback } from 'react';
// Note: This hook listens to window events dispatched by DisconnectEventService
// It does not directly interact with NetworkService

const useDisconnectStatus = (playerName) => {
  const [connectionStatus, setConnectionStatus] = useState('connected');
  const [isDisconnected, setIsDisconnected] = useState(false);
  const [isBot, setIsBot] = useState(false);
  const [canReconnect, setCanReconnect] = useState(true);

  useEffect(() => {
    const handleDisconnectEvent = (data) => {
      if (data.player_name === playerName || data.playerName === playerName) {
        setConnectionStatus('disconnected');
        setIsDisconnected(true);
        setIsBot(data.ai_activated || data.aiActivated || false);
        setCanReconnect(data.can_reconnect !== false);
      }
    };

    const handleReconnectEvent = (data) => {
      if (data.player_name === playerName || data.playerName === playerName) {
        setConnectionStatus('connected');
        setIsDisconnected(false);
        setIsBot(false);
      }
    };

    const handleFullStateSync = (data) => {
      if (data.reconnectedPlayer === playerName) {
        setConnectionStatus('connected');
        setIsDisconnected(false);
        
        // Check if player is still a bot in the synced state
        const playerData = data.players?.[playerName];
        if (playerData) {
          setIsBot(playerData.is_bot || playerData.isBot || false);
        }
      }
    };

    const handlePhaseChange = (data) => {
      // Update bot status from phase change data
      const players = data.players || data.phase_data?.players;
      if (players && players[playerName]) {
        setIsBot(players[playerName].is_bot || players[playerName].isBot || false);
      }
    };

    // Subscribe to window events dispatched by DisconnectEventService
    window.addEventListener('player_disconnected', handleDisconnectEvent);
    window.addEventListener('player_reconnected', handleReconnectEvent);
    window.addEventListener('full_state_sync', handleFullStateSync);
    window.addEventListener('phase_change', handlePhaseChange);

    // Cleanup
    return () => {
      window.removeEventListener('player_disconnected', handleDisconnectEvent);
      window.removeEventListener('player_reconnected', handleReconnectEvent);
      window.removeEventListener('full_state_sync', handleFullStateSync);
      window.removeEventListener('phase_change', handlePhaseChange);
    };
  }, [playerName]);

  const updateConnectionStatus = useCallback((status) => {
    setConnectionStatus(status);
    setIsDisconnected(status === 'disconnected');
  }, []);

  return {
    connectionStatus,
    isDisconnected,
    isBot,
    canReconnect,
    updateConnectionStatus
  };
};

export default useDisconnectStatus;