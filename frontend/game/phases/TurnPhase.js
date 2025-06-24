// frontend/game/phases/TurnPhase.js

import { BasePhase } from './BasePhase.js';

/**
 * Turn Phase
 * Players take turns playing sets of pieces
 * 
 * Rules:
 * - First player sets the required piece count (1-6)
 * - Other players must play same number of pieces
 * - Invalid plays are allowed but cannot win
 * - Winner takes all pieces as a "pile"
 * - Winner starts next turn
 * - Phase ends when all hands are empty
 */
export class TurnPhase extends BasePhase {
  constructor(stateManager, socketManager, uiManager) {
    super(stateManager, socketManager, uiManager);
    
    // Explicitly set phase name (overrides BasePhase constructor.name logic)
    this.name = 'turn';
    
    // Turn state
    this.waitingForPlay = false;
    this.isProcessingTurn = false;
    this.turnResolutionTimer = null;
  }

  /**
   * Enter turn phase
   */
  async enter() {
    await super.enter();
    
    console.log("\n--- Turn Phase ---");
    
    // Show UI
    this.uiRenderer.showTurnPhase();
    
    // Initialize first turn
    this.initializeFirstTurn();
  }

  /**
   * Initialize the first turn of the phase
   */
  initializeFirstTurn() {
    // Determine who starts based on round starter
    const starter = this.stateManager.roundStarter;
    
    console.log(`\n🎯 ${starter} starts the first turn`);
    
    // Start the turn
    this.stateManager.startNewTurn(starter);
    
    // Check if it's our turn
    this.checkTurnPlay();
  }

  /**
   * Register event handlers
   */
  registerEventHandlers() {
    this.addEventHandler('play', this.handlePlay);
    this.addEventHandler('turn_resolved', this.handleTurnResolved);
  }

  /**
   * Check if player needs to play
   */
  checkTurnPlay() {
    // Don't check if already waiting or processing
    if (this.waitingForPlay || this.isProcessingTurn) return;
    
    // Check if we have cards to play
    if (this.stateManager.myHand.length === 0) {
      console.log("📭 Your hand is empty - waiting for others...");
      return;
    }
    
    // Check if it's our turn
    if (this.stateManager.isMyTurnToPlay()) {
      this.promptTurnPlay();
    }
  }

  /**
   * Prompt player to play
   */
  async promptTurnPlay() {
    if (this.waitingForPlay) return;
    
    this.waitingForPlay = true;
    
    console.log(`\n--- Turn ${this.stateManager.currentTurnNumber} ---`);
    
    // Show hand
    this.uiRenderer.displayHand(this.stateManager.myHand);
    
    // Show declaration reminder
    const myDeclaration = this.stateManager.declarations[this.stateManager.playerName];
    console.log(`${this.stateManager.playerName} declares ${myDeclaration} piles.`);
    
    // Determine if first player
    const isFirstPlayer = this.stateManager.isFirstPlayerInTurn();
    
    let prompt, validator;
    
    if (isFirstPlayer) {
      prompt = "Enter the indices of pieces you want to play (space-separated):";
      validator = this.validateFirstPlay.bind(this);
    } else {
      const required = this.stateManager.requiredPieceCount;
      prompt = `Enter the indices of pieces you want to play (must be exactly ${required} pieces):`;
      validator = this.validateFollowPlay.bind(this, required);
    }
    
    const input = await this.uiRenderer.showInput(prompt, validator);
    
    // Parse indices
    const indices = input.trim().split(/\s+/).map(i => parseInt(i));
    await this.playTurn(indices);
  }

  /**
   * Validate first player's play
   */
  validateFirstPlay(input) {
    const indices = input.trim().split(/\s+/).map(i => parseInt(i));
    
    if (indices.some(i => isNaN(i))) {
      return { valid: false, message: "Please enter numbers only" };
    }
    
    if (indices.length < 1 || indices.length > 6) {
      return { valid: false, message: "Must play between 1-6 pieces" };
    }
    
    const maxIndex = this.stateManager.myHand.length - 1;
    if (indices.some(i => i < 0 || i > maxIndex)) {
      return { valid: false, message: "Invalid piece index" };
    }
    
    // Check for duplicates
    const uniqueIndices = new Set(indices);
    if (uniqueIndices.size !== indices.length) {
      return { valid: false, message: "Cannot play the same piece twice" };
    }
    
    return { valid: true };
  }

  /**
   * Validate follow player's play
   */
  validateFollowPlay(requiredCount, input) {
    const indices = input.trim().split(/\s+/).map(i => parseInt(i));
    
    const basicValidation = this.validateFirstPlay(input);
    if (!basicValidation.valid) return basicValidation;
    
    if (indices.length !== requiredCount) {
      return { 
        valid: false, 
        message: `Must play exactly ${requiredCount} pieces` 
      };
    }
    
    return { valid: true };
  }

  /**
   * Play the selected pieces
   */
  async playTurn(indices) {
    try {
      // Get the pieces being played
      const pieces = indices.map(i => this.stateManager.myHand[i]);
      
      console.log(`\n🎴 Playing: [${pieces.join(', ')}]`);
      
      // Send to server
      const url = `/api/play-turn?room_id=${this.stateManager.roomId}&player_name=${
        this.stateManager.playerName
      }&piece_indexes=${indices.join(',')}`;
      
      const response = await fetch(url, { method: "POST" });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error("Server error:", errorText);
        this.uiRenderer.showError("Failed to play turn");
        this.waitingForPlay = false;
        return;
      }
      
      const result = await response.json();
      
      if (result.status === "error") {
        console.error("❌", result.message);
        this.uiRenderer.showError(result.message);
        this.waitingForPlay = false;
        return;
      }
      
      // Remove played pieces from hand
      if (result.status === "waiting" || result.status === "resolved") {
        this.stateManager.removeFromHand(indices);
        console.log("✅ Pieces played successfully");
      }
      
      this.waitingForPlay = false;
      
      // If turn is resolved immediately (all players played)
      if (result.status === "resolved") {
        this.processTurnResult(result);
      }
      
    } catch (err) {
      console.error("Failed to play turn:", err);
      this.uiRenderer.showError("Network error. Please try again.");
      this.waitingForPlay = false;
    }
  }

  /**
   * Handle play event from any player
   */
  handlePlay(data) {
    const { player, pieces, valid, play_type } = data;
    
    // Show the play
    const validStr = valid ? "✅" : "❌";
    const typeStr = play_type || "INVALID";
    
    if (player === this.stateManager.playerName) {
      console.log(`Your play: [${pieces.join(', ')}] → ${validStr} (${typeStr})`);
    } else {
      console.log(`${player}'s play: [${pieces.join(', ')}] → ${validStr} (${typeStr})`);
    }
    
    // Update state
    this.stateManager.addTurnPlay(player, pieces, valid);
    
    // Update UI
    this.uiRenderer.updateTurnPlay(player, pieces, valid, play_type);
    
    // Check if we need to play
    const progress = this.stateManager.getTurnProgress();
    console.log(`Turn progress: ${progress.played}/${progress.total}`);
    
    if (progress.played < progress.total) {
      this.checkTurnPlay();
    }
  }

  /**
   * Handle turn resolution
   */
  handleTurnResolved(data) {
    this.processTurnResult(data);
  }

  /**
   * Process turn result
   */
  processTurnResult(data) {
    if (this.isProcessingTurn) return;
    
    this.isProcessingTurn = true;
    
    console.log("\n🎯 Turn Summary:");
    
    // Show all plays
    data.plays.forEach((play) => {
      const declared = this.stateManager.declarations[play.player];
      const validStr = play.is_valid ? "✅" : "❌";
      const currentScore = "?"; // Would need to track this
      
      console.log(`  - ${play.player}: [${play.pieces.join(', ')}] ${validStr} [${currentScore}/${declared}]`);
    });
    
    // Show winner
    if (data.winner) {
      const winningPlay = data.plays.find(p => p.player === data.winner);
      console.log(`\n>>> 🏆 ${data.winner} wins the turn with [${
        winningPlay.pieces.join(', ')
      }] (+${data.pile_count} pts).`);
      
      // Update state for next turn
      this.stateManager.currentTurnStarter = data.winner;
    } else {
      console.log("\n>>> ⚠️ No one wins the turn.");
    }
    
    // Update UI
    this.uiRenderer.showTurnResult(data);
    
    // Check if round is complete
    if (this.stateManager.myHand.length === 0) {
      // Check if all players have empty hands
      const allEmpty = data.plays.every(play => {
        // This is a simplification - would need server to confirm
        return true;
      });
      
      if (allEmpty) {
        console.log("\n🏁 All hands empty - round complete!");
        this.completeRound();
        return;
      }
    }
    
    // Continue to next turn after delay
    this.turnResolutionTimer = setTimeout(() => {
      this.isProcessingTurn = false;
      this.startNextTurn(data.winner);
    }, 2000);
  }

  /**
   * Start the next turn
   */
  startNextTurn(winner) {
    // Clear state
    this.stateManager.currentTurnPlays = [];
    this.stateManager.requiredPieceCount = null;
    
    // Start new turn with winner (or last starter if no winner)
    const nextStarter = winner || this.stateManager.currentTurnStarter;
    this.stateManager.startNewTurn(nextStarter);
    
    console.log(`\n🔄 ${nextStarter} starts the next turn`);
    
    // Check if we need to play
    this.checkTurnPlay();
  }

  /**
   * Complete the round
   */
  completeRound() {
    console.log("\n📊 Round complete - calculating scores...");
    
    // Server will handle scoring
    // Just transition to scoring phase
    setTimeout(() => {
      this.completePhase({ nextPhase: 'scoring' });
    }, 1000);
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
   * Check if phase is complete
   */
  isPhaseComplete() {
    // Phase completes when all hands are empty
    // This is tracked by the server
    return false;
  }

  /**
   * Get next phase
   */
  getNextPhase() {
    return 'scoring';
  }

  /**
   * Exit phase
   */
  async exit() {
    // Clear any timers
    if (this.turnResolutionTimer) {
      clearTimeout(this.turnResolutionTimer);
      this.turnResolutionTimer = null;
    }
    
    // Reset state
    this.waitingForPlay = false;
    this.isProcessingTurn = false;
    
    // Hide UI
    this.uiRenderer.hideTurnPhase();
    
    await super.exit();
  }
}