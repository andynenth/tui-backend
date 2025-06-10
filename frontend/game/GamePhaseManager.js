// frontend/game/GamePhaseManager.js

import { EventEmitter } from "../network/core/EventEmitter.js";
import { DeclarationPhase } from './phases/DeclarationPhase.js';
import { TurnPhase } from './phases/TurnPhase.js';
import { ScoringPhase } from './phases/ScoringPhase.js';
import { RedealPhase } from './phases/RedealPhase.js';

export class GamePhaseManager extends EventEmitter {
  constructor(stateManager, socketManager, uiRenderer) {
    super();

    this.stateManager = stateManager;
    this.socketManager = socketManager;
    this.uiRenderer = uiRenderer;

    this.currentPhase = null;
    this.currentPhaseName = null;
    this.phases = new Map();

    // Create phase instances
    this.initializePhases();

    console.log("GamePhaseManager initialized");
  }

  /**
   * Initialize all phase instances
   */
  initializePhases() {
    // Create actual phase instances
    this.phases.set('declaration', new DeclarationPhase(
      this.stateManager, 
      this.socketManager, 
      this.uiRenderer
    ));
    
    this.phases.set('turn', new TurnPhase(
      this.stateManager, 
      this.socketManager, 
      this.uiRenderer
    ));
    
    this.phases.set('scoring', new ScoringPhase(
      this.stateManager, 
      this.socketManager, 
      this.uiRenderer
    ));
    
    this.phases.set('redeal', new RedealPhase(
      this.stateManager, 
      this.socketManager, 
      this.uiRenderer
    ));

    // Listen for phase completion events from phases
    this.phases.forEach((phase, name) => {
      phase.on('phaseComplete', (data) => {
        console.log(`📍 Phase ${name} completed, transitioning to ${data.nextPhase}`);
        this.transitionTo(data.nextPhase);
      });
    });
  }

  /**
   * Transition to a new phase
   */
  async transitionTo(phaseName) {
    console.log(`🔄 Transitioning to phase: ${phaseName}`);

    // Exit the previous phase if phase exists
    if (!this.phases.has(phaseName)) {
      console.error(`Unknown phase: ${phaseName}`);
      return;
    }

    const oldPhaseName = this.currentPhaseName;
    const newPhase = this.phases.get(phaseName);

    try {
      // Exit current phase
      if (this.currentPhase) {
        await this.currentPhase.exit();
      }

      // Update current phase
      this.currentPhase = newPhase;
      this.currentPhaseName = phaseName;

      // Enter new phase
      await newPhase.enter();

      // Emit phase change event
      this.emit("phaseChanged", {
        from: oldPhaseName,
        to: phaseName,
      });

      // Update state manager
      this.stateManager.currentPhase = phaseName;
    } catch (error) {
      console.error(`Error transitioning to phase ${phaseName}:`, error);
      this.emit("phaseError", { phase: phaseName, error });
    }
  }

  /**
   * Get current phase name
   */
  getCurrentPhase() {
    return this.currentPhaseName;
  }

  /**
   * Check if in specific phase
   */
  isInPhase(phaseName) {
    return this.currentPhaseName === phaseName;
  }

  /**
   * Handle user input - delegate to current phase
   */
  async handleUserInput(input) {
    if (this.currentPhase) {
      return await this.currentPhase.handleUserInput(input);
    }
    return false;
  }

  /**
   * Destroy
   */
  destroy() {
    // Exit current phase
    if (this.currentPhase) {
      this.currentPhase.exit();
    }

    // Destroy all phases
    this.phases.forEach(phase => {
      if (phase.destroy) phase.destroy();
    });

    this.phases.clear();
    this.removeAllListeners();
    
    console.log("GamePhaseManager destroyed");
  }
}