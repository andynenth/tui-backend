// frontend/game/GamePhaseManager.js

import { EventEmitter } from "../network/core/EventEmitter.js";

/**
 * Manages game phase transitions and phase lifecycle
 *
 * Responsibilities:
 * - Track current game phase
 * - Handle phase transitions
 * - Manage phase instances
 * - Emit phase change events
 */
export class GamePhaseManager extends EventEmitter {
  constructor(stateManager, socketManager, uiRenderer) {
    super();

    this.stateManager = stateManager;
    this.socketManager = socketManager;
    this.uiRenderer = uiRenderer;

    this.currentPhase = null;
    this.currentPhaseName = null;
    this.phases = new Map();

    // Register available phases
    this.registerPhases();

    console.log("GamePhaseManager initialized");
  }

  /**
   * Register all available game phases
   */
  registerPhases() {
    // For now, we'll use simple phase objects
    // Later these can be replaced with actual phase classes

    this.phases.set("waiting", {
      name: "waiting",
      enter: () => {
        console.log("⏳ Entering waiting phase");
        this.uiRenderer.updatePhaseIndicator("Waiting...");
      },
      exit: () => {
        console.log("Exiting waiting phase");
      },
    });

    this.phases.set("redeal", {
      name: "redeal",
      enter: () => {
        console.log("🔄 Entering redeal phase");
        this.uiRenderer.showRedealPhase();
      },
      exit: () => {
        console.log("Exiting redeal phase");
      },
    });

    this.phases.set("declaration", {
      name: "declaration",
      enter: () => {
        console.log("📣 Entering declaration phase");
        this.uiRenderer.showDeclarationPhase();

        // Check if it's our turn to declare (we might be the starter)
        if (this.stateManager.starter === this.stateManager.playerName) {
          console.log("🎯 You're the starter - your turn to declare!");

          // Give a small delay for UI to update
          setTimeout(() => {
            // Find the event handler and prompt for declaration
            const gameScene = this.uiRenderer.gameScene;
            if (gameScene && gameScene.eventHandler) {
              gameScene.eventHandler.promptForDeclaration();
            }
          }, 500);
        } else {
          console.log(
            `⏳ Waiting for ${this.stateManager.starter} to declare first...`
          );
        }
      },
      exit: () => {
        console.log("Exiting declaration phase");
        // Hide any input UI
        this.uiRenderer.hideInput();
      },
    });

    this.phases.set("turn", {
      name: "turn",
      enter: () => {
        console.log("🎮 Entering turn phase");
        this.uiRenderer.showTurnPhase();
      },
      exit: () => {
        console.log("Exiting turn phase");
      },
    });

    this.phases.set("scoring", {
      name: "scoring",
      enter: () => {
        console.log("📊 Entering scoring phase");
        this.uiRenderer.showScoringPhase();
      },
      exit: () => {
        console.log("Exiting scoring phase");
      },
    });
  }

  /**
   * Transition to a new phase
   */
  async transitionTo(phaseName) {
    console.log(`🔄 Transitioning to phase: ${phaseName}`);

    // Check if phase exists
    if (!this.phases.has(phaseName)) {
      console.error(`Unknown phase: ${phaseName}`);
      return;
    }

    const oldPhaseName = this.currentPhaseName;
    const newPhase = this.phases.get(phaseName);

    try {
      // Exit current phase
      if (this.currentPhase && this.currentPhase.exit) {
        await this.currentPhase.exit();
      }

      // Update current phase
      this.currentPhase = newPhase;
      this.currentPhaseName = phaseName;

      // Enter new phase
      if (newPhase.enter) {
        await newPhase.enter();
      }

      // Emit phase change event
      this.emit("phaseChanged", {
        from: oldPhaseName,
        to: phaseName,
      });

      // Update state manager
      this.stateManager.currentPhase = phaseName;
    } catch (error) {
      console.error(`Error transitioning to phase ${phaseName}:`, error);
      // Emit error event
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
   * Handle input for current phase
   */
  async handleInput(input) {
    if (this.currentPhase && this.currentPhase.handleInput) {
      return await this.currentPhase.handleInput(input);
    }
    console.warn("Current phase does not handle input");
  }

  /**
   * Handle socket event for current phase
   */
  async handleSocketEvent(event, data) {
    if (this.currentPhase && this.currentPhase.handleSocketEvent) {
      return await this.currentPhase.handleSocketEvent(event, data);
    }
    // Phase doesn't handle this event, that's ok
  }

  /**
   * Clean up
   */
  destroy() {
    // Exit current phase
    if (this.currentPhase && this.currentPhase.exit) {
      this.currentPhase.exit();
    }

    // Clear references
    this.phases.clear();
    this.currentPhase = null;
    this.currentPhaseName = null;

    // Remove all listeners
    this.removeAllListeners();

    console.log("GamePhaseManager destroyed");
  }
}
