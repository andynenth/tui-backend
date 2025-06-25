// frontend/src/hooks/usePhaseManager.js
// Enhanced for Phase 3 Task 3.2: Maintains legacy phase management
// while working alongside new service architecture

import { useState, useEffect, useRef, useCallback } from 'react';
import { GamePhaseManager } from '../../game/GamePhaseManager.js';

/**
 * React hook for interfacing with existing GamePhaseManager
 * Provides phase management and transitions for React components
 * Enhanced to coexist with new service-based phase management
 */
export function usePhaseManager(stateManager, socketManager, uiRenderer) {
  const [currentPhase, setCurrentPhase] = useState(null);
  const [currentPhaseName, setCurrentPhaseName] = useState('waiting');
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [transitionError, setTransitionError] = useState(null);
  
  const phaseManagerRef = useRef(null);

  // Initialize GamePhaseManager
  useEffect(() => {
    if (!stateManager || !socketManager) return;
    
    // Store current refs to check if they actually changed
    const currentStateManager = phaseManagerRef.current?.stateManager;
    const currentSocketManager = phaseManagerRef.current?.socketManager;
    
    // If we already have a manager with the same instances, don't recreate
    if (phaseManagerRef.current && 
        currentStateManager === stateManager && 
        currentSocketManager === socketManager) {
      return;
    }

    // Clean up existing manager first
    if (phaseManagerRef.current) {
      console.log('🧹 Cleaning up existing GamePhaseManager');
      phaseManagerRef.current.destroy();
    }

    console.log('🚀 Creating GamePhaseManager instance');
    const manager = new GamePhaseManager(stateManager, socketManager, uiRenderer);
    phaseManagerRef.current = manager;

    // Set up event listeners for phase changes
    const handlePhaseChanged = (data) => {
      setCurrentPhaseName(data.to);
      setCurrentPhase(manager.getCurrentPhase());
      setIsTransitioning(false);
      setTransitionError(null);
      console.log(`React hook: Phase changed from ${data.from} to ${data.to}`);
    };

    const handleGameComplete = (data) => {
      console.log('Game completed:', data);
      // Game completion can be handled by parent components
    };

    // Register event listeners
    manager.on('phaseChanged', handlePhaseChanged);
    manager.on('gameComplete', handleGameComplete);

    // Initialize current state
    setCurrentPhase(manager.getCurrentPhase());
    setCurrentPhaseName(manager.getCurrentPhaseName());

    // Cleanup
    return () => {
      console.log('🧹 Destroying GamePhaseManager instance');
      if (phaseManagerRef.current === manager) {
        manager.destroy();
        phaseManagerRef.current = null;
      }
    };
  }, [stateManager, socketManager, uiRenderer]);

  // Transition to a new phase
  const transitionTo = useCallback(async (phaseName) => {
    if (!phaseManagerRef.current) return false;

    setIsTransitioning(true);
    setTransitionError(null);

    try {
      const success = await phaseManagerRef.current.transitionTo(phaseName);
      if (!success) {
        setTransitionError(`Failed to transition to ${phaseName}`);
      }
      return success;
    } catch (error) {
      setTransitionError(error.message);
      setIsTransitioning(false);
      return false;
    }
  }, []);

  // Auto-transition based on game state
  const autoTransition = useCallback(async () => {
    if (!phaseManagerRef.current) return;

    try {
      await phaseManagerRef.current.autoTransition();
    } catch (error) {
      console.error('Auto-transition failed:', error);
      setTransitionError(error.message);
    }
  }, []);

  // Handle user input for current phase
  const handleUserInput = useCallback(async (input) => {
    if (!phaseManagerRef.current) return false;

    try {
      return await phaseManagerRef.current.handleUserInput(input);
    } catch (error) {
      console.error('Failed to handle user input:', error);
      return false;
    }
  }, []);

  // Handle socket events for current phase
  const handleSocketEvent = useCallback(async (event, data) => {
    if (!phaseManagerRef.current) return false;

    try {
      return await phaseManagerRef.current.handleSocketEvent(event, data);
    } catch (error) {
      console.error('Failed to handle socket event:', error);
      return false;
    }
  }, []);

  // Reset phase manager to waiting state
  const reset = useCallback(async () => {
    if (!phaseManagerRef.current) return;

    setIsTransitioning(true);
    try {
      await phaseManagerRef.current.reset();
    } catch (error) {
      console.error('Failed to reset phase manager:', error);
      setTransitionError(error.message);
    } finally {
      setIsTransitioning(false);
    }
  }, []);

  // Handle phase completion
  const onPhaseComplete = useCallback(async (phaseData) => {
    if (!phaseManagerRef.current) return;

    try {
      await phaseManagerRef.current.onPhaseComplete(phaseData);
    } catch (error) {
      console.error('Failed to handle phase completion:', error);
      setTransitionError(error.message);
    }
  }, []);

  // Check if specific phase is active
  const isPhaseActive = useCallback((phaseName) => {
    return currentPhaseName === phaseName;
  }, [currentPhaseName]);

  // Get available phase actions for current phase
  const getPhaseActions = useCallback(() => {
    if (!currentPhase || !currentPhase.getAvailableActions) {
      return [];
    }
    return currentPhase.getAvailableActions();
  }, [currentPhase]);

  return {
    // State
    currentPhase,
    currentPhaseName,
    isTransitioning,
    transitionError,
    
    // Actions
    transitionTo,
    autoTransition,
    handleUserInput,
    handleSocketEvent,
    reset,
    onPhaseComplete,
    
    // Utilities
    isPhaseActive,
    getPhaseActions,
    
    // Direct access to manager (for advanced usage)
    manager: phaseManagerRef.current
  };
}