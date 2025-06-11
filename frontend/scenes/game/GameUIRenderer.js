// frontend/scenes/game/GameUIRenderer.js - Fixed positioning and debugging

import { Container, Text, TextStyle, Graphics } from "pixi.js";
import { GameButton } from "../../components/GameButton.js";
import { GameTextbox } from "../../components/GameTextbox.js";

/**
 * Game UI Renderer - Fixed version with proper positioning
 */
export class GameUIRenderer extends Container {
  constructor(gameScene) {
    super();
    
    this.gameScene = gameScene;
    this.stateManager = null;
    
    // UI containers
    this.containers = {};
    this.components = {};
    this.currentInputCallback = null;
    this.currentValidOptions = [];
    
    // Get screen dimensions
    this.screenWidth = window.innerWidth;
    this.screenHeight = window.innerHeight;
    
    console.log(`🖥️ Screen size: ${this.screenWidth}x${this.screenHeight}`);
    
    this.initializeLayout();
    this.createComponents();
  }

  /**
   * Initialize UI layout containers with proper positioning
   */
  initializeLayout() {
    console.log("🎨 Initializing UI layout...");
    
    // Create main containers
    this.containers.header = new Container();
    this.containers.main = new Container();
    this.containers.hand = new Container();
    this.containers.input = new Container();
    this.containers.footer = new Container();

    // Position containers on screen
    this.containers.header.x = 0;
    this.containers.header.y = 0;
    
    this.containers.main.x = 0;
    this.containers.main.y = 100;
    
    this.containers.hand.x = 20;
    this.containers.hand.y = 200;
    
    // ⭐ FIX: Position input in center of screen
    this.containers.input.x = this.screenWidth / 2; // Center horizontally
    this.containers.input.y = this.screenHeight / 2; // Center vertically
    
    // EMERGENCY: Also try absolute positioning
    console.log(`🎯 EMERGENCY: Input positioned at ${this.containers.input.x}, ${this.containers.input.y}`);
    
    // Backup positioning - top-left for testing
    this.containers.inputBackup = new Container();
    this.containers.inputBackup.x = 50;
    this.containers.inputBackup.y = 50;
    this.containers.inputBackup.visible = false;
    
    this.containers.footer.x = 0;
    this.containers.footer.y = this.screenHeight - 100;

    // Make all containers visible by default
    Object.values(this.containers).forEach((container) => {
      container.visible = true;
      this.addChild(container);
    });
    
    // Hide input initially
    this.containers.input.visible = false;
    
    console.log("✅ UI layout initialized");
    console.log(`📍 Input container position: x=${this.containers.input.x}, y=${this.containers.input.y}`);
  }

  // ===== FIXED INPUT METHODS =====

  /**
   * Show redeal input with Yes/No options - FIXED VERSION
   */
  showRedealInput(options, callback) {
    console.log("🎨 GameUIRenderer: showRedealInput called");
    console.log("  Options:", options);
    console.log("  Callback:", !!callback);
    
    this.currentInputCallback = callback;
    this.currentValidOptions = options;
    
    // Clear existing input first
    this.clearInputComponents();
    
    // EMERGENCY: Reset position to center
    this.containers.input.x = this.screenWidth / 2;
    this.containers.input.y = this.screenHeight / 2;
    
    console.log(`🎯 EMERGENCY: Reset input position to ${this.containers.input.x}, ${this.containers.input.y}`);
    
    try {
      // Create redeal prompt
      const promptText = new Text({
        text: "⚠️ REQUEST REDEAL?",
        style: new TextStyle({
          fill: "#ff6600",
          fontSize: 24,
          fontWeight: "bold",
          align: "center",
        }),
      });
      
      const descText = new Text({
        text: "You have no pieces > 9 points",
        style: new TextStyle({
          fill: "#ffffff",
          fontSize: 16,
          align: "center",
        }),
      });
      
      const optionsText = new Text({
        text: `Options: [${options.join(", ")}]`,
        style: new TextStyle({
          fill: "#cccccc",
          fontSize: 14,
          align: "center",
        }),
      });
      
      // Create buttons container
      const buttonContainer = new Container();
      
      options.forEach((option, index) => {
        console.log(`🔘 Creating button: ${option}`);
        
        const button = new GameButton({
          label: option,
          width: 120,
          height: 50,
          onClick: () => {
            console.log(`🎯 Button clicked: ${option}`);
            this.handleRedealChoice(option);
          },
        });
        
        // Position buttons side by side
        button.view.x = index * 140;
        button.view.y = 0;
        
        buttonContainer.addChild(button.view);
        
        // Add keyboard shortcut info
        const shortcutText = new Text({
          text: `Press [${index + 1}]`,
          style: new TextStyle({
            fill: "#888888",
            fontSize: 12,
            align: "center",
          }),
        });
        shortcutText.x = button.view.x + 60 - shortcutText.width / 2;
        shortcutText.y = button.view.height + 5;
        buttonContainer.addChild(shortcutText);
      });
      
      // Position all elements vertically
      promptText.x = -promptText.width / 2;
      promptText.y = -100;
      
      descText.x = -descText.width / 2;
      descText.y = promptText.y + 40;
      
      optionsText.x = -optionsText.width / 2;
      optionsText.y = descText.y + 30;
      
      buttonContainer.x = -buttonContainer.width / 2;
      buttonContainer.y = optionsText.y + 40;
      
      // Add all to input container
      this.containers.input.addChild(promptText);
      this.containers.input.addChild(descText);
      this.containers.input.addChild(optionsText);
      this.containers.input.addChild(buttonContainer);
      
      // Show input container
      this.containers.input.visible = true;
      
      console.log("✅ Redeal UI created and displayed");
      console.log(`📍 Container visible: ${this.containers.input.visible}`);
      console.log(`📍 Container position: x=${this.containers.input.x}, y=${this.containers.input.y}`);
      console.log(`📍 Container children: ${this.containers.input.children.length}`);
      
      // Force render update
      this.gameScene.app?.renderer?.render(this.gameScene);
      
    } catch (error) {
      console.error("❌ Error creating redeal UI:", error);
      console.error(error.stack);
    }
  }

  /**
   * Handle redeal choice selection - FIXED VERSION
   */
  handleRedealChoice(choice) {
    console.log(`🎯 GameUIRenderer: handleRedealChoice(${choice})`);
    
    if (!this.currentInputCallback) {
      console.error("❌ No callback available");
      return;
    }
    
    if (!this.currentValidOptions.includes(choice)) {
      console.error(`❌ Invalid choice: ${choice}. Valid: ${this.currentValidOptions}`);
      return;
    }
    
    // Store callback before clearing
    const callback = this.currentInputCallback;
    
    // Clear state first
    this.currentInputCallback = null;
    this.currentValidOptions = [];
    
    // Hide input
    this.hideInput();
    
    // Call callback
    try {
      console.log(`📞 Calling callback with choice: ${choice}`);
      callback(choice);
    } catch (error) {
      console.error("❌ Error in callback:", error);
    }
  }

  /**
   * Clear input components - FIXED VERSION
   */
  clearInputComponents() {
    console.log("🧹 Clearing input components");
    console.log(`   Children before: ${this.containers.input.children.length}`);
    
    this.containers.input.removeChildren();
    this.components.inputBox = null;
    this.components.submitButton = null;
    
    console.log(`   Children after: ${this.containers.input.children.length}`);
  }

  /**
   * Hide input container - FIXED VERSION
   */
  hideInput() {
    console.log("👻 Hiding input container");
    
    this.containers.input.visible = false;
    this.clearInputComponents();
    this.currentInputCallback = null;
    this.currentValidOptions = [];
    
    console.log(`📍 Container visible after hide: ${this.containers.input.visible}`);
  }

  // ===== DEBUGGING METHODS =====

  /**
   * Debug UI state - call from console
   */
  debugUI() {
    console.log("🔍 UI DEBUG INFO:");
    console.log("  Screen size:", this.screenWidth, "x", this.screenHeight);
    console.log("  Input container:");
    console.log("    - Visible:", this.containers.input.visible);
    console.log("    - Position:", this.containers.input.x, this.containers.input.y);
    console.log("    - Children:", this.containers.input.children.length);
    console.log("    - Callback:", !!this.currentInputCallback);
    console.log("    - Options:", this.currentValidOptions);
    
    // List all children
    this.containers.input.children.forEach((child, index) => {
      console.log(`    Child ${index}:`, child.constructor.name, child.x, child.y);
    });
  }

  /**
   * Force show test UI - for debugging
   */
  showTestUI() {
    console.log("🧪 Showing test UI");
    
    this.clearInputComponents();
    
    const testText = new Text({
      text: "🧪 TEST UI - CAN YOU SEE THIS?",
      style: new TextStyle({
        fill: "#ff0000",
        fontSize: 32,
        fontWeight: "bold",
      }),
    });
    
    testText.x = -testText.width / 2;
    testText.y = -testText.height / 2;
    
    this.containers.input.addChild(testText);
    this.containers.input.visible = true;
    
    // EMERGENCY: Also try absolute positioning
    this.containers.input.x = 100;
    this.containers.input.y = 100;
    
    console.log("✅ Test UI shown");
    console.log(`📍 Position: ${this.containers.input.x}, ${this.containers.input.y}`);
    
    // Try backup position if needed
    setTimeout(() => {
      console.log("🔄 Trying backup position...");
      this.containers.input.x = 50;
      this.containers.input.y = 50;
    }, 1000);
  }

  // ===== EXISTING METHODS (keep unchanged) =====

  async initialize(gameData) {
    this.stateManager = this.gameScene.stateManager;
    this.createComponents();
    console.log("✅ UI components created");
  }

  createComponents() {
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
  }

  showRedealPhase() {
    this.updatePhaseIndicator("Redeal Check");
    this.clearMainContent();
    
    const infoText = new Text({
      text: "Checking for weak hands...",
      style: new TextStyle({
        fill: "#ffffff",
        fontSize: 16,
      }),
    });
    this.containers.main.addChild(infoText);
  }

  updatePhaseIndicator(text) {
    if (this.components.phaseIndicator) {
      this.components.phaseIndicator.text = text;
    }
  }

  clearMainContent() {
    this.containers.main.removeChildren();
  }

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

  showSuccess(message) {
    const successText = new Text({
      text: `✅ ${message}`,
      style: new TextStyle({
        fill: "#00ff00",
        fontSize: 14,
      }),
    });
    
    this.containers.footer.addChild(successText);
    
    setTimeout(() => {
      if (successText.parent) {
        successText.parent.removeChild(successText);
      }
    }, 3000);
  }

  showError(message) {
    const errorText = new Text({
      text: `❌ ${message}`,
      style: new TextStyle({
        fill: "#ff0000",
        fontSize: 14,
      }),
    });
    
    this.containers.footer.addChild(errorText);
    
    setTimeout(() => {
      if (errorText.parent) {
        errorText.parent.removeChild(errorText);
      }
    }, 3000);
  }
}