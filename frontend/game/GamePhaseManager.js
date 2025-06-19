// frontend/game/GamePhaseManager.js

import { EventEmitter } from "../network/core/EventEmitter.js";

// Import all phases
import { RedealPhase } from "./phases/RedealPhase.js";
import { DeclarationPhase } from "./phases/DeclarationPhase.js";
import { TurnPhase } from "./phases/TurnPhase.js";
import { ScoringPhase } from "./phases/ScoringPhase.js";

/**
 * Game Phase Manager
 * Manages phase transitions and phase lifecycle
 */
export class GamePhaseManager extends EventEmitter {
  constructor(stateManager, socketManager, uiRenderer) {
    super();

    this.stateManager = stateManager;
    this.socketManager = socketManager;
    this.uiRenderer = uiRenderer;

    this.currentPhase = null;
    this.phases = {};

    this.initializePhases();

    console.log("GamePhaseManager initialized");
  }

  /**
   * Initialize all available phases
   */
  initializePhases() {
    // ✅ Register all phases including RedealPhase
    this.phases = {
      waiting: null, // Simple waiting state
      redeal: new RedealPhase(
        this.stateManager,
        this.socketManager,
        this.uiRenderer
      ),
      declaration: new DeclarationPhase(
        this.stateManager,
        this.socketManager,
        this.uiRenderer
      ),
      turn: new TurnPhase(
        this.stateManager,
        this.socketManager,
        this.uiRenderer
      ),
      scoring: new ScoringPhase(
        this.stateManager,
        this.socketManager,
        this.uiRenderer
      ),
    };

    console.log("✅ Initialized phases:", Object.keys(this.phases));
  }

  /**
   * Transition to a new phase
   */
  async transitionTo(phaseName) {
    console.log(
      `🔄 Phase transition requested: ${
        this.currentPhase?.constructor.name || "null"
      } → ${phaseName}`
    );

    // Add debug logging
    if (this.currentPhase) {
      console.log("Current phase details:", {
        constructorName: this.currentPhase.constructor.name,
        phase: this.currentPhase,
        isRedealPhase: this.currentPhase instanceof RedealPhase,
      });
    }

    // Validate phase exists
    if (phaseName !== "waiting" && !this.phases[phaseName]) {
      console.error(`❌ Unknown phase: ${phaseName}`);
      return false;
    }

    try {
      // Exit current phase
      if (this.currentPhase) {
        console.log(`🚪 Exiting phase: ${this.currentPhase.constructor.name}`);
        await this.currentPhase.exit();
      }

      const oldPhase = this.currentPhase;
      const oldPhaseName = oldPhase?.name || "waiting";

      // Set new phase
      if (phaseName === "waiting") {
        this.currentPhase = null;
        console.log("⏳ Entered waiting state");
      } else {
        this.currentPhase = this.phases[phaseName];
        console.log(`🚪 Entering phase: ${this.currentPhase.constructor.name}`);
        await this.currentPhase.enter();
      }

      // Single emission with consistent naming
      this.emit("phaseChanged", {
        from: oldPhaseName,
        to: phaseName,
      });

      console.log(
        `✅ Phase transition complete: ${oldPhaseName} → ${phaseName}`
      );

      return true;
    } catch (error) {
      console.error(`❌ Phase transition failed:`, error);
      console.error(error.stack);

      // Try to recover to waiting state
      this.currentPhase = null;
      return false;
    }
  }

  /**
   * Get current phase info
   */
  getCurrentPhase() {
    return this.currentPhase;
  }

  /**
   * Get current phase name
   */
  getCurrentPhaseName() {
    return (
      this.currentPhase?.constructor.name.replace("Phase", "").toLowerCase() ||
      "waiting"
    );
  }

  /**
   * Handle user input - forward to current phase
   */
  async handleUserInput(input) {
    if (this.currentPhase && this.currentPhase.handleUserInput) {
      return await this.currentPhase.handleUserInput(input);
    }
    return false;
  }

  /**
   * Handle socket events - forward to current phase
   */
  async handleSocketEvent(event, data) {
    if (this.currentPhase && this.currentPhase.handleSocketEvent) {
      return await this.currentPhase.handleSocketEvent(event, data);
    }
    return false;
  }

  /**
   * Force transition based on game state
   */
  async autoTransition() {
    // Auto-transition logic based on game state
    if (!this.currentPhase) {
      // Start with appropriate phase based on game state
      const gameState = this.stateManager;

      if (gameState.needsRedeal || this.checkForWeakHands()) {
        await this.transitionTo("redeal");
      } else if (this.allPlayersDeclaration()) {
        await this.transitionTo("turn");
      } else {
        await this.transitionTo("declaration");
      }
    }
  }

  /**
   * Check if any players have weak hands
   */
  checkForWeakHands() {
    // Check our own hand
    if (this.stateManager.myHand) {
      const hasStrongPiece = this.stateManager.myHand.some((card) => {
        const match = card.match(/\((\d+)\)/);
        return match && parseInt(match[1]) > 9;
      });

      if (!hasStrongPiece) {
        console.log("🔍 Detected weak hand, redeal needed");
        return true;
      }
    }

    return false;
  }

  /**
   * Check if all players have declared
   */
  allPlayersDeclaration() {
    const declarations = this.stateManager.declarations;
    const players = this.stateManager.players;

    return players.every(
      (player) =>
        declarations[player.name] !== null &&
        declarations[player.name] !== undefined
    );
  }

  /**
   * Handle phase completion
   */
  async onPhaseComplete(phaseData) {
    console.log("🎯 Phase complete:", phaseData);

    const currentPhaseName = this.getCurrentPhaseName();

    // Auto-transition to next phase
    switch (currentPhaseName) {
      case "redeal":
        await this.transitionTo("declaration");
        break;
      case "declaration":
        await this.transitionTo("turn");
        break;
      case "turn":
        // Check if round is complete
        if (phaseData.roundComplete) {
          await this.transitionTo("scoring");
        } else {
          // Stay in turn phase for next turn
        }
        break;
      case "scoring":
        // Check if game is complete
        if (phaseData.gameComplete) {
          this.emit("gameComplete", phaseData);
        } else {
          await this.transitionTo("redeal"); // Next round
        }
        break;
    }
  }

  /**
   * Emergency reset to waiting state
   */
  async reset() {
    console.log("🔄 Resetting phase manager");

    if (this.currentPhase) {
      try {
        await this.currentPhase.exit();
      } catch (error) {
        console.error("Error exiting phase during reset:", error);
      }
    }

    this.currentPhase = null;
    this.emit("phaseChanged", { from: "unknown", to: "waiting" });
  }

  /**
   * Clean up resources
   */
  destroy() {
    console.log("🧹 Destroying GamePhaseManager");

    // Exit current phase
    if (this.currentPhase) {
      this.currentPhase
        .exit()
        .catch((err) => console.error("Error during phase cleanup:", err));
    }

    // Clear all phases
    Object.values(this.phases).forEach((phase) => {
      if (phase && phase.destroy) {
        phase.destroy();
      }
    });

    this.phases = {};
    this.currentPhase = null;

    // Clear event listeners
    this.clear();
  }
}
