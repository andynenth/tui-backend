// frontend/game/phases/ScoringPhase.js

import { BasePhase } from './BasePhase.js';

/**
 * Scoring Phase
 * Calculate and display round scores
 * 
 * Responsibilities:
 * - Display round summary
 * - Show score calculations
 * - Check for game over
 * - Trigger next round or end game
 */
export class ScoringPhase extends BasePhase {
  constructor(stateManager, socketManager, uiManager) {
    super(stateManager, socketManager, uiManager);
    
    this.scoringComplete = false;
    this.gameOver = false;
    this.winners = [];
  }

  /**
   * Enter scoring phase
   */
  async enter() {
    await super.enter();
    
    console.log("\n🏁 --- End of Round ---");
    
    // Show UI
    this.uiManager.showScoringPhase();
    
    // Request scoring from server
    this.requestScoring();
  }

  /**
   * Register event handlers
   */
  registerEventHandlers() {
    this.addEventHandler('score', this.handleScore);
  }

  /**
   * Request scoring from server
   */
  async requestScoring() {
    try {
      console.log("📊 Calculating scores...");
      
      const response = await fetch(
        `/api/score-round?room_id=${this.stateManager.roomId}`,
        { method: "POST" }
      );
      
      if (!response.ok) {
        console.error("Failed to score round");
        this.uiManager.showError("Failed to calculate scores");
        return;
      }
      
      // Server will send score event via WebSocket
      
    } catch (err) {
      console.error("Failed to request scoring:", err);
      this.uiManager.showError("Network error during scoring");
    }
  }

  /**
   * Handle score event from server
   */
  handleScore(data) {
    console.log("\n📊 Round Summary:");
    
    if (!data.summary) {
      console.error("Invalid score data received");
      return;
    }
    
    const { summary } = data;
    
    // Update state manager with scores
    this.stateManager.updateRoundScores(summary);
    
    // Display score breakdown
    this.displayScoreSummary(summary);
    
    // Check for game over
    if (data.game_over) {
      this.handleGameOver(data);
    } else {
      this.prepareNextRound();
    }
    
    this.scoringComplete = true;
  }

  /**
   * Display score summary
   */
  displayScoreSummary(summary) {
    // Show round number and multiplier
    if (summary.multiplier && summary.multiplier > 1) {
      console.log(`\n🎲 Score Multiplier: x${summary.multiplier}`);
    }
    
    // Show each player's scoring
    if (summary.scores) {
      Object.entries(summary.scores).forEach(([player, scoreData]) => {
        const declared = scoreData.declared || summary.declares?.[player] || 0;
        const actual = scoreData.actual || summary.captured?.[player] || 0;
        const delta = scoreData.delta;
        const multiplier = scoreData.multiplier || summary.multiplier || 1;
        const total = scoreData.total;
        
        // Format the score line
        let scoreLine = `${player} → declared ${declared}, got ${actual} → `;
        
        if (delta >= 0) {
          scoreLine += `+${delta} pts`;
        } else {
          scoreLine += `${delta} pts`;
        }
        
        if (multiplier > 1) {
          scoreLine += ` (×${multiplier})`;
        }
        
        scoreLine += `, total: ${total}`;
        
        console.log(scoreLine);
        
        // Highlight special cases
        if (declared === 0 && actual === 0) {
          console.log(`  💎 Perfect zero declaration!`);
        } else if (declared === actual && declared > 0) {
          console.log(`  🎯 Perfect prediction!`);
        }
      });
    }
    
    // Update UI
    this.uiManager.showScoreSummary(summary);
    
    // Show current standings
    this.displayCurrentStandings();
  }

  /**
   * Display current standings
   */
  displayCurrentStandings() {
    console.log("\n📊 --- Total Scores ---");
    
    // Get players sorted by score
    const standings = Object.entries(this.stateManager.totalScores)
      .sort(([, a], [, b]) => b - a)
      .map(([player, score], index) => {
        let prefix = '';
        if (index === 0) prefix = '🥇 ';
        else if (index === 1) prefix = '🥈 ';
        else if (index === 2) prefix = '🥉 ';
        else prefix = '   ';
        
        return `${prefix}${player}: ${score} pts`;
      });
    
    standings.forEach(line => console.log(line));
    
    // Check if anyone is close to winning
    const topScore = Math.max(...Object.values(this.stateManager.totalScores));
    const targetScore = 50; // TODO: Get from game config
    
    if (topScore >= targetScore - 10) {
      console.log(`\n⚠️ First to ${targetScore} points wins!`);
    }
  }

  /**
   * Handle game over
   */
  handleGameOver(data) {
    this.gameOver = true;
    this.winners = data.winners || [];
    
    console.log("\n🎮 GAME OVER!");
    
    if (this.winners.length === 1) {
      console.log(`\n🏆 Winner: ${this.winners[0]}!`);
      
      // Check if we won
      if (this.winners[0] === this.stateManager.playerName) {
        console.log("🎉 Congratulations! You won!");
        this.uiManager.showSuccess("Victory! You won the game!");
      } else {
        console.log(`Better luck next time!`);
      }
    } else if (this.winners.length > 1) {
      console.log(`\n🤝 It's a tie! Winners: ${this.winners.join(", ")}`);
      
      if (this.winners.includes(this.stateManager.playerName)) {
        console.log("🎉 Congratulations! You tied for the win!");
        this.uiManager.showSuccess("You tied for the win!");
      }
    } else {
      console.log("\n🤷 No winner determined");
    }
    
    // Show final scores
    console.log("\n📊 Final Scores:");
    Object.entries(this.stateManager.totalScores)
      .sort(([, a], [, b]) => b - a)
      .forEach(([player, score]) => {
        const isWinner = this.winners.includes(player) ? " 🏆" : "";
        console.log(`${player}: ${score} pts${isWinner}`);
      });
    
    // Update UI
    this.uiManager.showGameOver({
      winners: this.winners,
      finalScores: this.stateManager.totalScores,
      gameOver: true
    });
    
    // Emit game ended event
    setTimeout(() => {
      this.stateManager.emit('gameEnded', {
        winners: this.winners,
        finalScores: this.stateManager.totalScores
      });
    }, 3000);
  }

  /**
   * Prepare for next round
   */
  prepareNextRound() {
    const nextRound = this.stateManager.currentRound + 1;
    console.log(`\n⏳ Preparing for Round ${nextRound}...`);
    
    // Show continue prompt
    setTimeout(async () => {
      const shouldContinue = await this.promptContinue();
      
      if (shouldContinue) {
        // Server will send new round data
        console.log("Waiting for next round...");
      } else {
        // Player wants to quit
        this.handlePlayerQuit();
      }
    }, 3000);
  }

  /**
   * Prompt player to continue
   */
  async promptContinue() {
    // For now, auto-continue
    // In full implementation, could ask player
    return true;
  }

  /**
   * Handle player quitting
   */
  handlePlayerQuit() {
    console.log("👋 Thanks for playing!");
    
    // Notify server
    // Return to lobby
    this.stateManager.emit('playerQuit');
  }

  /**
   * Check if phase is complete
   */
  isPhaseComplete() {
    return this.scoringComplete;
  }

  /**
   * Get next phase
   */
  getNextPhase() {
    if (this.gameOver) {
      return null; // Game ends
    }
    return 'redeal'; // Start new round
  }

  /**
   * Handle user input
   */
  async handleUserInput(input) {
    if (!await super.handleUserInput(input)) return false;
    
    // Could handle "Continue" button click here
    
    return false;
  }

  /**
   * Exit phase
   */
  async exit() {
    // Hide scoring UI
    this.uiManager.hideScoringPhase();
    
    // Reset state
    this.scoringComplete = false;
    this.gameOver = false;
    this.winners = [];
    
    await super.exit();
  }
}