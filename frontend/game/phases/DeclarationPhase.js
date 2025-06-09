// frontend/game/phases/DeclarationPhase.js

import { BasePhase } from './BasePhase.js';

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
  constructor(stateManager, socketManager, uiManager) {
    super(stateManager, socketManager, uiManager);
    
    this.waitingForInput = false;
    this.hasPromptedUser = false;
  }

  /**
   * Enter declaration phase
   */
  async enter() {
    await super.enter();
    
    console.log("🔸 --- Declare Phase ---");
    
    // Initialize declarations for all players
    this.stateManager.players.forEach(p => {
      this.stateManager.declarations[p.name] = undefined;
    });
    
    // Show declaration UI
    this.uiManager.showDeclarationPhase();
    
    // Check if it's our turn to declare
    this.checkDeclarationTurn();
  }

  /**
   * Register socket event handlers
   */
  registerEventHandlers() {
    // Listen for declaration events
    this.addEventHandler('declare', this.handleDeclare);
  }

  /**
   * Handle declaration from any player
   */
  handleDeclare(data) {
    const { player, value, is_bot } = data;
    
    // Update state
    this.stateManager.addDeclaration(player, value);
    
    // Show in UI
    if (is_bot) {
      console.log(`🤖 ${player} declares ${value} piles.`);
    } else if (player !== this.stateManager.playerName) {
      console.log(`👤 ${player} declares ${value} piles.`);
    }
    
    // Update UI
    this.uiManager.updateDeclaration(player, value);
    
    // Check if all players have declared
    if (this.stateManager.areAllPlayersDeclarated()) {
      this.handleAllDeclarationComplete();
    } else {
      // Check if it's now our turn
      this.checkDeclarationTurn();
    }
  }

  /**
   * Check if it's the player's turn to declare
   */
  checkDeclarationTurn() {
    // Don't check if we're waiting for input
    if (this.waitingForInput || this.hasPromptedUser) return;
    
    // Check if it's our turn
    if (this.stateManager.isMyTurnToDeclare()) {
      this.promptUserDeclaration();
    }
  }

  /**
   * Prompt user for declaration
   */
  async promptUserDeclaration() {
    if (this.waitingForInput) return;
    
    this.waitingForInput = true;
    this.hasPromptedUser = true;
    
    // Show hand
    this.uiManager.displayHand(this.stateManager.myHand);
    
    // Calculate valid options
    const declarationProgress = this.stateManager.getDeclarationProgress();
    const isLastPlayer = declarationProgress.declared === this.stateManager.players.length - 1;
    const validOptions = this.stateManager.getValidDeclarationOptions(isLastPlayer);
    
    // Show any restrictions
    const myPlayer = this.stateManager.getMyPlayer();
    if (myPlayer?.zero_declares_in_a_row >= 2) {
      console.log("\n⚠️ You must declare at least 1 (declared 0 twice in a row)");
      this.uiManager.showWarning("Must declare at least 1 (zero streak limit)");
    }
    
    // Create declaration prompt
    const prompt = `🟨 ${this.stateManager.playerName}, declare how many piles you want to capture`;
    const optionsText = `(options: [${validOptions.join(", ")}])`;
    
    console.log(`\n${prompt} ${optionsText}:`);
    
    // Show input UI
    this.uiManager.showDeclarationInput(validOptions, (value) => {
      this.handleUserDeclaration(value);
    });
  }

  /**
   * Handle user's declaration input
   */
  async handleUserDeclaration(value) {
    if (!this.waitingForInput) return;
    
    // Validate input
    const declarationProgress = this.stateManager.getDeclarationProgress();
    const isLastPlayer = declarationProgress.declared === this.stateManager.players.length - 1;
    const validOptions = this.stateManager.getValidDeclarationOptions(isLastPlayer);
    
    if (!validOptions.includes(value)) {
      console.log(`❌ Invalid declaration. Choose from [${validOptions.join(", ")}]`);
      this.uiManager.showError(`Invalid declaration. Choose from [${validOptions.join(", ")}]`);
      return;
    }
    
    // Send declaration to server
    try {
      const response = await fetch(
        `/api/declare?room_id=${this.stateManager.roomId}&player_name=${this.stateManager.playerName}&value=${value}`,
        { method: "POST" }
      );
      
      const result = await response.json();
      
      if (result.status === "ok") {
        console.log(`✅ You declared ${value} piles`);
        this.waitingForInput = false;
        this.uiManager.hideDeclarationInput();
        
        // The socket event will handle the state update
      } else {
        console.error("Failed to declare:", result.message);
        this.uiManager.showError(result.message || "Failed to declare");
      }
    } catch (err) {
      console.error("Failed to declare:", err);
      this.uiManager.showError("Network error. Please try again.");
    }
  }

  /**
   * Handle user input
   */
  async handleUserInput(input) {
    if (!await super.handleUserInput(input)) return false;
    
    if (this.waitingForInput && input.type === 'declaration') {
      await this.handleUserDeclaration(input.value);
      return true;
    }
    
    return false;
  }

  /**
   * Handle all players declared
   */
  handleAllDeclarationComplete() {
    const total = Object.values(this.stateManager.declarations)
      .reduce((sum, v) => sum + v, 0);
    
    console.log(`\n✅ All players declared! Total: ${total}`);
    
    // Show summary in UI
    this.uiManager.showDeclarationSummary(this.stateManager.declarations);
    
    // Phase is complete - transition to turn phase
    setTimeout(() => {
      this.completePhase({ nextPhase: 'turn' });
    }, 1500);
  }

  /**
   * Check if phase is complete
   */
  isPhaseComplete() {
    return this.stateManager.areAllPlayersDeclarated();
  }

  /**
   * Get next phase
   */
  getNextPhase() {
    return 'turn';
  }

  /**
   * Exit phase
   */
  async exit() {
    // Hide declaration UI
    this.uiManager.hideDeclarationPhase();
    
    // Reset state
    this.waitingForInput = false;
    this.hasPromptedUser = false;
    
    await super.exit();
  }
}