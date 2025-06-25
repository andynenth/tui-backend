// frontend/src/hooks/useGameState.js
// Enhanced for Phase 3 Task 3.2: Maintains legacy GameStateManager compatibility
// while preparing for service integration

import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { GameStateManager } from '../../game/GameStateManager.js';

/**
 * React hook for interfacing with existing GameStateManager
 * Provides state synchronization for React components
 * Enhanced to work alongside new service architecture
 */
export function useGameState(roomId, playerName, initialData) {
  const [gameState, setGameState] = useState(null);
  const [currentPhase, setCurrentPhase] = useState('INITIALIZATION');
  const [myHand, setMyHand] = useState([]);
  const [declarations, setDeclarations] = useState({});
  const [currentTurnPlays, setCurrentTurnPlays] = useState([]);
  const [scores, setScores] = useState({});
  const [isMyTurn, setIsMyTurn] = useState(false);
  
  const gameStateManagerRef = useRef(null);

  // Initialize GameStateManager
  useEffect(() => {
    if (!roomId || !playerName) return;

    const manager = new GameStateManager(roomId, playerName, initialData || {});
    gameStateManagerRef.current = manager;
    setGameState(manager);

    // Set up event listeners for state synchronization
    const handleHandUpdated = (data) => {
      setMyHand([...data.hand]);
    };

    const handleDeclarationAdded = (data) => {
      setDeclarations(prev => ({
        ...prev,
        [data.player]: data.value
      }));
    };

    const handleDeclarationsCleared = () => {
      setDeclarations({});
    };

    const handlePlayMade = (data) => {
      setCurrentTurnPlays(prev => [...prev, {
        player: data.player,
        cards: data.cards
      }]);
    };

    const handleTurnPlaysCleared = () => {
      setCurrentTurnPlays([]);
    };

    const handleScoreUpdated = (data) => {
      setScores(prev => ({
        ...prev,
        [data.player]: data.newScore
      }));
    };

    const handleTurnChanged = (data) => {
      setIsMyTurn(data.isMyTurn);
    };

    const handleNewRoundStarted = (data) => {
      setMyHand([...data.hand || []]);
      setDeclarations({});
      setCurrentTurnPlays([]);
    };

    // Register all event listeners
    manager.on('handUpdated', handleHandUpdated);
    manager.on('declarationAdded', handleDeclarationAdded);
    manager.on('declarationsCleared', handleDeclarationsCleared);
    manager.on('playMade', handlePlayMade);
    manager.on('turnPlaysCleared', handleTurnPlaysCleared);
    manager.on('scoreUpdated', handleScoreUpdated);
    manager.on('turnChanged', handleTurnChanged);
    manager.on('newRoundStarted', handleNewRoundStarted);

    // Initialize state from manager
    setMyHand([...manager.myHand]);
    setDeclarations({...manager.declarations});
    setCurrentTurnPlays([...manager.currentTurnPlays]);
    setScores({...manager.scores});
    setCurrentPhase(manager.currentPhase);

    // Cleanup
    return () => {
      manager.removeAllListeners();
    };
  }, [roomId, playerName, initialData]);

  // Memoized action methods
  const updateHand = useCallback((newHand) => {
    gameStateManagerRef.current?.updateHand(newHand);
  }, []);

  const addDeclaration = useCallback((playerName, value) => {
    gameStateManagerRef.current?.addDeclaration(playerName, value);
  }, []);

  const addTurnPlay = useCallback((playerName, cards) => {
    gameStateManagerRef.current?.addTurnPlay(playerName, cards);
  }, []);

  const updateScore = useCallback((playerName, newScore) => {
    gameStateManagerRef.current?.updateScore(playerName, newScore);
  }, []);

  const startNewTurn = useCallback((starterName) => {
    gameStateManagerRef.current?.startNewTurn(starterName);
  }, []);

  const startNewRound = useCallback((roundData) => {
    gameStateManagerRef.current?.startNewRound(roundData);
  }, []);

  const removeFromHand = useCallback((indices) => {
    return gameStateManagerRef.current?.removeFromHand(indices) || [];
  }, []);

  // Computed state - memoized for performance
  const isMyTurnToDeclare = useMemo(() => {
    return gameStateManagerRef.current?.isMyTurnToDeclare() || false;
  }, [declarations]);

  const areAllPlayersDeclarated = useMemo(() => {
    return gameStateManagerRef.current?.areAllPlayersDeclarated() || false;
  }, [declarations]);

  const isMyTurnToPlay = useMemo(() => {
    return gameStateManagerRef.current?.isMyTurnToPlay() || false;
  }, [currentTurnPlays]);

  const getValidDeclarationOptions = useCallback((isLastPlayer) => {
    return gameStateManagerRef.current?.getValidDeclarationOptions(isLastPlayer) || [];
  }, [myHand, declarations]);

  return {
    // State
    gameState: gameStateManagerRef.current,
    currentPhase,
    myHand,
    declarations,
    currentTurnPlays,
    scores,
    isMyTurn,
    
    // Actions
    updateHand,
    addDeclaration,
    addTurnPlay,
    updateScore,
    startNewTurn,
    startNewRound,
    removeFromHand,
    
    // Computed state
    isMyTurnToDeclare,
    areAllPlayersDeclarated,
    isMyTurnToPlay,
    getValidDeclarationOptions,
    
    // Direct access to manager (for advanced usage)
    manager: gameStateManagerRef.current
  };
}