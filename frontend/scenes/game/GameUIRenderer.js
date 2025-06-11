// frontend/scenes/game/GameUIRenderer.js

import { Container, Text, TextStyle } from "pixi.js";
import { GameTextbox } from "../../components/GameTextbox.js";
import { GameButton } from "../../components/GameButton.js";

/**
 * Handles all UI rendering for the game
 * Separates presentation logic from game logic
 *
 * Responsibilities:
 * - Create and manage UI components
 * - Update UI based on game state
 * - Handle UI animations
 * - Manage layout
 */
export class GameUIRenderer extends Container {
  constructor(gameScene) {
    super();

    this.gameScene = gameScene;
    this.parentContainer = gameScene;

    // UI containers
    this.containers = {
      header: new Container(),
      main: new Container(),
      input: new Container(),
      footer: new Container(),
    };

    // UI components
    this.components = {
      statusText: null,
      handDisplay: null,
      inputBox: null,
      submitButton: null,
      phaseIndicator: null,
    };

    // Input state
    this.currentInputCallback = null;
    this.inputValidator = null;

    // Add self to parent
    gameScene.addChild(this);

    this.setupLayout();
  }

  /**
   * Initialize UI after all components are ready
   */
  async initialize(gameData) {
    // Now we can safely access stateManager
    this.stateManager = this.gameScene.stateManager;
    this.createComponents();
    console.log("UI components created");
  }

  /**
   * Set up container layout
   */
  setupLayout() {
    // Main layout
    this.layout = {
      width: "100%",
      height: "100%",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "flex-start",
      padding: 20,
      gap: 20,
    };

    // Header layout
    this.containers.header.layout = {
      width: "100%",
      height: "auto",
      flexDirection: "column",
      alignItems: "center",
      gap: 10,
    };

    // Main content layout
    this.containers.main.layout = {
      width: "100%",
      flex: 1,
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      gap: 20,
    };

    // Input layout
    this.containers.input.layout = {
      flexDirection: "row",
      gap: 8,
      alignItems: "center",
    };

    // Footer layout
    this.containers.footer.layout = {
      width: "100%",
      height: "auto",
      flexDirection: "row",
      justifyContent: "space-between",
      alignItems: "center",
    };

    // Add containers to self
    Object.values(this.containers).forEach((container) => {
      this.addChild(container);
    });
  }

  /**
   * Create UI components
   */
  createComponents() {
    // Status text
    this.components.statusText = new Text({
      text: `Game Room: ${this.stateManager.roomId}`,
      style: new TextStyle({
        fill: "#666666",
        fontSize: 14,
      }),
    });
    this.containers.header.addChild(this.components.statusText);

    // Phase indicator
    this.components.phaseIndicator = new Text({
      text: "",
      style: new TextStyle({
        fill: "#ffffff",
        fontSize: 20,
        fontWeight: "bold",
      }),
    });
    this.containers.header.addChild(this.components.phaseIndicator);

    // Input components
    this.components.inputBox = new GameTextbox({
      placeholder: "Your input",
      width: 300,
    });

    this.components.submitButton = new GameButton({
      label: "Enter",
      width: 80,
      onClick: () => this.handleSubmit(),
    });

    this.containers.input.addChild(
      this.components.inputBox.view,
      this.components.submitButton.view
    );

    // Hide input by default
    this.containers.input.visible = false;
  }

  // ===== PHASE UI METHODS =====

  /**
   * Show redeal phase UI
   */
  showRedealPhase() {
    this.updatePhaseIndicator("Redeal Check");
    this.clearMainContent();
  }

  /**
   * Show declaration phase UI
   */
  showDeclarationPhase() {
    this.updatePhaseIndicator("Declaration Phase");
    this.clearMainContent();

    // Show declaration progress
    const progressText = new Text({
      text: "Waiting for declarations...",
      style: new TextStyle({
        fill: "#ffffff",
        fontSize: 16,
      }),
    });
    this.containers.main.addChild(progressText);
  }

  /**
   * Show turn phase UI
   */
  showTurnPhase() {
    this.updatePhaseIndicator("Turn Phase");
    this.clearMainContent();
  }

  /**
   * Show scoring phase UI
   */
  showScoringPhase() {
    this.updatePhaseIndicator("Scoring");
    this.clearMainContent();
  }

  // ===== INPUT METHODS =====

  /**
   * Show input prompt
   */
  async showInput(prompt, validator = null) {
    return new Promise((resolve) => {
      console.log(`\n${prompt}`);

      this.containers.input.visible = true;
      this.components.inputBox.setText("");
      this.components.inputBox.focus();

      this.currentInputCallback = resolve;
      this.inputValidator = validator;
    });
  }

  /**
   * Show declaration input
   */
  showDeclarationInput(validOptions, callback) {
    // Could enhance this with buttons for each option
    this.showInput(
      `Enter declaration (${validOptions.join(", ")}):`,
      (value) => {
        const num = parseInt(value);
        if (isNaN(num)) {
          return { valid: false, message: "Please enter a number" };
        }
        if (!validOptions.includes(num)) {
          return {
            valid: false,
            message: `Choose from [${validOptions.join(", ")}]`,
          };
        }
        return { valid: true };
      }
    ).then((value) => {
      callback(parseInt(value));
    });
  }

  /**
   * Hide input
   */
  hideInput() {
    this.containers.input.visible = false;
    this.currentInputCallback = null;
    this.inputValidator = null;
  }

  /**
   * Handle submit button
   */
  handleSubmit() {
    if (!this.currentInputCallback) return;

    const value = this.components.inputBox.getText().trim();
    if (!value) return;

    // Validate if validator provided
    if (this.inputValidator) {
      const result = this.inputValidator(value);
      if (!result.valid) {
        this.showError(result.message);
        return;
      }
    }

    // Save callback BEFORE hiding input
    const callback = this.currentInputCallback;

    // Now hide and clear
    this.hideInput();

    // Call the saved callback
    callback(value);
  }

  // ===== DISPLAY METHODS =====

  /**
   * Display player's hand
   */
  displayHand(hand) {
    console.log("\n🃏 Your hand:");
    hand.forEach((card, i) => {
      console.log(`${i}: ${card}`);
    });

    // TODO: Create visual hand display
  }

  /**
   * Update declaration for a player
   */
  updateDeclaration(playerName, value) {
    // TODO: Update declaration display
    console.log(`${playerName} declared ${value}`);
  }

  /**
   * Show declaration summary
   */
  showDeclarationSummary(declarations) {
    console.log("\n📋 Declaration Summary:");
    Object.entries(declarations).forEach(([player, value]) => {
      console.log(`  ${player}: ${value} piles`);
    });
  }

  /**
   * Update phase indicator
   */
  updatePhaseIndicator(phaseName) {
    this.components.phaseIndicator.text = phaseName;
  }

  /**
   * Clear main content
   */
  clearMainContent() {
    this.containers.main.removeChildren();
  }

  // ===== FEEDBACK METHODS =====

  /**
   * Show error message
   */
  showError(message) {
    console.error(`❌ ${message}`);

    const errorText = new Text({
      text: message,
      style: new TextStyle({
        fill: "#ff0000",
        fontSize: 16,
      }),
    });
    errorText.position.set(10, 200);
    this.containers.main.addChild(errorText);

    // Remove after 3 seconds
    setTimeout(() => {
      if (errorText.parent) {
        errorText.destroy();
      }
    }, 3000);
  }

  /**
   * Show warning message
   */
  showWarning(message) {
    console.warn(`⚠️ ${message}`);
    // TODO: Show visual warning
  }

  /**
   * Show success message
   */
  showSuccess(message) {
    console.log(`✅ ${message}`);
    // TODO: Show visual success
  }

  /**
   * Show game over screen
   */
  showGameResults(data) {
    this.clearMainContent();
    this.updatePhaseIndicator("Game Over");

    const gameOverText = new Text({
      text:
        data.winners?.length > 0
          ? `🏆 Winner: ${data.winners.join(", ")}`
          : "🎮 Game Over!",
      style: new TextStyle({
        fill: "#00ff00",
        fontSize: 30,
        fontWeight: "bold",
      }),
    });

    this.containers.main.addChild(gameOverText);
  }

  // ===== CLEANUP =====

  /**
   * Destroy all UI components
   */
  destroy(options) {
    Object.values(this.containers).forEach((container) => {
      container.destroy({ children: true });
    });

    this.components = {};
    this.containers = {};

    super.destroy(options);
  }
}