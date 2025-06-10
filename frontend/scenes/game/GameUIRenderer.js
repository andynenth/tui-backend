// frontend/scenes/game/GameUIRenderer.js (Updated with Redeal Input)

import { Container, Text, TextStyle } from "pixi.js";
import { GameButton } from "../../components/GameButton.js";
import { GameTextbox } from "../../components/GameTextbox.js";

/**
 * Game UI Renderer
 * Handles all UI rendering for the game scene
 */
export class GameUIRenderer extends Container {
  constructor(gameScene) {
    super();
    
    this.gameScene = gameScene;
    this.stateManager = null; // Will be set in initialize()
    
    // UI containers
    this.containers = {};
    this.components = {};
    this.currentInputCallback = null;
    this.currentValidOptions = [];
    
    this.initializeLayout();
    this.createComponents();
  }

  /**
   * Initialize UI layout containers
   */
  initializeLayout() {
    // Create main containers
    this.containers.header = new Container();
    this.containers.main = new Container();
    this.containers.hand = new Container();
    this.containers.input = new Container();
    this.containers.footer = new Container();

    // Set basic layout properties
    this.containers.header.layout = {
      width: "100%",
      height: 80,
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      gap: 10
    };

    this.containers.main.layout = {
      width: "100%",
      height: "auto",
      flexDirection: "column",
      alignItems: "center",
      gap: 20,
    };

    this.containers.input.layout = {
      flexDirection: "row",
      gap: 8,
      alignItems: "center",
    };

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
   * Initialize UI after all components are ready
   */
  async initialize(gameData) {
    // Now we can safely access stateManager
    this.stateManager = this.gameScene.stateManager;
    this.createComponents();
    console.log("✅ UI components created");
  }

  /**
   * Create UI components
   */
  createComponents() {
    // Check if stateManager is available
    if (!this.stateManager) {
      console.warn("⚠️ StateManager not available yet");
      return;
    }

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
    
    // Add redeal phase info
    const infoText = new Text({
      text: "Checking for weak hands...",
      style: new TextStyle({
        fill: "#ffffff",
        fontSize: 16,
      }),
    });
    this.containers.main.addChild(infoText);
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

  // ===== INPUT METHODS =====

  /**
   * Show redeal input with Yes/No options
   */
  showRedealInput(options, callback) {
    this.currentInputCallback = callback;
    this.currentValidOptions = options;
    
    // Clear existing input
    this.clearInputComponents();
    
    // Create redeal prompt
    const promptText = new Text({
      text: "Request redeal? (You have no pieces > 9 points)",
      style: new TextStyle({
        fill: "#ffff00",
        fontSize: 16,
        fontWeight: "bold",
      }),
    });
    
    const optionsText = new Text({
      text: `Options: [${options.join(", ")}]`,
      style: new TextStyle({
        fill: "#cccccc",
        fontSize: 14,
      }),
    });
    
    // Create choice buttons
    const buttonContainer = new Container();
    
    options.forEach((option, index) => {
      const button = new GameButton({
        label: option,
        width: 100,
        onClick: () => this.handleRedealChoice(option),
      });
      
      button.view.x = index * 120;
      buttonContainer.addChild(button.view);
      
      // Add keyboard shortcut info
      const shortcutText = new Text({
        text: `[${index + 1}]`,
        style: new TextStyle({
          fill: "#888888",
          fontSize: 12,
        }),
      });
      shortcutText.x = button.view.x + button.view.width / 2 - shortcutText.width / 2;
      shortcutText.y = button.view.height + 5;
      buttonContainer.addChild(shortcutText);
    });
    
    // Add to input container
    this.containers.input.addChild(promptText);
    this.containers.input.addChild(optionsText);
    this.containers.input.addChild(buttonContainer);
    
    // Position elements
    optionsText.y = promptText.height + 5;
    buttonContainer.y = optionsText.y + optionsText.height + 10;
    
    // Show input container
    this.containers.input.visible = true;
    
    console.log(`🟨 ${this.stateManager?.playerName || 'Player'}, request redeal? [${options.join(", ")}]:`);
  }

  /**
   * Show declaration input with numeric options
   */
  showDeclarationInput(validOptions, callback) {
    this.currentInputCallback = callback;
    this.currentValidOptions = validOptions;
    
    // Clear existing input
    this.clearInputComponents();
    
    // Create declaration prompt
    const promptText = new Text({
      text: `Declare how many piles you want to capture:`,
      style: new TextStyle({
        fill: "#ffff00",
        fontSize: 16,
        fontWeight: "bold",
      }),
    });
    
    const optionsText = new Text({
      text: `Valid options: [${validOptions.join(", ")}]`,
      style: new TextStyle({
        fill: "#cccccc",
        fontSize: 14,
      }),
    });
    
    // Create number input
    this.components.inputBox = new GameTextbox({
      placeholder: "Enter number",
      width: 200,
    });

    this.components.submitButton = new GameButton({
      label: "Declare",
      width: 80,
      onClick: () => this.handleDeclarationSubmit(),
    });
    
    // Add to input container
    this.containers.input.addChild(promptText);
    this.containers.input.addChild(optionsText);
    this.containers.input.addChild(this.components.inputBox.view);
    this.containers.input.addChild(this.components.submitButton.view);
    
    // Position elements
    optionsText.y = promptText.height + 5;
    this.components.inputBox.view.y = optionsText.y + optionsText.height + 10;
    this.components.submitButton.view.x = this.components.inputBox.view.width + 10;
    this.components.submitButton.view.y = this.components.inputBox.view.y;
    
    // Show input container
    this.containers.input.visible = true;
    
    // Focus on input
    this.components.inputBox.focus();
  }

  /**
   * Handle redeal choice selection
   */
  handleRedealChoice(choice) {
    if (this.currentInputCallback && this.currentValidOptions.includes(choice)) {
      const callback = this.currentInputCallback;
      this.currentInputCallback = null;
      this.currentValidOptions = [];
      
      callback(choice);
    }
  }

  /**
   * Handle declaration submit
   */
  handleDeclarationSubmit() {
    if (!this.currentInputCallback || !this.components.inputBox) return;
    
    const value = parseInt(this.components.inputBox.getText().trim());
    
    if (isNaN(value)) {
      this.showError("Please enter a valid number");
      return;
    }
    
    if (!this.currentValidOptions.includes(value)) {
      this.showError(`Invalid choice. Select from [${this.currentValidOptions.join(", ")}]`);
      return;
    }
    
    const callback = this.currentInputCallback;
    this.currentInputCallback = null;
    this.currentValidOptions = [];
    
    callback(value);
  }

  /**
   * Handle keyboard number selection
   */
  selectByNumber(number) {
    if (this.currentValidOptions.includes(number) && this.currentInputCallback) {
      // For redeal phase (Yes=1, No=2)
      if (this.currentValidOptions.length === 2 && 
          this.currentValidOptions.includes('Yes') && 
          this.currentValidOptions.includes('No')) {
        const choice = number === 1 ? 'Yes' : number === 2 ? 'No' : null;
        if (choice) {
          this.handleRedealChoice(choice);
        }
      }
      // For declaration phase (numeric values)
      else if (typeof number === 'number') {
        const callback = this.currentInputCallback;
        this.currentInputCallback = null;
        this.currentValidOptions = [];
        callback(number);
      }
    }
  }

  // ===== UTILITY METHODS =====

  /**
   * Update phase indicator text
   */
  updatePhaseIndicator(text) {
    if (this.components.phaseIndicator) {
      this.components.phaseIndicator.text = text;
    }
  }

  /**
   * Clear main content area
   */
  clearMainContent() {
    this.containers.main.removeChildren();
  }

  /**
   * Clear input components
   */
  clearInputComponents() {
    this.containers.input.removeChildren();
    this.components.inputBox = null;
    this.components.submitButton = null;
  }

  /**
   * Hide input container
   */
  hideInput() {
    this.containers.input.visible = false;
    this.clearInputComponents();
    this.currentInputCallback = null;
    this.currentValidOptions = [];
  }

  /**
   * Submit current input (called by Enter key)
   */
  submitCurrentInput() {
    if (this.components.submitButton) {
      // Trigger the submit button click
      this.components.submitButton.onClick();
    }
  }

  /**
   * Display player hand
   */
  displayHand(hand) {
    this.containers.hand.removeChildren();
    
    if (!hand || hand.length === 0) return;
    
    const title = new Text({
      text: "Your Hand:",
      style: new TextStyle({
        fill: "#ffffff",
        fontSize: 16,
        fontWeight: "bold",
      }),
    });
    
    this.containers.hand.addChild(title);
    
    hand.forEach((card, index) => {
      const cardText = new Text({
        text: `${index + 1}. ${card}`,
        style: new TextStyle({
          fill: "#cccccc",
          fontSize: 14,
        }),
      });
      cardText.y = title.height + 5 + (index * 20);
      this.containers.hand.addChild(cardText);
    });
  }

  /**
   * Show success message
   */
  showSuccess(message) {
    // Create temporary success message
    const successText = new Text({
      text: `✅ ${message}`,
      style: new TextStyle({
        fill: "#00ff00",
        fontSize: 14,
      }),
    });
    
    this.containers.footer.addChild(successText);
    
    // Remove after 3 seconds
    setTimeout(() => {
      if (successText.parent) {
        successText.parent.removeChild(successText);
      }
    }, 3000);
  }

  /**
   * Show error message
   */
  showError(message) {
    // Create temporary error message
    const errorText = new Text({
      text: `❌ ${message}`,
      style: new TextStyle({
        fill: "#ff0000",
        fontSize: 14,
      }),
    });
    
    this.containers.footer.addChild(errorText);
    
    // Remove after 3 seconds
    setTimeout(() => {
      if (errorText.parent) {
        errorText.parent.removeChild(errorText);
      }
    }, 3000);
  }

  /**
   * Show warning message
   */
  showWarning(message) {
    // Create temporary warning message
    const warningText = new Text({
      text: `⚠️ ${message}`,
      style: new TextStyle({
        fill: "#ffaa00",
        fontSize: 14,
      }),
    });
    
    this.containers.footer.addChild(warningText);
    
    // Remove after 3 seconds
    setTimeout(() => {
      if (warningText.parent) {
        warningText.parent.removeChild(warningText);
      }
    }, 3000);
  }

  /**
   * Update declaration progress
   */
  updateDeclaration(player, value) {
    // Find or create declaration display
    let declarationDisplay = this.containers.main.children.find(
      child => child.declarationDisplay
    );
    
    if (!declarationDisplay) {
      declarationDisplay = new Container();
      declarationDisplay.declarationDisplay = true;
      this.containers.main.addChild(declarationDisplay);
    }
    
    // Update display logic here
    // This would show current declarations from all players
  }

  /**
   * Show declaration summary
   */
  showDeclarationSummary(declarations) {
    this.clearMainContent();
    
    const title = new Text({
      text: "Declaration Summary:",
      style: new TextStyle({
        fill: "#ffffff",
        fontSize: 18,
        fontWeight: "bold",
      }),
    });
    
    this.containers.main.addChild(title);
    
    let yOffset = title.height + 10;
    const total = Object.values(declarations).reduce((sum, value) => sum + value, 0);
    
    Object.entries(declarations).forEach(([player, value]) => {
      const declText = new Text({
        text: `${player}: ${value} piles`,
        style: new TextStyle({
          fill: "#cccccc",
          fontSize: 14,
        }),
      });
      declText.y = yOffset;
      this.containers.main.addChild(declText);
      yOffset += 20;
    });
    
    const totalText = new Text({
      text: `Total: ${total}`,
      style: new TextStyle({
        fill: "#ffff00",
        fontSize: 16,
        fontWeight: "bold",
      }),
    });
    totalText.y = yOffset + 10;
    this.containers.main.addChild(totalText);
  }
}