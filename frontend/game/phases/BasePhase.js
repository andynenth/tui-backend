// frontend/game/phases/BasePhase.js

import { EventEmitter } from "../../network/core/EventEmitter";

export class BasePhase extends EventEmitter {
  constructor(stateManager, socketManager, uiManager) {
    super();
    this.stateManager = stateManager;
    this.socketManager = socketManager;
    this.uiRenderer = uiManager;
    this.isActive = false;
    this.eventHandlers = new Map();
  }

  async enter() {
    this.isActive = true;
    this.registerEventHandlers();
    console.log(`Entering ${this.constructor.name}`);
  }

  async exit() {
    this.isActive = false;
    this.unregisterEventHandlers();
    console.log(`Exiting ${this.constructor.name}`);
  }

  /**
   * Register socket event handlers
   */
  registerEventHandlers() {
    // Override in subclasses
  }

  /**
   * Add event handler
   */
  addEventHandler(event, handler) {
    const boundHandler = handler.bind(this);
    this.eventHandlers.set(event, boundHandler);
    this.socketManager.on(event, boundHandler);
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
   * Complete this phase and request transition
   */
  completePhase(data = {}) {
    this.emit('phaseComplete', {
      phase: this.constructor.name,
      ...data
    });
  }

  /**
   * Handle user input
   */
  async handleUserInput(input) {
    if (!this.isActive) return false;
    return false; // Override in subclasses
  }
}