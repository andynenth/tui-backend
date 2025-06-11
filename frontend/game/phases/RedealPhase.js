// frontend/game/phases/RedealPhase.js
import { BasePhase } from "./BasePhase.js";

/**
 * Redeal Phase - Fixed with debugging
 * Check if player wants to redeal due to weak hand
 */
export class RedealPhase extends BasePhase {
  constructor(stateManager, socketManager, uiRenderer) {
    super(stateManager, socketManager, uiRenderer);
    
    this.hasChecked = false;
    this.waitingForInput = false;
    this.hasPromptedUser = false;
    
    console.log("🔄 RedealPhase constructor complete");
  }

  /**
   * Enter redeal phase
   */
  async enter() {
    await super.enter();
    console.log("🔸 --- REDEAL PHASE START ---");
    
    // Debug current state
    console.log("🔍 RedealPhase DEBUG:");
    console.log("  - Player:", this.stateManager.playerName);
    console.log("  - Hand:", this.stateManager.myHand);
    console.log("  - Current round:", this.stateManager.currentRound);
    console.log("  - UI Renderer available:", !!this.uiRenderer);
    
    // Show round start info
    this.showRoundStartInfo();
    
    // Start redeal check process
    setTimeout(() => {
      this.checkRedealEligibility();
    }, 500);
  }

  /**
   * Register event handlers
   */
  registerEventHandlers() {
    console.log("🔗 RedealPhase: Registering event handlers");
    
    this.addEventHandler('redeal_response', this.handleRedealResponse);
    this.addEventHandler('new_hand', this.handleNewHand);
    this.addEventHandler('redeal_complete', this.handleRedealComplete);
    this.addEventHandler('new_round', this.handleNewRound);
    
    console.log("✅ RedealPhase: Event handlers registered");
  }

  /**
   * Show round start information
   */
  showRoundStartInfo() {
    console.log("📋 RedealPhase: Showing round start info");
    
    if (this.uiRenderer) {
      try {
        this.uiRenderer.showRedealPhase();
        this.uiRenderer.updatePhaseIndicator(`Round ${this.stateManager.currentRound} - Redeal Check`);
        console.log("✅ UI updated for redeal phase");
      } catch (error) {
        console.error("❌ Error updating UI:", error);
      }
    } else {
      console.warn("⚠️ UI Renderer not available");
    }
  }

  /**
   * Check if player is eligible for redeal
   */
  checkRedealEligibility() {
    console.log("🔍 RedealPhase: Checking redeal eligibility");
    console.log("  - hasChecked:", this.hasChecked);
    console.log("  - waitingForInput:", this.waitingForInput);
    console.log("  - hasPromptedUser:", this.hasPromptedUser);
    
    // Don't check if we already checked or are waiting for input
    if (this.hasChecked || this.waitingForInput || this.hasPromptedUser) {
      console.log("🚫 Skipping redeal check - already processed");
      return;
    }
    
    // Only check for human player, not bots
    if (this.stateManager.myPlayerData?.is_bot) {
      console.log("🤖 Player is bot, skipping redeal");
      this.skipRedeal();
      return;
    }
    
    console.log("🎯 Analyzing hand for redeal eligibility...");
    
    // Check hand strength
    const hand = this.stateManager.myHand || [];
    console.log("📋 Current hand:", hand);
    
    if (hand.length === 0) {
      console.warn("⚠️ No hand data available, skipping redeal");
      this.skipRedeal();
      return;
    }
    
    const strongPieces = [];
    const hasStrongPiece = hand.some((card, index) => {
      const match = card.match(/\((\d+)\)/);
      const points = match ? parseInt(match[1]) : 0;
      
      console.log(`  Card ${index + 1}: "${card}" = ${points} points`);
      
      if (points > 9) {
        strongPieces.push(card);
        return true;
      }
      return false;
    });
    
    console.log("💪 Strong pieces (>9 points):", strongPieces);
    console.log("🎯 Has strong pieces:", hasStrongPiece);
    
    if (!hasStrongPiece) {
      console.log("⚠️ WEAK HAND DETECTED - Eligible for redeal!");
      this.promptRedeal();
    } else {
      console.log("✅ Strong hand - No redeal needed");
      this.skipRedeal();
    }
  }

  /**
   * Prompt player for redeal decision
   */
  async promptRedeal() {
    if (this.waitingForInput || this.hasPromptedUser) {
      console.log("🚫 Already prompting for redeal");
      return;
    }
    
    console.log("❓ RedealPhase: Prompting user for redeal decision");
    
    this.waitingForInput = true;
    this.hasPromptedUser = true;
    
    // Show hand in UI
    if (this.uiRenderer) {
      try {
        this.uiRenderer.displayHand(this.stateManager.myHand);
        
        // Show redeal warning and options
        console.log("⚠️ You have no pieces > 9 points. Request redeal?");
        console.log("• Yes - Request new cards (increases score multiplier)");
        console.log("• No - Continue with current hand");
        
        // Show redeal input UI with callback
        this.uiRenderer.showRedealInput(['Yes', 'No'], (choice) => {
          console.log(`🎯 User selected: ${choice}`);
          this.handleUserRedealDecision(choice);
        });
        
        console.log("✅ Redeal prompt shown to user");
      } catch (error) {
        console.error("❌ Error showing redeal prompt:", error);
        this.showError("Failed to show redeal prompt");
        this.skipRedeal();
      }
    } else {
      console.error("❌ Cannot prompt - UI Renderer not available");
      this.skipRedeal();
    }
  }

  /**
   * Handle user's redeal decision
   */
  async handleUserRedealDecision(choice) {
    if (!this.waitingForInput) {
      console.log("🚫 Not waiting for input, ignoring decision");
      return;
    }
    
    console.log(`✅ RedealPhase: User chose "${choice}"`);
    
    this.waitingForInput = false;
    
    if (this.uiRenderer) {
      this.uiRenderer.hideInput();
    }
    
    if (choice === 'Yes') {
      console.log("🔄 User wants to redeal - sending request to server");
      await this.requestRedeal();
    } else {
      console.log("📋 User keeping current hand");
      this.skipRedeal();
    }
  }

  /**
   * Send redeal request to server
   */
  async requestRedeal() {
    console.log("📤 RedealPhase: Sending redeal request to server");
    
    try {
      const url = `/api/redeal?room_id=${this.stateManager.roomId}&player_name=${this.stateManager.playerName}`;
      console.log("📡 Request URL:", url);
      
      const response = await fetch(url, { method: "POST" });
      const result = await response.json();
      
      console.log("📥 Redeal response:", result);
      
      if (result.redeal_allowed) {
        console.log(`🎉 Redeal approved! Multiplier: x${result.multiplier}`);
        
        // Update state
        this.stateManager.redealMultiplier = result.multiplier;
        
        // Show success message
        this.showSuccess(`Redeal approved! Multiplier: x${result.multiplier}`);
        
        // Wait for server to send new hand
        console.log("⏳ Waiting for new hand from server...");
        
      } else {
        console.error("❌ Redeal not allowed:", result.reason);
        this.showError(result.reason || "Redeal not allowed");
        this.skipRedeal();
      }
    } catch (err) {
      console.error("❌ Failed to request redeal:", err);
      this.showError("Failed to request redeal");
      this.skipRedeal();
    }
  }

  /**
   * Skip redeal and proceed to declaration
   */
  skipRedeal() {
    if (this.hasChecked) {
      console.log("🚫 Already skipped redeal");
      return;
    }
    
    console.log("⏭️ RedealPhase: Skipping redeal, proceeding to declaration");
    
    this.hasChecked = true;
    
    // Short delay before moving to declaration
    setTimeout(() => {
      console.log("🎯 RedealPhase: Completing phase → declaration");
      this.completePhase();
    }, 1000);
  }

  /**
   * Handle redeal response from server
   */
  handleRedealResponse(data) {
    console.log("📥 RedealPhase: Redeal response received:", data);
    
    if (data.player === this.stateManager.playerName) {
      console.log("✅ This is our redeal response");
      // Handle our own redeal response if needed
    } else {
      console.log(`🔄 Another player (${data.player}) made redeal decision: ${data.choice}`);
    }
  }

  /**
   * Handle new hand after redeal
   */
  handleNewHand(data) {
    console.log("✨ RedealPhase: New hand received:", data);
    
    if (data.player === this.stateManager.playerName) {
      console.log("🎉 Received our new hand after redeal!");
      console.log("New hand:", data.hand);
      
      // Update our hand
      this.stateManager.updateHand(data.hand);
      
      // Reset state and check again (in case still weak)
      this.hasChecked = false;
      this.waitingForInput = false;
      this.hasPromptedUser = false;
      
      console.log("🔄 Checking new hand for redeal eligibility...");
      setTimeout(() => {
        this.checkRedealEligibility();
      }, 500);
    }
  }

  /**
   * Handle redeal completion
   */
  handleRedealComplete(data) {
    console.log("🎯 RedealPhase: Redeal process complete:", data);
    
    // Update game state if provided
    if (data.new_round_data) {
      this.stateManager.updateFromRoundData(data.new_round_data);
    }
    
    console.log("✅ RedealPhase: Moving to declaration phase");
    setTimeout(() => {
      this.completePhase();
    }, 1000);
  }

  /**
   * Handle new round event from server
   */
  handleNewRound(data) {
    console.log("🔄 RedealPhase: New round after redeal:", data);
    
    // Update hand and round info
    if (data.hands && data.hands[this.stateManager.playerName]) {
      this.stateManager.updateHand(data.hands[this.stateManager.playerName]);
    }
    
    this.stateManager.currentRound = data.round;
    this.stateManager.roundStarter = data.starter;
    
    console.log("✅ New round data updated!");
    
    // Go to declaration phase
    setTimeout(() => {
      this.completePhase();
    }, 1500);
  }

  /**
   * Handle user input
   */
  async handleUserInput(input) {
    if (!(await super.handleUserInput(input))) return false;
    
    console.log("⌨️ RedealPhase: User input received:", input);
    
    // Handle redeal choice input
    if (this.waitingForInput && input.type === "redeal_choice") {
      await this.handleUserRedealDecision(input.choice);
      return true;
    }
    
    // Handle keyboard shortcuts
    if (this.waitingForInput && input.type === "keypress") {
      if (input.key === "1" || input.key.toLowerCase() === "y") {
        await this.handleUserRedealDecision("Yes");
        return true;
      } else if (input.key === "2" || input.key.toLowerCase() === "n") {
        await this.handleUserRedealDecision("No");
        return true;
      }
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
    console.log("🔹 RedealPhase: Exiting phase");
    
    // Reset state
    this.hasChecked = false;
    this.waitingForInput = false;
    this.hasPromptedUser = false;
    
    await super.exit();
    
    console.log("✅ RedealPhase: Exit complete");
  }
}