// frontend/src/hooks/useDisconnectedPlayers.js

import { useState, useEffect } from 'react';
import { networkService } from '../services/NetworkService';

/**
 * Hook to track disconnected players in the game
 * Listens to WebSocket events and maintains a list of players with AI takeover
 */
export function useDisconnectedPlayers(players = []) {
  const [disconnectedPlayers, setDisconnectedPlayers] = useState([]);

  useEffect(() => {
    // Initialize disconnected players based on is_bot flag
    const initialDisconnected = players
      .filter((player) => player.is_bot && player.original_is_bot === false)
      .map((player) => player.name);
    setDisconnectedPlayers(initialDisconnected);

    // Handle player disconnected event
    const handlePlayerDisconnected = (event) => {
      const { playerName, ai_activated } = event.detail;
      if (ai_activated) {
        setDisconnectedPlayers((prev) => {
          if (!prev.includes(playerName)) {
            return [...prev, playerName];
          }
          return prev;
        });
      }
    };

    // Handle player reconnected event
    const handlePlayerReconnected = (event) => {
      const { playerName } = event.detail;
      setDisconnectedPlayers((prev) =>
        prev.filter((name) => name !== playerName)
      );
    };

    // Listen to window events (bridged from NetworkService)
    window.addEventListener('player_disconnected', handlePlayerDisconnected);
    window.addEventListener('player_reconnected', handlePlayerReconnected);

    // Also listen directly to NetworkService for immediate updates
    networkService.addEventListener(
      'player_disconnected',
      handlePlayerDisconnected
    );
    networkService.addEventListener(
      'player_reconnected',
      handlePlayerReconnected
    );

    return () => {
      window.removeEventListener(
        'player_disconnected',
        handlePlayerDisconnected
      );
      window.removeEventListener('player_reconnected', handlePlayerReconnected);
      networkService.removeEventListener(
        'player_disconnected',
        handlePlayerDisconnected
      );
      networkService.removeEventListener(
        'player_reconnected',
        handlePlayerReconnected
      );
    };
  }, [players]);

  return disconnectedPlayers;
}

export default useDisconnectedPlayers;
