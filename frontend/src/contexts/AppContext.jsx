// frontend/src/contexts/AppContext.jsx

import React, { createContext, useContext, useState, useEffect } from 'react';

const AppContext = createContext(null);

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};

export const AppProvider = ({ children }) => {
  const [currentScene, setCurrentScene] = useState('start');
  const [playerName, setPlayerName] = useState('');
  const [currentRoomId, setCurrentRoomId] = useState(null);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [appError, setAppError] = useState(null);

  // Load persisted data on mount
  useEffect(() => {
    const savedPlayerName = localStorage.getItem('playerName');
    if (savedPlayerName) {
      setPlayerName(savedPlayerName);
    }

    const savedRoomId = localStorage.getItem('currentRoomId');
    if (savedRoomId) {
      setCurrentRoomId(savedRoomId);
      // Consider if we should auto-navigate to room scene
    }
  }, []);

  // Persist player name
  useEffect(() => {
    if (playerName) {
      localStorage.setItem('playerName', playerName);
    } else {
      localStorage.removeItem('playerName');
    }
  }, [playerName]);

  // Persist room ID
  useEffect(() => {
    if (currentRoomId) {
      localStorage.setItem('currentRoomId', currentRoomId);
    } else {
      localStorage.removeItem('currentRoomId');
    }
  }, [currentRoomId]);

  // Scene navigation
  const navigateToScene = async (sceneName, options = {}) => {
    setIsTransitioning(true);
    setAppError(null);

    try {
      // Scene-specific logic
      switch (sceneName) {
        case 'start':
          setCurrentRoomId(null);
          break;

        case 'lobby':
          if (!playerName) {
            throw new Error('Player name required for lobby');
          }
          break;

        case 'room':
          if (!playerName || !options.roomId) {
            throw new Error('Player name and room ID required for room');
          }
          setCurrentRoomId(options.roomId);
          break;

        case 'game':
          if (!playerName || !currentRoomId) {
            throw new Error('Player name and room ID required for game');
          }
          break;

        default:
          throw new Error(`Unknown scene: ${sceneName}`);
      }

      setCurrentScene(sceneName);
    } catch (error) {
      console.error('Scene navigation failed:', error);
      setAppError(error);
    } finally {
      setIsTransitioning(false);
    }
  };

  // Convenience navigation methods
  const goToStart = () => navigateToScene('start');
  const goToLobby = () => navigateToScene('lobby');
  const goToRoom = (roomId) => navigateToScene('room', { roomId });
  const goToGame = () => navigateToScene('game');

  // Player management
  const updatePlayerName = (name) => {
    const trimmedName = name.trim();
    if (trimmedName.length < 2) {
      throw new Error('Player name must be at least 2 characters');
    }
    if (trimmedName.length > 20) {
      throw new Error('Player name must be less than 20 characters');
    }
    setPlayerName(trimmedName);
  };

  // Room management
  const joinRoom = async (roomId) => {
    if (!playerName) {
      throw new Error('Player name required to join room');
    }
    await navigateToScene('room', { roomId });
  };

  const leaveRoom = () => {
    setCurrentRoomId(null);
    navigateToScene('lobby');
  };

  // Error handling
  const clearError = () => {
    setAppError(null);
  };

  // App state validation
  const canNavigateToScene = (sceneName) => {
    switch (sceneName) {
      case 'start':
        return true;
      case 'lobby':
        return !!playerName;
      case 'room':
        return !!playerName && !!currentRoomId;
      case 'game':
        return !!playerName && !!currentRoomId;
      default:
        return false;
    }
  };

  const value = {
    // Current state
    currentScene,
    playerName,
    currentRoomId,
    isTransitioning,
    appError,

    // Navigation
    navigateToScene,
    goToStart,
    goToLobby,
    goToRoom,
    goToGame,

    // Player management
    updatePlayerName,

    // Room management
    joinRoom,
    leaveRoom,

    // Utilities
    clearError,
    canNavigateToScene,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};
