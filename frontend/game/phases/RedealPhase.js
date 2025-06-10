// frontend/game/phases/RedealPhase.js
import { BasePhase } from "./BasePhase.js";

/**
 * Redeal Phase
 * Check if player wants to redeal due to weak hand
 *
 * Rules:
 * - Player can request redeal if no pieces > 9 points
 * - Redeal multiplies scores for the round
 * - Player who redeals becomes next round starter
 */
export class RedealPhase extends BasePhase {
  constructor(stateManager, socketManager, uiRenderer) {
    super(stateManager, socketManager, uiRenderer);
    
    this.hasChecked = false;
    this.waitingForInput = false;
    this.hasPromptedUser = false;
  }

  /**
   * Enter redeal phase
   */
  async enter() {
    await super.enter();
    console.log("🔸 --- Redeal Phase ---");
    
    // Show round start info
    this.showRoundStartInfo();
    
    // Check if player should be offered redeal
    this.checkRedealEligibility();
  }

  /**
   * Show round start information
   */
  showRoundStartInfo() {
    
    // Update UI
    this.uiRenderer.showRedealPhase();
    this.uiRenderer.updatePhaseIndicator(`Round ${this.stateManager.currentRound} - Redeal Check`);
  }

  /**
   * Check if player is eligible for redeal
   */
  checkRedealEligibility() {
    // Don't check if we already checked or are waiting for input
    if (this.hasChecked || this.waitingForInput || this.hasPromptedUser) return;
    
    // Only check for human player, not bots
    if (this.stateManager.myPlayerData?.is_bot) {
      this.skipRedeal();
      return;
    }
    
    // Check hand strength
    const hasStrongPiece = this.stateManager.myHand.some((card) => {
      const match = card.match(/\((\d+)\)/);
      return match && parseInt(match[1]) > 9;
    });
    
    if (!hasStrongPiece) {
      // Eligible for redeal
      this.promptRedeal();
    } else {
      // Not eligible, skip to declaration
      this.skipRedeal();
    }
  }

  /**
   * Prompt player for redeal decision
   */
  async promptRedeal() {
    if (this.waitingForInput || this.hasPromptedUser) return;
    
    this.waitingForInput = true;
    this.hasPromptedUser = true;
    
    // Show hand
    this.uiRenderer.displayHand(this.stateManager.myHand);
    
    // Show redeal warning and options
    console.log("⚠️ You have no pieces > 9 points. Request redeal?");
    console.log("• Yes - Request new cards (increases score multiplier)");
    console.log("• No - Continue with current hand");
    
    // Show redeal input UI with callback
    this.uiRenderer.showRedealInput(['Yes', 'No'], (choice) => {
      this.handleUserRedealDecision(choice);
    });
  }

  /**
   * Handle user's redeal decision
   */
  async handleUserRedealDecision(choice) {
    if (!this.waitingForInput) return;
    
    console.log(`✅ You chose: ${choice}`);
    
    if (choice === 'Yes') {
      await this.requestRedeal();
    } else {
      console.log("📋 Continuing with current hand");
      this.skipRedeal();
    }
    
    this.waitingForInput = false;
    this.uiRenderer.hideInput();
  }

  /**
   * Send redeal request to server
   */
  async requestRedeal() {
    try {
      const response = await fetch(
        `/api/redeal?room_id=${this.stateManager.roomId}&player_name=${this.stateManager.playerName}`,
        { method: "POST" }
      );
      
      const result = await response.json();
      
      if (result.redeal_allowed) {
        console.log(`\n🔄 ${this.stateManager.playerName} has requested a redeal!`);
        console.log(`Score multiplier: x${result.multiplier}`);
        
        // Update state
        this.stateManager.redealMultiplier = result.multiplier;
        
        // Show success message
        this.uiRenderer.showSuccess(`Redeal approved! Multiplier: x${result.multiplier}`);
        
        // Server will handle dealing new cards
        // Wait for new hand via socket
      } else {
        console.log("❌ Redeal not allowed:", result.reason);
        this.uiRenderer.showError(result.reason);
        this.skipRedeal();
      }
    } catch (err) {
      console.error("Failed to request redeal:", err);
      this.uiRenderer.showError("Failed to request redeal");
      this.skipRedeal();
    }
  }

  /**
   * Skip redeal and proceed to declaration
   */
  skipRedeal() {
    if (this.hasChecked) return;
    
    this.hasChecked = true;
    
    // Short delay before moving to declaration
    setTimeout(() => {
      this.completePhase();
    }, 1000);
  }

  /**
   * Register event handlers
   */
  registerEventHandlers() {
    // Listen for redeal events
    this.addEventHandler('redeal', this.handleRedeal);
    this.addEventHandler('new_hand', this.handleNewHand);
    this.addEventHandler('new_round', this.handleNewRound);
  }

  /**
   * Handle new round event from server
   */
  handleNewRound(data) {
    // Update hand
    this.stateManager.updateHand(data.hands[this.stateManager.playerName]);
    this.stateManager.currentRound = data.round;
    this.stateManager.roundStarter = data.starter;
    
    console.log("✅ New round after redeal!");
    
    // Go to declaration phase
    setTimeout(() => {
      this.completePhase({ nextPhase: "declaration" });
    }, 1500);
  }

  /**
   * Handle redeal event from server
   */
  handleRedeal(data) {
    console.log(`\n🔄 ${data.player} has requested a redeal!`);
    console.log(`Score multiplier is now x${data.multiplier}`);
    
    // Update multiplier
    this.stateManager.redealMultiplier = data.multiplier;
    
    // Show in UI
    this.uiRenderer.showSuccess(
      `${data.player} requested redeal. Multiplier: x${data.multiplier}`
    );
  }

  /**
   * Handle new hand after redeal
   */
  handleNewHand(data) {
    if (data.player === this.stateManager.playerName) {
      // Update our hand
      this.stateManager.updateHand(data.hand);
      console.log("✅ Received new hand after redeal");
      
      // Reset state and check again (in case still weak)
      this.hasChecked = false;
      this.waitingForInput = false;
      this.hasPromptedUser = false;
      
      this.checkRedealEligibility();
    }
  }

  /**
   * Handle user input
   */
  async handleUserInput(input) {
    if (!(await super.handleUserInput(input))) return false;
    
    // Handle redeal choice input
    if (this.waitingForInput && input.type === "redeal_choice") {
      await this.handleUserRedealDecision(input.choice);
      return true;
    }
    
    return false;
  }

  /**
   * Get next phase
   */
  getNextPhase() {
    return "declaration";
  }

  /**
   * Exit phase
   */
  async exit() {
    // Reset state
    this.hasChecked = false;
    this.waitingForInput = false;
    this.hasPromptedUser = false;
    
    await super.exit();
  }
}