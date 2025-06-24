// frontend/game/phases/DeclarationPhase.js

import { BasePhase } from "./BasePhase.js";

/**
 * Declaration Phase
 * Players declare how many piles they plan to capture
 *
 * Rules:
 * - Players declare in order starting from round starter
 * - Total declarations cannot equal 8
 * - Players who declared 0 twice must declare at least 1
 */
export class DeclarationPhase extends BasePhase {
  
  // ===============================
  // CONSTRUCTOR & INITIALIZATION
  // ===============================
  
  constructor(stateManager, socketManager, uiRenderer) {
    super(stateManager, socketManager, uiRenderer);

    // Explicitly set phase name (overrides BasePhase constructor.name logic)
    this.name = 'declaration';
    
    // Input state management
    this.waitingForInput = false;
    this.hasPromptedUser = false;
  }

  // ===============================
  // PHASE LIFECYCLE
  // ===============================

  /**
   * Enter declaration phase
   * Sets up UI and checks if it's player's turn
   */
  async enter() {
    await super.enter();

    console.log("🔸 --- Declare Phase ---");

    // Initialize phase UI (optional)
    if (this.uiRenderer) {
      this.uiRenderer.showDeclarationPhase();
    }

    // Check if it's our turn to declare
    this.checkDeclarationTurn();
  }

  /**
   * Exit declaration phase
   * Clean up state and resources
   */
  async exit() {
    // Reset input state
    this.waitingForInput = false;
    this.hasPromptedUser = false;

    await super.exit();
  }

  // ===============================
  // EVENT HANDLERS SETUP
  // ===============================

  /**
   * Register socket event handlers for this phase
   */
  registerEventHandlers() {
    this.addEventHandler("declare", this.handleDeclare);
  }

  // ===============================
  // SOCKET EVENT HANDLERS
  // ===============================

  /**
   * Handle declaration from any player (including bots)
   * @param {Object} data - Declaration data from server
   * @param {string} data.player - Player name
   * @param {number} data.value - Declaration value
   * @param {boolean} data.is_bot - Whether it's a bot
   */
  handleDeclare(data) {
    const { player, value, is_bot } = data;

    // Update game state
    this.stateManager.addDeclaration(player, value);

    // Log declaration
    this._logDeclaration(player, value, is_bot);

    // Update UI
    this.uiRenderer.updateDeclaration(player, value);

    // Check game progression
    if (this.stateManager.areAllPlayersDeclarated()) {
      this.handleAllDeclarationComplete();
    } else {
      this.checkDeclarationTurn();
    }
  }

  // ===============================
  // TURN MANAGEMENT
  // ===============================

  /**
   * Check if it's the player's turn to declare
   * Prevents multiple prompts and handles turn flow
   */
  checkDeclarationTurn() {
    // Guard: Don't check if already waiting for input
    if (this.waitingForInput || this.hasPromptedUser) {
      return;
    }

    // Check if it's our turn
    if (this.stateManager.isMyTurnToDeclare()) {
      this.promptUserDeclaration();
    }
  }

  // ===============================
  // USER INPUT HANDLING
  // ===============================

  /**
   * Prompt user for declaration input
   * Shows hand, calculates options, and displays input UI
   */
  async promptUserDeclaration() {
    // Guard: Prevent multiple prompts
    if (this.waitingForInput) return;

    // Set input state
    this.waitingForInput = true;
    this.hasPromptedUser = true;

    // Display current hand
    this.uiRenderer.displayHand(this.stateManager.myHand);

    // Calculate valid declaration options
    const { validOptions, isLastPlayer } = this._calculateDeclarationOptions();

    // Show restrictions if any
    this._showDeclarationRestrictions();

    // Log prompt
    this._logDeclarationPrompt(validOptions);

    // Show input UI
    this.uiRenderer.showDeclarationInput(validOptions, (value) => {
      this.handleUserDeclaration(value);
    });
  }

  /**
   * Handle user's declaration input
   * Validates input and sends to server
   * @param {number} value - User's declaration value
   */
  async handleUserDeclaration(value) {
    // Guard: Only process if waiting for input
    if (!this.waitingForInput) return;

    // Validate input
    if (!this._validateDeclaration(value)) {
      return; // Error already shown by validation
    }

    // Send to server
    await this._sendDeclarationToServer(value);
  }

  /**
   * Handle legacy user input format
   * For backward compatibility
   */
  async handleUserInput(input) {
    if (!(await super.handleUserInput(input))) return false;

    if (this.waitingForInput && input.type === "declaration") {
      await this.handleUserDeclaration(input.value);
      return true;
    }

    return false;
  }

  // ===============================
  // PHASE COMPLETION
  // ===============================

  /**
   * Handle completion of all declarations
   * Shows summary and transitions to next phase
   */
  handleAllDeclarationComplete() {
    const total = Object.values(this.stateManager.declarations).reduce(
      (sum, v) => sum + v,
      0
    );

    console.log(`\n✅ All players declared! Total: ${total}`);

    // Show summary in UI
    this.uiRenderer.showDeclarationSummary(this.stateManager.declarations);

    // Transition to next phase
    setTimeout(() => {
      this.completePhase({ nextPhase: "turn" });
    }, 1500);
  }

  /**
   * Check if phase is complete
   * @returns {boolean} True if all players have declared
   */
  isPhaseComplete() {
    return this.stateManager.areAllPlayersDeclarated();
  }

  /**
   * Get next phase name
   * @returns {string} Next phase identifier
   */
  getNextPhase() {
    return "turn";
  }

  // ===============================
  // PRIVATE HELPER METHODS
  // ===============================

  /**
   * Calculate valid declaration options for current player
   * @private
   * @returns {Object} Options and player info
   */
  _calculateDeclarationOptions() {
    const declarationProgress = this.stateManager.getDeclarationProgress();
    const isLastPlayer = 
      declarationProgress.declared === this.stateManager.players.length - 1;
    const validOptions = 
      this.stateManager.getValidDeclarationOptions(isLastPlayer);

    return { validOptions, isLastPlayer };
  }

  /**
   * Show declaration restrictions if applicable
   * @private
   */
  _showDeclarationRestrictions() {
    const myPlayer = this.stateManager.getMyPlayer();
    
    if (myPlayer?.zero_declares_in_a_row >= 2) {
      console.log(
        "\n⚠️ You must declare at least 1 (declared 0 twice in a row)"
      );
      this.uiRenderer.showWarning(
        "Must declare at least 1 (zero streak limit)"
      );
    }
  }

  /**
   * Log declaration prompt to console
   * @private
   * @param {number[]} validOptions - Valid declaration options
   */
  _logDeclarationPrompt(validOptions) {
    const prompt = `🟨 ${this.stateManager.playerName}, declare how many piles you want to capture`;
    const optionsText = `(options: [${validOptions.join(", ")}])`;
    console.log(`\n${prompt} ${optionsText}:`);
  }

  /**
   * Log declaration from any player
   * @private
   * @param {string} player - Player name
   * @param {number} value - Declaration value
   * @param {boolean} is_bot - Whether it's a bot
   */
  _logDeclaration(player, value, is_bot) {
    if (is_bot) {
      console.log(`🤖 ${player} declares ${value} piles.`);
    } else if (player !== this.stateManager.playerName) {
      console.log(`👤 ${player} declares ${value} piles.`);
    }
  }

  /**
   * Validate user's declaration input
   * @private
   * @param {number} value - Declaration value to validate
   * @returns {boolean} True if valid
   */
  _validateDeclaration(value) {
    const { validOptions } = this._calculateDeclarationOptions();

    if (!validOptions.includes(value)) {
      const errorMsg = `❌ Invalid declaration. Choose from [${validOptions.join(", ")}]`;
      console.log(errorMsg);
      this.uiRenderer.showError(
        `Invalid declaration. Choose from [${validOptions.join(", ")}]`
      );
      return false;
    }

    return true;
  }

  /**
   * Send declaration to server
   * @private
   * @param {number} value - Declaration value
   */
  async _sendDeclarationToServer(value) {
    try {
      const response = await fetch(
        `/api/declare?room_id=${this.stateManager.roomId}&player_name=${this.stateManager.playerName}&value=${value}`,
        { method: "POST" }
      );

      const result = await response.json();

      if (result.status === "ok") {
        console.log(`✅ You declared ${value} piles`);
        
        // Reset input state
        this.waitingForInput = false;
        this.uiRenderer.hideInput();

        // The socket event will handle the state update
      } else {
        console.error("Failed to declare:", result.message);
        this.uiRenderer.showError(result.message || "Failed to declare");
      }
    } catch (err) {
      console.error("Failed to declare:", err);
      this.uiRenderer.showError("Network error. Please try again.");
    }
  }
}