// frontend/game/phases/RedealPhase.js

import { BasePhase } from './BasePhase.js';

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
  constructor(stateManager, socketManager, uiManager) {
    super(stateManager, socketManager, uiManager);
    
    this.hasChecked = false;
    this.waitingForResponse = false;
  }

  /**
   * Enter redeal phase
   */
  async enter() {
    await super.enter();
    
    console.log("\n" + "=".repeat(50));
    console.log(`ROUND ${this.stateManager.currentRound}`);
    console.log("=".repeat(50));
    
    // Show round start info
    this.showRoundStartInfo();
    
    // Check if player should be offered redeal
    this.checkRedealEligibility();
  }

  /**
   * Show round start information
   */
  showRoundStartInfo() {
    const starter = this.stateManager.roundStarter;
    let startReason = "Won previous round";
    
    if (this.stateManager.currentRound === 1) {
      // Check if starter has GENERAL_RED
      const starterHand = this.stateManager.gameData.hands?.[starter];
      if (starterHand?.some(card => card.includes("GENERAL_RED"))) {
        startReason = "Has GENERAL_RED";
      }
    }
    
    console.log(`${starter} starts the game (${startReason})\n`);
    
    // Update UI
    this.uiRenderer.showRedealPhase();
    this.uiRenderer.updatePhaseIndicator(`Round ${this.stateManager.currentRound} - Redeal Check`);
  }

  /**
   * Check if player is eligible for redeal
   */
  checkRedealEligibility() {
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
    if (this.waitingForResponse) return;
    
    this.waitingForResponse = true;
    
    // Show hand
    this.uiRenderer.displayHand(this.stateManager.myHand);
    
    // Show redeal prompt
    console.log("⚠️ You have no pieces > 9 points. Request redeal?");
    
    const response = await this.uiRenderer.showInput(
      "Request redeal? (y/n):",
      (input) => {
        const lower = input.toLowerCase();
        return {
          valid: lower === 'y' || lower === 'n',
          message: "Please enter 'y' or 'n'"
        };
      }
    );
    
    if (response.toLowerCase() === 'y') {
      await this.requestRedeal();
    } else {
      this.skipRedeal();
    }
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
    this.uiRenderer.showSuccess(`${data.player} requested redeal. Multiplier: x${data.multiplier}`);
  }

  /**
   * Handle new hand after redeal
   */
  handleNewHand(data) {
    if (data.player === this.stateManager.playerName) {
      // Update our hand
      this.stateManager.updateHand(data.hand);
      console.log("✅ Received new hand after redeal");
      
      // Check again (in case still weak)
      this.hasChecked = false;
      this.waitingForResponse = false;
      this.checkRedealEligibility();
    }
  }

  /**
   * Get next phase
   */
  getNextPhase() {
    return 'declaration';
  }

  /**
   * Handle user input
   */
  async handleUserInput(input) {
    if (!await super.handleUserInput(input)) return false;
    
    // This phase uses the prompt system
    return false;
  }

  /**
   * Exit phase
   */
  async exit() {
    this.hasChecked = false;
    this.waitingForResponse = false;
    
    await super.exit();
  }
}