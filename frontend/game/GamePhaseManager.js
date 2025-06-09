// frontend/game/GamePhaseManager.js

import { BasePhase } from './phases/BasePhase.js';
import { RedealPhase } from './phases/RedealPhase.js';
import { DeclarationPhase } from './phases/DeclarationPhase.js';
import { TurnPhase } from './phases/TurnPhase.js';
import { ScoringPhase } from './phases/ScoringPhase.js';

/**
 * Manages game phase transitions
 * Implements the State pattern for game flow
 * 
 * Responsibilities:
 * - Create and manage phase instances
 * - Handle phase transitions
 * - Ensure proper cleanup between phases
 * - Provide phase history for debugging
 */
export class GamePhaseManager {
  constructor(stateManager, socketManager, uiManager) {
    this.stateManager = stateManager;
    this.socketManager = socketManager;
    this.uiManager = uiManager;
    
    // Current phase instance
    this.currentPhase = null;
    
    // Phase history for debugging
    this.phaseHistory = [];
    
    // Available phases
    this.phases = {
      'redeal': RedealPhase,
      'declaration': DeclarationPhase,
      'turn': TurnPhase,
      'scoring': ScoringPhase
    };
    
    // Phase transition map
    this.transitions = {
      'initialization': 'redeal',
      'redeal': 'declaration',
      'declaration': 'turn',
      'turn': 'scoring',
      'scoring': 'redeal'  // Next round
    };
    
    // Listen for phase completion events
    this.stateManager.on('phaseComplete', this.handlePhaseComplete.bind(this));
    
    // Listen for game events that trigger phase changes
    this.setupGameEventListeners();
  }

  /**
   * Set up listeners for game events that trigger phase changes
   */
  setupGameEventListeners() {
    // When all players declare, move to turn phase
    this.stateManager.on('allPlayersDeclarated', () => {
      if (this.currentPhase?.constructor.name === 'DeclarationPhase') {
        this.transitionTo('turn');
      }
    });
    
    // When round scoring is complete, check for game over or new round
    this.stateManager.on('roundScoringComplete', (data) => {
      if (data.gameOver) {
        this.endGame(data);
      } else {
        // Prepare for next round
        setTimeout(() => {
          this.transitionTo('redeal');
        }, 2000);
      }
    });
  }

  /**
   * Start the game flow
   */
  async start() {
    console.log('🎮 Starting game phase manager');
    
    // Start with redeal check
    await this.transitionTo('redeal');
  }

  /**
   * Transition to a new phase
   */
  async transitionTo(phaseName) {
    console.log(`🔄 Transitioning to phase: ${phaseName}`);
    
    // Exit current phase if exists
    if (this.currentPhase) {
      try {
        await this.currentPhase.exit();
      } catch (error) {
        console.error('Error exiting phase:', error);
      }
    }
    
    // Create new phase instance
    const PhaseClass = this.phases[phaseName];
    if (!PhaseClass) {
      console.error(`Unknown phase: ${phaseName}`);
      return;
    }
    
    try {
      this.currentPhase = new PhaseClass(
        this.stateManager,
        this.socketManager,
        this.uiManager
      );
      
      // Update state manager
      this.stateManager.setPhase(phaseName);
      
      // Record in history
      this.phaseHistory.push({
        phase: phaseName,
        timestamp: Date.now()
      });
      
      // Enter new phase
      await this.currentPhase.enter();
      
    } catch (error) {
      console.error(`Error entering phase ${phaseName}:`, error);
      // TODO: Handle phase transition errors
    }
  }

  /**
   * Handle phase completion events
   */
  handlePhaseComplete(data) {
    console.log('📍 Phase complete:', data);
    
    if (data.nextPhase) {
      this.transitionTo(data.nextPhase);
    } else {
      // Use default transition map
      const currentPhaseName = this.getCurrentPhaseName();
      const nextPhase = this.transitions[currentPhaseName];
      
      if (nextPhase) {
        this.transitionTo(nextPhase);
      } else {
        console.warn('No next phase defined for:', currentPhaseName);
      }
    }
  }

  /**
   * Get current phase name
   */
  getCurrentPhaseName() {
    if (!this.currentPhase) return 'none';
    
    // Convert class name to phase key
    const className = this.currentPhase.constructor.name;
    return className.replace('Phase', '').toLowerCase();
  }

  /**
   * Handle user input
   */
  async handleUserInput(input) {
    if (!this.currentPhase) {
      console.warn('No active phase to handle input');
      return false;
    }
    
    return await this.currentPhase.handleUserInput(input);
  }

  /**
   * Force a phase transition (for testing/debugging)
   */
  async forceTransition(phaseName) {
    console.warn(`⚠️ Forcing transition to ${phaseName}`);
    await this.transitionTo(phaseName);
  }

  /**
   * End the game
   */
  endGame(data) {
    console.log('🏁 Game ended:', data);
    
    // Clean up current phase
    if (this.currentPhase) {
      this.currentPhase.exit();
      this.currentPhase = null;
    }
    
    // Notify UI
    this.uiManager.showGameOver(data);
    
    // Emit game over event
    this.stateManager.emit('gameEnded', data);
  }

  /**
   * Get phase history for debugging
   */
  getPhaseHistory() {
    return this.phaseHistory.map(entry => ({
      ...entry,
      duration: entry.timestamp - (this.phaseHistory[this.phaseHistory.indexOf(entry) - 1]?.timestamp || entry.timestamp)
    }));
  }

  /**
   * Reset for new round
   */
  resetForNewRound(roundData) {
    // Let state manager handle the reset
    this.stateManager.resetForNewRound(roundData);
    
    // Clear phase history for new round
    this.phaseHistory = [];
    
    // Start new round flow
    this.start();
  }

  /**
   * Clean up resources
   */
  destroy() {
    if (this.currentPhase) {
      this.currentPhase.exit();
      this.currentPhase = null;
    }
    
    // Remove listeners
    this.stateManager.off('phaseComplete', this.handlePhaseComplete.bind(this));
    this.stateManager.off('allPlayersDeclarated');
    this.stateManager.off('roundScoringComplete');
    
    this.phaseHistory = [];
  }
}