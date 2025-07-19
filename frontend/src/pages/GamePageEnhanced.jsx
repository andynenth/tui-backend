// frontend/src/pages/GamePageEnhanced.jsx

import React, { useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useApp } from '../contexts/AppContext';
import { useGame } from '../contexts/GameContext';
import useAutoReconnect from '../hooks/useAutoReconnect';
import GamePage from './GamePage';

/**
 * Enhanced GamePage with session storage and reconnection support
 */
const GamePageEnhanced = () => {
  const { roomId } = useParams();
  const navigate = useNavigate();
  const app = useApp();
  const game = useGame();
  const { createSession, updateSessionPhase, clearSession } = useAutoReconnect();

  // Create session on mount
  useEffect(() => {
    if (app.playerName && roomId) {
      createSession(roomId, app.playerName, game?.phase);
    }
  }, [app.playerName, roomId, createSession, game?.phase]);

  // Update session when phase changes
  useEffect(() => {
    if (game?.phase) {
      updateSessionPhase(game.phase);
    }
  }, [game?.phase, updateSessionPhase]);

  // Clear session on intentional leave
  const handleLeaveGame = useCallback(() => {
    clearSession();
    navigate('/lobby');
  }, [clearSession, navigate]);

  // Handle window close
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      // Most browsers don't show custom messages anymore
      e.preventDefault();
      e.returnValue = '';
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, []);

  // Pass through to original GamePage with leave handler
  return <GamePage onLeaveGame={handleLeaveGame} />;
};

export default GamePageEnhanced;