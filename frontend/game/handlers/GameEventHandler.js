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
    
    // Bind event handlers
    this.eventHandlers = {
      'declare': this.handleDeclare.bind(this),
      'all_declared': this.handleAllDeclared.bind(this),
      'play': this.handlePlay.bind(this),
      'turn_end': this.handleTurnEnd.bind(this),
      'round_end': this.handleRoundEnd.bind(this),
      'game_end': this.handleGameEnd.bind(this),
      'player_quit': this.handlePlayerQuit.bind(this),
      'room_closed': this.handleRoomClosed.bind(this),
      'error': this.handleError.bind(this)
    };
    
    console.log('GameEventHandler initialized');
  }
  
  /**
   * Connect to game WebSocket and set up listeners
   */
  async connect() {
    console.log('📡 Connecting game event handlers');
    
    // Connect to game WebSocket
    // const url = `/ws/game?room_id=${this.stateManager.roomId}&name=${this.stateManager.playerName}`;
    await this.socketManager.connect(this.stateManager.roomId);
    
    // Set up event listeners
    Object.entries(this.eventHandlers).forEach(([event, handler]) => {
      this.socketManager.on(event, handler);
    });
    
    console.log('✅ Game event handlers connected');
  }
  
  /**
   * Handle declaration event
   */
  handleDeclare(data) {
    console.log('📣 Declaration received:', data);
    
    // Update state
    this.stateManager.addDeclaration(data.player, data.value);
    
    // Update UI
    if (this.phaseManager.uiRenderer) {
      this.phaseManager.uiRenderer.updateDeclaration(data.player, data.value);
    }
    
    // If it's a bot declaration, log it
    if (data.is_bot) {
      console.log(`🤖 ${data.player} declares ${data.value} piles.`);
    }
    
    // Check if it's now our turn to declare
    if (data.next_player === this.stateManager.playerName) {
      this.promptForDeclaration();
    }
  }
  
  /**
   * Prompt player for declaration
   */
  promptForDeclaration() {
    console.log("🎯 It's your turn to declare!");
    
    // Calculate valid declaration options
    const validOptions = this.calculateValidDeclarations();
    
    // Show input UI
    if (this.phaseManager.uiRenderer) {
      this.phaseManager.uiRenderer.showDeclarationInput(
        validOptions,
        (value) => this.sendDeclaration(value)
      );
    }
  }
  
  /**
   * Calculate valid declaration options based on hand
   */
  calculateValidDeclarations() {
    const handSize = this.stateManager.myHand.length;
    const options = [];
    
    // Can declare 0 to handSize piles
    for (let i = 0; i <= handSize; i++) {
      options.push(i);
    }
    
    return options;
  }
  
  /**
   * Send declaration to server
   */
  sendDeclaration(value) {
    console.log(`📤 Sending declaration: ${value}`);
    
    this.socketManager.send('declare', {
      value: value
    });
  }
  
  /**
   * Handle all players declared
   */
  handleAllDeclared(data) {
    console.log('✅ All players have declared!');
    
    // Show declaration summary
    if (this.phaseManager.uiRenderer) {
      this.phaseManager.uiRenderer.showDeclarationSummary(data.declarations);
    }
    
    // Transition to turn phase
    setTimeout(() => {
      this.phaseManager.transitionTo('turn');
    }, 2000);
  }
  
  /**
   * Handle play event
   */
  handlePlay(data) {
    console.log('🎮 Play received:', data);
    
    // Update state
    this.stateManager.addTurnPlay(data.player, data.cards);
    
    // TODO: Update UI with play
  }
  
  /**
   * Handle turn end
   */
  handleTurnEnd(data) {
    console.log('🔚 Turn ended:', data);
    
    // Clear turn plays
    this.stateManager.clearTurnPlays();
    
    // TODO: Show turn winner
  }
  
  /**
   * Handle round end
   */
  handleRoundEnd(data) {
    console.log('🏁 Round ended:', data);
    
    // Update scores
    if (data.scores) {
      this.stateManager.setRoundScores(data.scores);
    }
    
    // Transition to scoring phase
    this.phaseManager.transitionTo('scoring');
  }
  
  /**
   * Handle game end
   */
  handleGameEnd(data) {
    console.log('🎮 Game ended:', data);
    
    // Update state
    this.stateManager.endGame(data);
  }
  
  /**
   * Handle player quit
   */
  handlePlayerQuit(data) {
    console.log('👋 Player quit:', data);
    
    this.stateManager.playerQuit(data.player);
  }
  
  /**
   * Handle room closed
   */
  handleRoomClosed(data) {
    console.log('🚪 Room closed:', data);
    
    this.stateManager.roomClosed(data);
  }
  
  /**
   * Handle errors
   */
  handleError(data) {
    console.error('❌ Game error:', data);
    
    if (this.phaseManager.uiRenderer) {
      this.phaseManager.uiRenderer.showError(data.message || 'An error occurred');
    }
  }
  
  /**
   * Disconnect and clean up
   */
  disconnect() {
    // Remove all listeners
    Object.keys(this.eventHandlers).forEach(event => {
      this.socketManager.off(event);
    });
    
    console.log('GameEventHandler disconnected');
  }
}