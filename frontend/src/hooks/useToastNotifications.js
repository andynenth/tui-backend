// frontend/src/hooks/useToastNotifications.js

import { useState, useCallback, useEffect } from 'react';
import { disconnectEventService } from '../services/DisconnectEventService';

const useToastNotifications = () => {
  const [notifications, setNotifications] = useState([]);

  const addNotification = useCallback((notification) => {
    const id = notification.id || `toast-${Date.now()}-${Math.random()}`;
    const newNotification = {
      id,
      ...notification,
      createdAt: Date.now(),
    };

    setNotifications(prev => [...prev, newNotification]);
    return id;
  }, []);

  const removeNotification = useCallback((id) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  }, []);

  const clearAll = useCallback(() => {
    setNotifications([]);
  }, []);

  // Setup disconnect event listeners
  useEffect(() => {
    // Player disconnected
    const handlePlayerDisconnected = (event) => {
      const data = event.detail;
      addNotification({
        type: 'disconnect',
        title: 'Player Disconnected',
        message: `${data.player_name || data.playerName} lost connection. AI is taking over.`,
        duration: 5000,
      });
    };

    // Player reconnected
    const handlePlayerReconnected = (event) => {
      const data = event.detail;
      addNotification({
        type: 'reconnect',
        title: 'Player Reconnected',
        message: `${data.player_name || data.playerName} is back in control!`,
        duration: 5000,
      });
    };

    // AI activated
    const handleAIActivated = (event) => {
      const data = event.detail;
      addNotification({
        type: 'ai-activated',
        title: 'AI Activated',
        message: `AI is now playing for ${data.player_name || data.playerName}`,
        duration: 4000,
      });
    };

    // Reconnection summary
    const handleReconnectionSummary = (event) => {
      const data = event.detail;
      const missedCount = data.missed_events?.length || 0;
      
      if (missedCount > 0) {
        addNotification({
          type: 'info',
          title: 'Welcome Back!',
          message: `You missed ${missedCount} game event${missedCount > 1 ? 's' : ''} while away.`,
          duration: 6000,
        });
      }
    };

    // Connection status update
    const handleConnectionStatusUpdate = (event) => {
      const { disconnectedPlayers } = event.detail;
      
      if (disconnectedPlayers && disconnectedPlayers.length > 0) {
        addNotification({
          type: 'warning',
          title: 'Multiple Disconnections',
          message: `${disconnectedPlayers.length} player${disconnectedPlayers.length > 1 ? 's are' : ' is'} currently disconnected.`,
          duration: 5000,
        });
      }
    };

    // Add event listeners
    window.addEventListener('player_disconnected', handlePlayerDisconnected);
    window.addEventListener('player_reconnected', handlePlayerReconnected);
    window.addEventListener('ai_activated', handleAIActivated);
    window.addEventListener('reconnection_summary', handleReconnectionSummary);
    window.addEventListener('connection_status_update', handleConnectionStatusUpdate);

    // Cleanup
    return () => {
      window.removeEventListener('player_disconnected', handlePlayerDisconnected);
      window.removeEventListener('player_reconnected', handlePlayerReconnected);
      window.removeEventListener('ai_activated', handleAIActivated);
      window.removeEventListener('reconnection_summary', handleReconnectionSummary);
      window.removeEventListener('connection_status_update', handleConnectionStatusUpdate);
    };
  }, [addNotification]);

  return {
    notifications,
    addNotification,
    removeNotification,
    clearAll,
  };
};

export default useToastNotifications;