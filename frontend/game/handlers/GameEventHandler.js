// frontend/game/handlers/GameEventHandler.js

/**
 * Handles all game-related socket events
 * Bridges between socket events and game state/phases
 */
export class GameEventHandler {
  constructor(stateManager, phaseManager, socketManager) {
    this.stateManager = stateManager;
    this.phaseManager = phaseManager;
    this.socketManager = socketManager;

    // Bind event handlers - เพิ่ม redeal events
    this.eventHandlers = {
      // Existing handlers
      declare: this.handleDeclare.bind(this),
      all_declared: this.handleAllDeclared.bind(this),
      play: this.handlePlay.bind(this),
      turn_end: this.handleTurnEnd.bind(this),
      round_end: this.handleRoundEnd.bind(this),
      game_end: this.handleGameEnd.bind(this),
      player_quit: this.handlePlayerQuit.bind(this),
      room_closed: this.handleRoomClosed.bind(this),
      error: this.handleError.bind(this),

      redeal_phase_started: this.handleRedealPhaseStarted.bind(this),
      redeal_prompt: this.handleRedealPrompt.bind(this),
      redeal_decision_made: this.handleRedealDecisionMade.bind(this),

      redeal_response: this.handleRedealResponse.bind(this),
      new_hand: this.handleNewHand.bind(this),
      redeal_complete: this.handleRedealComplete.bind(this),
      weak_hands_check: this.handleWeakHandsCheck.bind(this),
    };

    console.log("GameEventHandler initialized");
  }

  /**
   * Connect to game WebSocket and set up listeners
   */
  async connect() {
    console.log("📡 Connecting game event handlers");

    // Connect to game WebSocket
    await this.socketManager.connect(this.stateManager.roomId);

    // Set up event listeners
    Object.entries(this.eventHandlers).forEach(([event, handler]) => {
      this.socketManager.on(event, handler);
    });

    console.log("✅ Game event handlers connected");
  }

  /**
   * Handle redeal response from players (including bots)
   */
  handleRedealResponse(data) {
    console.log("🔄 Redeal response received:", data);

    // Forward to current phase if it's redeal phase
    const currentPhase = this.phaseManager.getCurrentPhase();
    if (currentPhase && currentPhase.name === "redeal") {
      currentPhase.handleRedealResponse(data);
    }
  }

  /**
   * Handle new hand after redeal
   */
  handleNewHand(data) {
    console.log("✨ New hand received:", data);

    if (data.player === this.stateManager.playerName) {
      // Update our hand
      this.stateManager.updateHand(data.hand);
      console.log("✅ Updated player hand after redeal");
    }

    // Forward to current phase
    const currentPhase = this.phaseManager.getCurrentPhase();
    if (currentPhase && currentPhase.handleNewHand) {
      currentPhase.handleNewHand(data);
    }
  }

  /**
   * Handle redeal completion
   */
  handleRedealComplete(data) {
    console.log("🎯 Redeal complete:", data);

    // Update game state
    if (data.new_round_data) {
      this.stateManager.updateFromRoundData(data.new_round_data);
    }

    // Transition to next phase
    setTimeout(() => {
      this.phaseManager.transitionTo("declaration");
    }, 1000);
  }

  /**
   * Handle weak hands check from server
   */
  handleWeakHandsCheck(data) {
    console.log("🔍 Weak hands check:", data);

    // If we have weak hand, go to redeal phase
    if (
      data.weak_players &&
      data.weak_players.includes(this.stateManager.playerName)
    ) {
      console.log("⚠️ Player has weak hand, entering redeal phase");
      this.phaseManager.transitionTo("redeal");
    }
  }

  /**
   * Handle declaration event
   */
  handleDeclare(data) {
    console.log("📣 Declaration received:", data);

    // Update game state
    this.stateManager.addDeclaration(data.player, data.value);

    // Update UI
    // this.uiRenderer.addDeclaration(data.player, data.value);

    // Log bot declarations
    if (data.is_bot) {
      console.log(`🤖 ${data.player} declares ${data.value} piles.`);
    }

    // The DeclarationPhase will handle checking whose turn it is
    // via its socket event handler
  }

  /**
   * Handle all players declared
   */
  handleAllDeclared(data) {
    console.log("✅ All players have declared!");

    // Show declaration summary
    if (this.phaseManager.uiRenderer) {
      this.phaseManager.uiRenderer.showDeclarationSummary(data.declarations);
    }

    // Transition to turn phase
    setTimeout(() => {
      this.phaseManager.transitionTo("turn");
    }, 2000);
  }

  /**
   * Handle play event
   */
  handlePlay(data) {
    console.log("🎮 Play received:", data);

    // Update state
    this.stateManager.addTurnPlay(data.player, data.cards);

    // TODO: Update UI with play
  }

  /**
   * Handle turn end
   */
  handleTurnEnd(data) {
    console.log("🔚 Turn ended:", data);

    // Clear turn plays
    this.stateManager.clearTurnPlays();

    // TODO: Show turn winner
  }

  /**
   * Handle round end
   */
  handleRoundEnd(data) {
    console.log("🏁 Round ended:", data);

    // Update scores
    if (data.scores) {
      this.stateManager.setRoundScores(data.scores);
    }

    // Transition to scoring phase
    this.phaseManager.transitionTo("scoring");
  }

  /**
   * Handle game end
   */
  handleGameEnd(data) {
    console.log("🎮 Game ended:", data);

    // Update state
    this.stateManager.endGame(data);
  }

  /**
   * Handle player quit
   */
  handlePlayerQuit(data) {
    console.log("👋 Player quit:", data);

    this.stateManager.playerQuit(data.player);
  }

  /**
   * Handle room closed
   */
  handleRoomClosed(data) {
    console.log("🚪 Room closed:", data);

    this.stateManager.roomClosed(data);
  }

  /**
   * Handle errors
   */
  handleError(data) {
    console.error("❌ Game error:", data);

    if (this.phaseManager.uiRenderer) {
      this.phaseManager.uiRenderer.showError(
        data.message || "An error occurred"
      );
    }
  }

  /**
   * Handle redeal phase started event
   * Forward to current phase if it's RedealPhase
   */
  handleRedealPhaseStarted(data) {
    console.log("🔴 GameEventHandler: redeal_phase_started received:", data);

    const currentPhase = this.phaseManager.getCurrentPhase();
    if (currentPhase && currentPhase.constructor.name === "RedealPhase") {
      console.log("📨 Forwarding to RedealPhase.handleRedealPhaseStarted");
      currentPhase.handleRedealPhaseStarted(data);
    } else {
      console.warn(
        "⚠️ Received redeal_phase_started but not in RedealPhase:",
        currentPhase?.constructor.name
      );
    }
  }

  /**
   * Handle redeal prompt event
   * Forward to current phase if it's RedealPhase
   */
  handleRedealPrompt(data) {
    console.log("🔴 GameEventHandler: redeal_prompt received:", data);

    const currentPhase = this.phaseManager.getCurrentPhase();
    if (currentPhase && currentPhase.constructor.name === "RedealPhase") {
      console.log("📨 Forwarding to RedealPhase.handleRedealPrompt");
      currentPhase.handleRedealPrompt(data);
    } else {
      console.warn(
        "⚠️ Received redeal_prompt but not in RedealPhase:",
        currentPhase?.constructor.name
      );
    }
  }

  /**
   * Handle redeal decision made event
   * Forward to current phase if it's RedealPhase
   */
  handleRedealDecisionMade(data) {
    console.log("🔴 GameEventHandler: redeal_decision_made received:", data);

    const currentPhase = this.phaseManager.getCurrentPhase();
    if (currentPhase && currentPhase.constructor.name === "RedealPhase") {
      console.log("📨 Forwarding to RedealPhase.handleRedealDecision");
      currentPhase.handleRedealDecision(data);
    } else {
      console.warn(
        "⚠️ Received redeal_decision_made but not in RedealPhase:",
        currentPhase?.constructor.name
      );
    }
  }

  /**
   * Disconnect and clean up
   */
  disconnect() {
    // Remove all listeners
    Object.keys(this.eventHandlers).forEach((event) => {
      this.socketManager.off(event);
    });

    console.log("GameEventHandler disconnected");
  }
}
