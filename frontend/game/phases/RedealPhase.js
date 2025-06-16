// frontend/game/phases/RedealPhase.js

import { BasePhase } from "./BasePhase.js";

/**
 * Redeal Phase
 * Check if player wants to redeal due to weak hand
 *
 * Rules:
 * - Only human players can request redeal
 * - Weak hand = no pieces with >9 points
 * - Redeal increases score multiplier
 * - Limited number of redeals per game
 */
export class RedealPhase extends BasePhase {
  constructor(stateManager, socketManager, uiRenderer) {
    super(stateManager, socketManager, uiRenderer);

    this.waitingForInput = false;
    this.hasPromptedUser = false;
    this.hasChecked = false;
    this.isWaitingForOthers = false;

    // ✅ เพิ่ม debug tracking
    this.receivedEvents = [];
    this.handlersRegistered = false;
  }

  // ===============================
  // PHASE LIFECYCLE
  // ===============================

  /**
   * Enter redeal phase
   * Sets up UI and checks redeal eligibility
   */
  async enter() {
    await super.enter();

    console.log("🔸 --- REDEAL PHASE START ---");
    this._logDebugInfo();
    this.uiRenderer.showRedealPhase();

    // ✅ แก้ไข: Register handlers ก่อน check eligibility
    this.registerEventHandlers();

    // ✅ เพิ่ม: Process any buffered events
    this._processBufferedEvents();

    setTimeout(() => {
      this.checkRedealEligibility();
    }, 500);
  }

  /**
   * Exit redeal phase
   * Clean up state and resources
   */
  async exit() {
    console.log("🔹 RedealPhase: Exiting phase");

    // Reset input state
    this.hasChecked = false;
    this.waitingForInput = false;
    this.hasPromptedUser = false;

    await super.exit();

    console.log("✅ RedealPhase: Exit complete");
  }

  // ===============================
  // EVENT HANDLERS SETUP
  // ===============================

  /**
   * Register socket event handlers for this phase
   */
  registerEventHandlers() {
    console.log("🔧 RedealPhase: Registering handlers...");

    // ✅ เพิ่ม debug wrapper
    this.addEventHandler("redeal_phase_started", (data) => {
      console.log("🎯 DEBUG: redeal_phase_started received:", data);
      this.handleRedealPhaseStarted(data);
    });

    this.addEventHandler("redeal_prompt", (data) => {
      console.log("🎯 DEBUG: redeal_prompt received:", data);
      this.handleRedealPrompt(data);
    });

    this.addEventHandler("redeal_decision_made", (data) => {
      console.log("🎯 DEBUG: redeal_decision_made received:", data);
      this.handleRedealDecision(data);
    });

    this.addEventHandler("redeal_phase_complete", (data) => {
      console.log("🎯 DEBUG: redeal_phase_complete received:", data);
      this.handleRedealComplete(data);
    });

    this.handlersRegistered = true;
    console.log("✅ RedealPhase: Event handlers registered with debug");
  }

  _processBufferedEvents() {
    console.log("🔍 Processing buffered events:", this.receivedEvents.length);

    this.receivedEvents.forEach(({ event, data }) => {
      console.log(`📦 Processing buffered event: ${event}`, data);

      switch (event) {
        case "redeal_phase_started":
          this.handleRedealPhaseStarted(data);
          break;
        case "redeal_prompt":
          this.handleRedealPrompt(data);
          break;
        // ... other events
      }
    });

    this.receivedEvents = []; // Clear buffer
  }

  // ===============================
  // SOCKET EVENT HANDLERS
  // ===============================

  handleRedealPhaseStarted(data) {
    console.log("🔔 RedealPhase: handleRedealPhaseStarted called with:", data);

    const totalPlayers = data.total_players || 0;
    console.log(`📊 Total weak players: ${totalPlayers}`);

    if (totalPlayers === 0) {
      console.log("✅ No redeal needed, waiting for completion...");
    } else {
      console.log("⏳ Waiting for sequential redeal decisions...");
      this.isWaitingForOthers = true;

      // ✅ เพิ่ม check method exists
      if (this.uiRenderer.showWaitingMessage) {
        this.uiRenderer.showWaitingMessage("Waiting for redeal decisions...");
      } else {
        console.warn("⚠️ uiRenderer.showWaitingMessage not available");
      }
    }
  }

  handleRedealPrompt(data) {
    console.log("📨 RedealPhase: handleRedealPrompt called with:", data);

    if (data.target_player === this.stateManager.playerName) {
      console.log(
        `🎯 It's our turn! (${data.player_index + 1}/${data.total_players})`
      );
      this.isWaitingForOthers = false;
      this.promptRedeal();
    } else {
      console.log(
        `⏳ Waiting for ${data.target_player} (${data.player_index + 1}/${
          data.total_players
        })`
      );
      this.isWaitingForOthers = true;

      if (this.uiRenderer.showWaitingMessage) {
        this.uiRenderer.showWaitingMessage(
          `Waiting for ${data.target_player} to decide...`
        );
      }
    }
  }

  handleRedealDecision(data) {
    console.log("📊 Redeal decision made:", data);

    if (data.is_bot) {
      console.log(`🤖 ${data.player} chose: ${data.choice}`);
    } else {
      console.log(`👤 ${data.player} chose: ${data.choice}`);
    }

    // Safe call to showDecisionResult (check if method exists)
    if (this.uiRenderer.showDecisionResult) {
      this.uiRenderer.showDecisionResult(data.player, data.choice);
    }

    // If there are remaining players, show waiting message
    if (data.remaining_players > 0) {
      this.isWaitingForOthers = true;

      // Safe call to showWaitingMessage
      if (this.uiRenderer.showWaitingMessage) {
        this.uiRenderer.showWaitingMessage(
          `${data.remaining_players} players remaining...`
        );
      }
    }
  }

  handleRedealComplete(data) {
    console.log("✅ Redeal phase complete:", data);

    this.isWaitingForOthers = false;

    // ไป declaration phase
    setTimeout(() => {
      this.completePhase({ nextPhase: "declaration" });
    }, 1000);
  }

  checkRedealEligibility() {
    // ✅ แก้ไข: รอ backend แทนที่จะ check local
    console.log("🔍 RedealPhase: Waiting for backend redeal sequence...");

    // ไม่ต้อง check local แล้ว เพราะ backend จะควบคุม
    if (this.isWaitingForOthers) {
      console.log("⏳ Still waiting for backend redeal process...");
      return;
    }
  }

  async _sendRedealRequest() {
    console.log("📤 RedealPhase: Sending redeal request to backend");

    const choice = "accept"; // or get from UI
    const url = `/api/redeal-decision?room_id=${this.stateManager.roomId}&player_name=${this.stateManager.playerName}&choice=${choice}`;

    try {
      const response = await fetch(url, { method: "POST" });
      const result = await response.json();
      console.log("📥 Redeal request sent:", result);

      // Backend จะส่ง event กลับมา ไม่ต้อง handle ที่นี่
    } catch (error) {
      console.error("❌ Failed to send redeal decision:", error);
      this.showError("Failed to send redeal decision");
    }
  }

  /**
   * Handle redeal response from server
   * @param {Object} data - Redeal response data
   * @param {string} data.player - Player name
   * @param {string} data.choice - "Yes" or "No"
   */
  handleRedealResponse(data) {
    console.log("📥 RedealPhase: Redeal response received:", data);

    if (data.player === this.stateManager.playerName) {
      console.log("✅ This is our redeal response");
    } else {
      console.log(
        `🔄 Another player (${data.player}) made redeal decision: ${data.choice}`
      );
    }
  }

  /**
   * Handle new hand after redeal
   * @param {Object} data - New hand data
   * @param {string} data.player - Player name
   * @param {string[]} data.hand - New hand cards
   */
  handleNewHand(data) {
    console.log("✨ RedealPhase: New hand received:", data);

    if (data.player === this.stateManager.playerName) {
      console.log("🎉 Received our new hand after redeal!");
      console.log("New hand:", data.hand);

      // Update our hand
      this.stateManager.updateHand(data.hand);

      // Reset and recheck new hand
      this._resetRedealState();
      setTimeout(() => {
        this.checkRedealEligibility();
      }, 500);
    }
  }

  /**
   * Handle redeal completion from server
   * @param {Object} data - Completion data
   */
  //   handleRedealComplete(data) {
  //     console.log("🎯 RedealPhase: Redeal process complete:", data);

  //     // Update game state if provided
  //     if (data.new_round_data) {
  //       this.stateManager.updateFromRoundData(data.new_round_data);
  //     }

  //     console.log("✅ RedealPhase: Moving to declaration phase");
  //     setTimeout(() => {
  //       this.completePhase();
  //     }, 1000);
  //   }

  /**
   * Handle new round event from server
   * @param {Object} data - New round data
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

  // ===============================
  // REDEAL MANAGEMENT
  // ===============================

  /**
   * Check if player is eligible for redeal
   * Analyzes hand strength and prompts if needed
//    */
  //   checkRedealEligibility() {
  //     console.log("🔍 RedealPhase: Checking redeal eligibility");

  //     // Guard: Don't check if already processed
  //     if (this.hasChecked || this.waitingForInput || this.hasPromptedUser) {
  //       console.log("🚫 Skipping redeal check - already processed");
  //       return;
  //     }

  //     // Guard: Skip for bots
  //     if (this.stateManager.myPlayerData?.is_bot) {
  //       console.log("🤖 Player is bot, skipping redeal");
  //       this.skipRedeal();
  //       return;
  //     }

  //     // Analyze hand strength
  //     const handAnalysis = this._analyzeHandStrength();

  //     if (!handAnalysis.hasStrongPiece) {
  //       console.log("⚠️ WEAK HAND DETECTED - Eligible for redeal!");
  //       this.promptRedeal();
  //     } else {
  //       console.log("✅ Strong hand - No redeal needed");
  //       this.skipRedeal();
  //     }
  //   }

  /**
   * Skip redeal and proceed to declaration
   */
  skipRedeal() {
    // Guard: Prevent multiple skips
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

  // ===============================
  // USER INPUT HANDLING
  // ===============================

  /**
   * Prompt user for redeal decision
   * Shows hand and redeal options
   */
  async promptRedeal() {
    // Guard: Prevent multiple prompts
    if (this.waitingForInput || this.hasPromptedUser) {
      console.log("🚫 Already prompting for redeal");
      return;
    }

    console.log("❓ RedealPhase: Prompting user for redeal decision");

    // Set input state
    this.waitingForInput = true;
    this.hasPromptedUser = true;

    // Display current hand
    this.uiRenderer.displayHand(this.stateManager.myHand);

    // Show redeal information
    this._showRedealInformation();

    // Show redeal input UI
    this.uiRenderer.showRedealInput(["Yes", "No"], (choice) => {
      this.handleUserRedealDecision(choice);
    });

    console.log("✅ Redeal prompt shown to user");
  }

  /**
   * Handle user's redeal decision
   * @param {string} choice - User's choice ("Yes" or "No")
   */
  async handleUserRedealDecision(choice) {
    if (!this.waitingForInput) {
      console.log("🚫 Not waiting for input, ignoring decision");
      return;
    }

    console.log(`✅ RedealPhase: User chose "${choice}"`);

    this.waitingForInput = false;
    this.uiRenderer.hideInput();

    if (choice === "Yes") {
      console.log("🔄 User wants to redeal - sending 'accept' to backend");
      await this._sendRedealDecision("accept");
    } else {
      console.log(
        "📋 User keeping current hand - sending 'decline' to backend"
      );
      await this._sendRedealDecision("decline");
    }
  }

  async _sendRedealDecision(choice) {
    console.log(`📤 RedealPhase: Sending redeal decision: ${choice}`);

    const url = `/api/redeal-decision?room_id=${this.stateManager.roomId}&player_name=${this.stateManager.playerName}&choice=${choice}`;

    try {
      const response = await fetch(url, { method: "POST" });
      const result = await response.json();
      console.log("📥 Redeal decision sent successfully:", result);
    } catch (error) {
      console.error("❌ Failed to send redeal decision:", error);
      this.showError("Failed to send redeal decision");
    }
  }

  /**
   * Handle legacy user input format
   * For backward compatibility
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

  // ===============================
  // PHASE COMPLETION
  // ===============================

  /**
   * Get next phase name
   * @returns {string} Next phase identifier
   */
  getNextPhase() {
    return "declaration";
  }

  // ===============================
  // PRIVATE HELPER METHODS
  // ===============================

  /**
   * Log debug information
   * @private
   */
  _logDebugInfo() {
    console.log("🔍 RedealPhase DEBUG:");
    console.log("  - Player:", this.stateManager.playerName);
    console.log("  - Hand:", this.stateManager.myHand);
    console.log("  - Current round:", this.stateManager.currentRound);
    console.log("  - UI Renderer available:", !!this.uiRenderer);
  }

  /**
   * Analyze hand strength for redeal eligibility
   * @private
   * @returns {Object} Analysis result
   */
  _analyzeHandStrength() {
    console.log("🎯 Analyzing hand for redeal eligibility...");

    const hand = this.stateManager.myHand || [];
    console.log("📋 Current hand:", hand);

    if (hand.length === 0) {
      console.warn("⚠️ No hand data available, skipping redeal");
      return { hasStrongPiece: true, strongPieces: [] };
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

    return { hasStrongPiece, strongPieces };
  }

  /**
   * Show redeal information to user
   * @private
   */
  _showRedealInformation() {
    console.log("⚠️ You have no pieces > 9 points. Request redeal?");
    console.log("• Yes - Request new cards (increases score multiplier)");
    console.log("• No - Continue with current hand");
  }

  /**
   * Send redeal request to server
   * @private
   */
  //   async _sendRedealRequest() {
  //     const choice = "accept"; // or "decline"
  //     const url = `/api/redeal-decision?room_id=${this.stateManager.roomId}&player_name=${this.stateManager.playerName}&choice=${choice}`;

  //     const response = await fetch(url, { method: "POST" });
  //     const result = await response.json();
  //     // ไม่ต้อง handle response เพราะ backend จะส่ง event กลับมา
  //   }

  /**
   * Reset redeal state for recheck
   * @private
   */
  _resetRedealState() {
    this.hasChecked = false;
    this.waitingForInput = false;
    this.hasPromptedUser = false;
  }
}
