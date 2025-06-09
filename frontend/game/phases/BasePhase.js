// frontend/game/phases/BasePhase.js

/**
 * Abstract base class for all game phases
 * Follows the State pattern for clean phase management
 * 
 * Each phase is responsible for:
 * - Handling its own UI state
 * - Processing relevant socket events
 * - Managing user input
 * - Determining when to transition to the next phase
 */
export class BasePhase {
  constructor(stateManager, socketManager, uiManager) {
    this.stateManager = stateManager;
    this.socketManager = socketManager;
    this.uiManager = uiManager;
    this.isActive = false;
    this.eventHandlers = new Map();
  }

  /**
   * Called when entering this phase
   * Override to set up phase-specific state and listeners
   */
  async enter() {
    this.isActive = true;
    console.log(`📍 Entering ${this.constructor.name}`);
    this.registerEventHandlers();
  }

  /**
   * Called when exiting this phase
   * Override to clean up listeners and state
   */
  async exit() {
    console.log(`📤 Exiting ${this.constructor.name}`);
    this.isActive = false;
    this.unregisterEventHandlers();
  }

  /**
   * Register socket event handlers
   * Override to add phase-specific handlers
   */
  registerEventHandlers() {
    // Base implementation - override in subclasses
  }

  /**
   * Unregister all event handlers
   */
  unregisterEventHandlers() {
    this.eventHandlers.forEach((handler, event) => {
      this.socketManager.off(event, handler);
    });
    this.eventHandlers.clear();
  }

  /**
   * Helper to register an event handler
   */
  addEventHandler(event, handler) {
    const boundHandler = handler.bind(this);
    this.eventHandlers.set(event, boundHandler);
    this.socketManager.on(event, boundHandler);
  }

  /**
   * Handle user input
   * Override in subclasses for phase-specific input handling
   */
  async handleUserInput(input) {
    if (!this.isActive) {
      console.warn(`${this.constructor.name} received input while inactive`);
      return false;
    }
    // Override in subclasses
    return false;
  }

  /**
   * Check if this phase is complete
   * Override to implement phase completion logic
   */
  isPhaseComplete() {
    return false;
  }

  /**
   * Get the next phase name
   * Override to specify phase transitions
   */
  getNextPhase() {
    return null;
  }

  /**
   * Emit phase completion event
   */
  completePhase(data = {}) {
    if (!this.isActive) return;
    
    const nextPhase = this.getNextPhase();
    this.stateManager.emit('phaseComplete', {
      currentPhase: this.constructor.name,
      nextPhase,
      ...data
    });
  }
}