// frontend/game/phases/BasePhase.js

/**
 * Base Phase Abstract Class
 * All game phases should extend this class
 */
export class BasePhase {
  constructor(stateManager, socketManager, uiRenderer) {
    this.stateManager = stateManager;
    this.socketManager = socketManager;
    this.uiRenderer = uiRenderer;
    
    this.isActive = false;
    this.name = this.constructor.name.replace('Phase', '').toLowerCase();
    this.eventHandlers = {};
  }

  /**
   * Enter this phase
   */
  async enter() {
    this.isActive = true;
    console.log(`🔸 Entering ${this.constructor.name}`);
    
    // Register event handlers
    this.registerEventHandlers();
    
    // Update UI
    if (this.uiRenderer) {
      this.uiRenderer.updatePhaseIndicator(this.getPhaseDisplayName());
    }
  }

  /**
   * Exit this phase
   */
  async exit() {
    console.log(`🔹 Exiting ${this.constructor.name}`);
    
    this.isActive = false;
    
    // Unregister event handlers
    this.unregisterEventHandlers();
    
    // Hide any phase-specific UI
    if (this.uiRenderer) {
      this.uiRenderer.hideInput();
    }
  }

  /**
   * Register socket event handlers for this phase
   * Override in subclasses
   */
  registerEventHandlers() {
    // Override in subclasses
  }

  /**
   * Unregister socket event handlers
   */
  unregisterEventHandlers() {
    Object.entries(this.eventHandlers).forEach(([event, handler]) => {
      this.socketManager.off(event, handler);
    });
    this.eventHandlers = {};
  }

  /**
   * Add an event handler (with automatic cleanup)
   */
  addEventHandler(event, handler) {
    const boundHandler = handler.bind(this);
    this.eventHandlers[event] = boundHandler;
    this.socketManager.on(event, boundHandler);
  }

  /**
   * Handle user input
   * Override in subclasses
   */
  async handleUserInput(input) {
    if (!this.isActive) {
      console.log(`⚠️ Input ignored - ${this.constructor.name} not active`);
      return false;
    }
    
    // Override in subclasses
    return false;
  }

  /**
   * Handle socket events
   * Override in subclasses
   */
  async handleSocketEvent(event, data) {
    if (!this.isActive) {
      console.log(`⚠️ Socket event ignored - ${this.constructor.name} not active`);
      return false;
    }
    
    // Override in subclasses
    return false;
  }

  /**
   * Complete this phase and move to next
   */
  completePhase(data = {}) {
    console.log(`✅ ${this.constructor.name} complete`);
    
    if (this.stateManager) {
      this.stateManager.emit('phaseComplete', {
        phase: this.name,
        nextPhase: this.getNextPhase(),
        ...data
      });
    }
  }

  /**
   * Get next phase name
   * Override in subclasses
   */
  getNextPhase() {
    return null; // Override in subclasses
  }

  /**
   * Get display name for this phase
   */
  getPhaseDisplayName() {
    return this.constructor.name.replace('Phase', ' Phase');
  }

  /**
   * Show error message
   */
  showError(message) {
    console.error(`❌ ${this.constructor.name}: ${message}`);
    if (this.uiRenderer) {
      this.uiRenderer.showError(message);
    }
  }

  /**
   * Show success message
   */
  showSuccess(message) {
    console.log(`✅ ${this.constructor.name}: ${message}`);
    if (this.uiRenderer) {
      this.uiRenderer.showSuccess(message);
    }
  }

  /**
   * Show warning message
   */
  showWarning(message) {
    console.warn(`⚠️ ${this.constructor.name}: ${message}`);
    if (this.uiRenderer) {
      this.uiRenderer.showWarning(message);
    }
  }

  /**
   * Clean up resources
   */
  destroy() {
    this.unregisterEventHandlers();
    this.isActive = false;
  }
}