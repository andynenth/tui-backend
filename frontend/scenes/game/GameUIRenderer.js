// frontend/scenes/game/GameUIRenderer.js

import { Container, Text, TextStyle } from "pixi.js";
import { GameTextbox } from "../../components/GameTextbox.js";
import { GameButton } from "../../components/GameButton.js";

/**
 * Game UI Renderer
 * Handles all UI rendering for the game
 * Separates presentation logic from game logic
 *
 * Responsibilities:
 * - Create and manage UI components
 * - Update UI based on game state
 * - Handle UI animations and layouts
 * - Manage user input interfaces
 */
export class GameUIRenderer extends Container {
  // ===============================
  // CONSTRUCTOR & INITIALIZATION
  // ===============================

  /**
   * Initialize GameUIRenderer
   * @param {GameScene} gameScene - Parent game scene
   */
  constructor(gameScene) {
    super();

    this.gameScene = gameScene;
    this.parentContainer = gameScene;
    this.stateManager = null; // Will be set in initialize()

    // UI containers organized by layout sections
    this.containers = {
      header: new Container(),
      main: new Container(),
      input: new Container(),
      footer: new Container(),
    };

    // UI components registry
    this.components = {
      statusText: null,
      handDisplay: null,
      inputBox: null,
      submitButton: null,
      phaseIndicator: null,
    };

    // Input state management
    this.currentInputCallback = null;
    this.inputValidator = null;

    // Initialize UI structure
    gameScene.addChild(this);
    this.setupLayout();
  }

  /**
   * Initialize UI after all dependencies are ready
   * @param {Object} gameData - Initial game data
   */
  async initialize(gameData) {
    this.stateManager = this.gameScene.stateManager;
    this.createComponents();
    console.log("UI components created");
  }

  // ===============================
  // LAYOUT & COMPONENT SETUP
  // ===============================

  /**
   * Set up container layout and positioning
   * Defines the spatial organization of UI elements
   */
  setupLayout() {
    // Define layout configurations
    this._defineLayoutConfigs();

    // Add containers to display hierarchy
    Object.values(this.containers).forEach((container) => {
      this.addChild(container);
    });
  }

  /**
   * Create and configure UI components
   * Sets up all interactive and display elements
   */
  createComponents() {
    if (!this.stateManager) {
      console.warn("⚠️ StateManager not available yet");
      return;
    }

    this._createHeaderComponents();
    this._createInputComponents();
  }

  // ===============================
  // PHASE UI MANAGEMENT
  // ===============================

  /**
   * Show redeal phase UI
   * Displays interface for redeal checking
   */
  showRedealPhase() {
    this.updatePhaseIndicator("Redeal Check");
    this.clearMainContent();
  }

  /**
   * Show declaration phase UI
   * Displays interface for player declarations
   */
  showDeclarationPhase() {
    this.updatePhaseIndicator("Declaration Phase");
    this.clearMainContent();

    const progressText = this._createText("Waiting for declarations...", {
      fill: "#ffffff",
      fontSize: 16,
    });
    this.containers.main.addChild(progressText);
  }

  /**
   * Show turn phase UI
   * Displays interface for game turns and card play
   */
  showTurnPhase() {
    this.updatePhaseIndicator("Turn Phase");
    this.clearMainContent();
  }

  /**
   * Show scoring phase UI
   * Displays interface for round scoring
   */
  showScoringPhase() {
    this.updatePhaseIndicator("Scoring");
    this.clearMainContent();
  }

  // ===============================
  // INPUT INTERFACE MANAGEMENT
  // ===============================

  /**
   * Show redeal input interface
   * @param {string[]} options - Available options (["Yes", "No"])
   * @param {Function} callback - Callback for user selection
   */
  showRedealInput(options, callback) {
    console.log("🎨 GameUIRenderer: showRedealInput called");
    console.log("  Options:", options);
    console.log("  Callback:", !!callback);

    this.currentInputCallback = callback;
    this.currentValidOptions = options;

    // Clear existing input first
    this._clearRedealComponents();

    // Reset position to center
    this._positionInputContainer();

    try {
      // Create redeal prompt elements
      const elements = this._createRedealPromptElements(options);

      // Position all elements
      this._positionRedealElements(elements);

      // Add all to input container
      elements.forEach((element) => {
        this.containers.input.addChild(element);
      });

      // Show input container
      this.containers.input.visible = true;

      console.log("✅ Redeal UI created and displayed");
      console.log(`📍 Container visible: ${this.containers.input.visible}`);
      console.log(
        `📍 Container position: x=${this.containers.input.x}, y=${this.containers.input.y}`
      );

      // Force render update
      this.gameScene.app?.renderer?.render(this.gameScene);
    } catch (error) {
      console.error("❌ Error creating redeal UI:", error);
      console.error(error.stack);
    }
  }

  /**
   * Handle redeal choice selection
   * @param {string} choice - User's choice ("Yes" or "No")
   */
  handleRedealChoice(choice) {
    console.log(`🎯 GameUIRenderer: handleRedealChoice(${choice})`);

    if (!this.currentInputCallback) {
      console.error("❌ No callback available");
      return;
    }

    if (!this.currentValidOptions.includes(choice)) {
      console.error(
        `❌ Invalid choice: ${choice}. Valid: ${this.currentValidOptions}`
      );
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
      console.log(`📞 Calling redeal callback with choice: ${choice}`);
      callback(choice);
    } catch (error) {
      console.error("❌ Error in redeal callback:", error);
    }
  }

  // ===============================
  // REDEAL PHASE UI METHODS
  // ===============================

  /**
   * Show redeal phase UI
   * Displays interface for redeal checking
   */
  //   showRedealPhase() {
  //     this.updatePhaseIndicator("Redeal Check");
  //     this.clearMainContent();

  //     const infoText = this._createText("Checking for weak hands...", {
  //       fill: "#ffffff",
  //       fontSize: 16,
  //     });
  //     this.containers.main.addChild(infoText);
  //   }

  // ===============================
  // PRIVATE REDEAL HELPER METHODS
  // ===============================

  /**
   * Clear redeal-specific components
   * @private
   */
  _clearRedealComponents() {
    console.log("🧹 Clearing redeal components");
    console.log(`   Children before: ${this.containers.input.children.length}`);

    this.containers.input.removeChildren();

    console.log(`   Children after: ${this.containers.input.children.length}`);
  }

  /**
   * Position input container for redeal
   * @private
   */
  _positionInputContainer() {
    // Get screen dimensions
    const screenWidth = window.innerWidth;
    const screenHeight = window.innerHeight;

    // Center the input container
    this.containers.input.x = screenWidth / 2;
    this.containers.input.y = screenHeight / 2;

    console.log(
      `🎯 Input positioned at center: ${this.containers.input.x}, ${this.containers.input.y}`
    );
  }

  /**
   * Create redeal prompt UI elements
   * @private
   * @param {string[]} options - Available options
   * @returns {DisplayObject[]} Array of UI elements
   */
  _createRedealPromptElements(options) {
    const elements = [];

    // Main prompt
    const promptText = this._createText("⚠️ REQUEST REDEAL?", {
      fill: "#ff6600",
      fontSize: 24,
      fontWeight: "bold",
      align: "center",
    });
    elements.push(promptText);

    // Description
    const descText = this._createText("You have no pieces > 9 points", {
      fill: "#ffffff",
      fontSize: 16,
      align: "center",
    });
    elements.push(descText);

    // Options text
    const optionsText = this._createText(`Options: [${options.join(", ")}]`, {
      fill: "#cccccc",
      fontSize: 14,
      align: "center",
    });
    elements.push(optionsText);

    // Create buttons container
    const buttonContainer = this._createRedealButtons(options);
    elements.push(buttonContainer);

    return elements;
  }

  /**
   * Create redeal option buttons
   * @private
   * @param {string[]} options - Available options
   * @returns {Container} Button container
   */
  _createRedealButtons(options) {
    const buttonContainer = new Container();

    options.forEach((option, index) => {
      console.log(`🔘 Creating redeal button: ${option}`);

      const button = new GameButton({
        label: option,
        width: 120,
        height: 50,
        onClick: () => {
          console.log(`🎯 Redeal button clicked: ${option}`);
          this.handleRedealChoice(option);
        },
      });

      // Position buttons side by side
      button.view.x = index * 140;
      button.view.y = 0;

      buttonContainer.addChild(button.view);

      // Add keyboard shortcut info
      const shortcutText = this._createText(`Press [${index + 1}]`, {
        fill: "#888888",
        fontSize: 12,
        align: "center",
      });
      shortcutText.x = button.view.x + 60 - shortcutText.width / 2;
      shortcutText.y = button.view.height + 5;
      buttonContainer.addChild(shortcutText);
    });

    return buttonContainer;
  }

  /**
   * Position redeal UI elements
   * @private
   * @param {DisplayObject[]} elements - UI elements to position
   */
  _positionRedealElements(elements) {
    const [promptText, descText, optionsText, buttonContainer] = elements;

    // Position elements vertically
    // promptText.x = -promptText.width / 2;
    promptText.x = -promptText.width*2;
    promptText.y = -100;

    // descText.x = -descText.width / 2;
    descText.x = -descText.width*2;
    descText.y = promptText.y + 40;

    // optionsText.x = -optionsText.width / 2;
    optionsText.x = -optionsText.width*2;
    optionsText.y = descText.y + 30;

    // buttonContainer.x = -buttonContainer.width / 2;
    buttonContainer.x = -buttonContainer.width*2;
    buttonContainer.y = optionsText.y + 40;
  }

  /**
   * Add keyboard input support for redeal
   * @param {KeyboardEvent} event - Keyboard event
   * @returns {boolean} True if handled
   */
  handleRedealKeyboard(event) {
    if (this.currentInputCallback && this.currentValidOptions.length > 0) {
      const key = event.key;

      // Handle Yes/No shortcuts
      if (key === "1" || key.toLowerCase() === "y") {
        if (this.currentValidOptions.includes("Yes")) {
          console.log(`⌨️ Keyboard redeal: Yes`);
          this.handleRedealChoice("Yes");
          event.preventDefault();
          return true;
        }
      } else if (key === "2" || key.toLowerCase() === "n") {
        if (this.currentValidOptions.includes("No")) {
          console.log(`⌨️ Keyboard redeal: No`);
          this.handleRedealChoice("No");
          event.preventDefault();
          return true;
        }
      }
    }
    return false;
  }

  /**
   * Show generic input prompt
   * @param {string} prompt - Input prompt message
   * @param {Function} validator - Optional input validator function
   * @returns {Promise<string>} User input value
   */
  async showInput(prompt, validator = null) {
    return new Promise((resolve) => {
      console.log(`\n${prompt}`);

      this._showInputInterface();
      this._setupInputHandlers(resolve, validator);
    });
  }

  /**
   * Show declaration input interface
   * @param {number[]} validOptions - Valid declaration values
   * @param {Function} callback - Callback for user selection
   */
  showDeclarationInput(validOptions, callback) {
    const validator = this._createDeclarationValidator(validOptions);

    this.showInput(
      `Enter declaration (${validOptions.join(", ")}):`,
      validator
    ).then((value) => {
      callback(parseInt(value));
    });
  }


  /**
   * Handle input submission
   * Processes user input and triggers callbacks
   */
  handleSubmit() {
    if (!this.currentInputCallback) return;

    const value = this.components.inputBox.getText().trim();
    if (!value) return;

    // Validate input if validator exists
    if (!this._validateInput(value)) return;

    // Process valid input
    this._processInputSubmission(value);
  }

  // ===============================
  // DISPLAY & VISUALIZATION
  // ===============================

  /**
   * Display player's hand
   * @param {string[]} hand - Array of card strings
   */
  displayHand(hand) {
    console.log("\n🃏 Your hand:");
    hand.forEach((card, i) => {
      console.log(`${i}: ${card}`);
    });
    // TODO: Create visual hand display
  }

  /**
   * Update declaration display for a player
   * @param {string} playerName - Name of declaring player
   * @param {number} value - Declaration value
   */
  updateDeclaration(playerName, value) {
    console.log(`${playerName} declared ${value}`);
    // TODO: Update declaration display
  }

  /**
   * Show declaration summary
   * @param {Object} declarations - Map of player names to declaration values
   */
  showDeclarationSummary(declarations) {
    console.log("\n📋 Declaration Summary:");
    Object.entries(declarations).forEach(([player, value]) => {
      console.log(`  ${player}: ${value} piles`);
    });
  }

  /**
   * Update phase indicator text
   * @param {string} phaseName - Current phase name
   */
  updatePhaseIndicator(phaseName) {
    if (this.components.phaseIndicator) {
      this.components.phaseIndicator.text = phaseName;
    }
  }


  // ===============================
  // FEEDBACK & MESSAGING
  // ===============================

  /**
   * Show error message to user
   * @param {string} message - Error message to display
   */
  showError(message) {
    console.error(`❌ ${message}`);

    const errorText = this._createText(message, {
      fill: "#ff0000",
      fontSize: 16,
    });

    errorText.position.set(10, 200);
    this.containers.main.addChild(errorText);

    this._scheduleElementRemoval(errorText, 3000);
  }

  /**
   * Show warning message to user
   * @param {string} message - Warning message to display
   */
  showWarning(message) {
    console.warn(`⚠️ ${message}`);
    // TODO: Show visual warning
  }

  /**
   * Show success message to user
   * @param {string} message - Success message to display
   */
  showSuccess(message) {
    console.log(`✅ ${message}`);
    // TODO: Show visual success
  }

  /**
   * Show game results screen
   * @param {Object} data - Game result data
   * @param {string[]} data.winners - Array of winner names
   */
  showGameResults(data) {
    this.clearMainContent();
    this.updatePhaseIndicator("Game Over");

    const resultText =
      data.winners?.length > 0
        ? `🏆 Winner: ${data.winners.join(", ")}`
        : "🎮 Game Over!";

    const gameOverText = this._createText(resultText, {
      fill: "#00ff00",
      fontSize: 30,
      fontWeight: "bold",
    });

    this.containers.main.addChild(gameOverText);
  }

  // ===============================
  // CLEANUP & DESTRUCTION
  // ===============================

  /**
   * Destroy UI renderer and clean up resources
   * @param {Object} options - Destruction options
   */
  destroy(options) {
    // Destroy all containers and their children
    Object.values(this.containers).forEach((container) => {
      container.destroy({ children: true });
    });

    // Clear component and container references
    this.components = {};
    this.containers = {};

    // Clear callbacks to prevent memory leaks
    this.currentInputCallback = null;
    this.inputValidator = null;

    super.destroy(options);
  }

  // ===============================
  // PRIVATE HELPER METHODS
  // ===============================

  /**
   * Define layout configurations for containers
   * @private
   */
  _defineLayoutConfigs() {
    // Main layout configuration
    this.layout = {
      width: "100%",
      height: "100%",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "flex-start",
      padding: 20,
      gap: 20,
    };

    // Individual container layouts
    this.containers.header.layout = {
      width: "100%",
      height: "auto",
      flexDirection: "column",
      alignItems: "center",
      gap: 10,
    };

    this.containers.main.layout = {
      width: "100%",
      flex: 1,
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
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
  }

  /**
   * Create header UI components
   * @private
   */
  _createHeaderComponents() {
    // Status text
    this.components.statusText = this._createText(
      `Game Room: ${this.stateManager.roomId}`,
      { fill: "#666666", fontSize: 14 }
    );
    this.containers.header.addChild(this.components.statusText);

    // Phase indicator
    this.components.phaseIndicator = this._createText("", {
      fill: "#ffffff",
      fontSize: 20,
      fontWeight: "bold",
    });
    this.containers.header.addChild(this.components.phaseIndicator);
  }

  /**
   * Create input UI components
   * @private
   */
  _createInputComponents() {
    // Text input box
    this.components.inputBox = new GameTextbox({
      placeholder: "Your input",
      width: 300,
    });

    // Submit button
    this.components.submitButton = new GameButton({
      label: "Enter",
      width: 80,
      onClick: () => this.handleSubmit(),
    });

    // Add to input container
    this.containers.input.addChild(
      this.components.inputBox.view,
      this.components.submitButton.view
    );

    // Hide input by default
    this.containers.input.visible = false;
  }

  /**
   * Create text element with style
   * @private
   * @param {string} text - Text content
   * @param {Object} styleOptions - Text style options
   * @returns {Text} Created text element
   */
  _createText(text, styleOptions = {}) {
    return new Text({
      text,
      style: new TextStyle(styleOptions),
    });
  }

  /**
   * Show input interface
   * @private
   */
  _showInputInterface() {
    this.containers.input.visible = true;
    this.components.inputBox.setText("");
    this.components.inputBox.focus();
  }

  /**
   * Setup input handlers and callbacks
   * @private
   * @param {Function} resolve - Promise resolver
   * @param {Function} validator - Input validator
   */
  _setupInputHandlers(resolve, validator) {
    this.currentInputCallback = resolve;
    this.inputValidator = validator;
  }

  /**
   * Create declaration input validator
   * @private
   * @param {number[]} validOptions - Valid declaration options
   * @returns {Function} Validator function
   */
  _createDeclarationValidator(validOptions) {
    return (value) => {
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
    };
  }

  /**
   * Validate input using current validator
   * @private
   * @param {string} value - Input value to validate
   * @returns {boolean} True if valid
   */
  _validateInput(value) {
    if (this.inputValidator) {
      const result = this.inputValidator(value);
      if (!result.valid) {
        this.showError(result.message);
        return false;
      }
    }
    return true;
  }

  /**
   * Process valid input submission
   * @private
   * @param {string} value - Valid input value
   */
  _processInputSubmission(value) {
    // Save callback before clearing state
    const callback = this.currentInputCallback;

    // Clear input state
    this.hideInput();

    // Execute callback
    callback(value);
  }

  /**
   * Schedule element removal after delay
   * @private
   * @param {DisplayObject} element - Element to remove
   * @param {number} delay - Delay in milliseconds
   */
  _scheduleElementRemoval(element, delay) {
    setTimeout(() => {
      if (element.parent) {
        element.destroy();
      }
    }, delay);
  }

  /**
   * Show waiting message
   * @param {string} message - Message to display while waiting
   */
  showWaitingMessage(message) {
    console.log(`⏳ ${message}`);

    // Clear any existing waiting messages
    this._clearWaitingMessages();

    // Create waiting text
    const waitingText = this._createText(message, {
      fill: "#ffff00", // Yellow color for waiting
      fontSize: 18,
      fontWeight: "bold",
      align: "center",
    });

    // Tag it for easy removal later
    waitingText.name = "waitingMessage";

    // Center it in the main area
    const screenWidth = window.innerWidth;
    // waitingText.x = (screenWidth - waitingText.width) / 2;
    waitingText.y = 250;

    // Add to main container
    this.containers.main.addChild(waitingText);

    // Add a simple loading animation (dots)
    this._startWaitingAnimation(waitingText);
  }

  /**
   * Clear all waiting messages
   * @private
   */
  _clearWaitingMessages() {
    // Remove all children with name "waitingMessage"
    const toRemove = this.containers.main.children.filter(
      (child) => child.name === "waitingMessage"
    );
    toRemove.forEach((child) => child.destroy());
  }

  /**
   * Start waiting animation (animated dots)
   * @private
   * @param {Text} textElement - Text element to animate
   */
  _startWaitingAnimation(textElement) {
    const originalText = textElement.text;
    let dotCount = 0;

    const animationInterval = setInterval(() => {
      // Stop if element was destroyed
      if (!textElement.parent) {
        clearInterval(animationInterval);
        return;
      }

      // Animate dots: . .. ...
      dotCount = (dotCount + 1) % 4;
      const dots = ".".repeat(dotCount);
      textElement.text = originalText + dots;
    }, 500);

    // Store interval ID for cleanup
    textElement._animationInterval = animationInterval;
  }

  /**
   * Show decision result (optional method for showing who decided what)
   * @param {string} playerName - Player who made decision
   * @param {string} choice - Their choice
   */
  showDecisionResult(playerName, choice) {
    console.log(`📊 ${playerName} chose: ${choice}`);

    // Create result text
    const resultText = this._createText(
      `${playerName} ${
        choice === "accept" ? "✅ accepted" : "❌ declined"
      } redeal`,
      {
        fill: choice === "accept" ? "#00ff00" : "#ff9999",
        fontSize: 16,
        align: "center",
      }
    );

    // Position it
    const screenWidth = window.innerWidth;
    // resultText.x = (screenWidth - resultText.width) / 2;
    resultText.y = 300;

    // Add to main container
    this.containers.main.addChild(resultText);

    // Remove after 2 seconds
    this._scheduleElementRemoval(resultText, 2000);
  }

  // Also update the hideInput method to clear waiting messages:
  hideInput() {
    this.containers.input.visible = false;
    this.currentInputCallback = null;
    this.inputValidator = null;

    // Also clear any waiting messages when hiding input
    this._clearWaitingMessages();
  }

  // Update clearMainContent to properly clean up animations:
  clearMainContent() {
    // Stop any animations
    this.containers.main.children.forEach((child) => {
      if (child._animationInterval) {
        clearInterval(child._animationInterval);
      }
    });

    this.containers.main.removeChildren();
  }
}
