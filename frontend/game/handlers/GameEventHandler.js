// frontend/game/handlers/GameEventHandler.js

/**
 * Centralized WebSocket event handling for the game
 * Separates network concerns from game logic
 * 
 * Responsibilities:
 * - Register/unregister socket listeners
 * - Route events to appropriate handlers
 * - Update state manager
 * - Coordinate with phase manager
 */
export class GameEventHandler {
  constructor(socketManager, stateManager, phaseManager) {
    this.socketManager = socketManager;
    this.stateManager = stateManager;
    this.phaseManager = phaseManager;
    
    // Event handler map
    this.handlers = new Map();
    
    // Track active state
    this.isActive = false;
  }

  /**
   * Connect and register all event handlers
   */
  connect() {
    if (this.isActive) return;
    
    console.log('📡 Connecting game event handlers');
    this.isActive = true;
    
    // Core game events
    this.registerHandler('start_game', this.handleStartGame);
    this.registerHandler('start_round', this.handleStartRound);
    this.registerHandler('player_left', this.handlePlayerLeft);
    this.registerHandler('room_closed', this.handleRoomClosed);
    
    // Phase-specific events (handled by current phase)
    this.registerHandler('declare', this.routeToPhase);
    this.registerHandler('play', this.routeToPhase);
    this.registerHandler('turn_resolved', this.routeToPhase);
    this.registerHandler('score', this.handleScore);
    this.registerHandler('redeal', this.routeToPhase);
    
    // Connection events
    this.registerHandler('reconnected', this.handleReconnected);
  }

  /**
   * Disconnect and clean up handlers
   */
  disconnect() {
    if (!this.isActive) return;
    
    console.log('📡 Disconnecting game event handlers');
    
    this.handlers.forEach((handler, event) => {
      this.socketManager.off(event, handler);
    });
    
    this.handlers.clear();
    this.isActive = false;
  }

  /**
   * Register an event handler
   */
  registerHandler(event, handler) {
    const boundHandler = handler.bind(this);
    this.handlers.set(event, boundHandler);
    this.socketManager.on(event, boundHandler);
  }

  /**
   * Route event to current phase
   */
  routeToPhase(data) {
    const currentPhase = this.phaseManager.currentPhase;
    if (currentPhase && currentPhase.handleSocketEvent) {
      currentPhase.handleSocketEvent(data.event, data);
    }
  }

  /**
   * Handle game start
   */
  handleStartGame(data) {
    console.log('🎮 Game started!', data);
    
    // Update state with initial game data
    if (data.players) {
      this.stateManager.players = data.players;
    }
    
    if (data.round) {
      this.stateManager.currentRound = data.round;
    }
    
    if (data.starter) {
      this.stateManager.roundStarter = data.starter;
    }
    
    if (data.hands && data.hands[this.stateManager.playerName]) {
      this.stateManager.updateHand(data.hands[this.stateManager.playerName]);
    }
    
    // Start game flow
    this.phaseManager.start();
  }

  /**
   * Handle new round start
   */
  handleStartRound(data) {
    console.log('🆕 New round started', data);
    
    // Reset state for new round
    this.stateManager.resetForNewRound(data);
    
    // Start new round flow
    this.phaseManager.resetForNewRound(data);
  }

  /**
   * Handle scoring
   */
  handleScore(data) {
    console.log('📊 Round scored', data);
    
    // Update scores
    if (data.summary) {
      this.stateManager.updateRoundScores(data.summary);
    }
    
    // Check for game over
    if (data.game_over) {
      this.handleGameOver(data);
    } else {
      // Emit event for phase manager
      this.stateManager.emit('roundScoringComplete', {
        gameOver: false,
        winners: []
      });
    }
  }

  /**
   * Handle game over
   */
  handleGameOver(data) {
    console.log('🏁 Game over!', data);
    
    this.stateManager.emit('roundScoringComplete', {
      gameOver: true,
      winners: data.winners || [],
      finalScores: this.stateManager.totalScores
    });
  }

  /**
   * Handle player left
   */
  handlePlayerLeft(data) {
    console.log('👋 Player left:', data.player);
    
    // Update UI
    this.stateManager.emit('playerLeft', data);
  }

  /**
   * Handle room closed
   */
  handleRoomClosed(data) {
    console.log('🚪 Room closed:', data);
    
    // Clean up and return to lobby
    this.disconnect();
    this.stateManager.emit('roomClosed', data);
  }

  /**
   * Handle reconnection
   */
  async handleReconnected() {
    console.log('✅ Reconnected to game');
    
    // Request current game state
    try {
      const response = await fetch(`/api/get-game-state?room_id=${this.stateManager.roomId}`);
      const gameState = await response.json();
      
      // Update state
      this.stateManager.syncWithServerState(gameState);
      
      // Resume current phase
      this.phaseManager.resumeCurrentPhase();
      
    } catch (error) {
      console.error('Failed to sync game state:', error);
    }
  }

  /**
   * Send event to server
   */
  async sendGameEvent(event, data) {
    if (!this.socketManager.connected) {
      console.warn('Not connected, queuing event:', event);
    }
    
    this.socketManager.send(event, {
      room_id: this.stateManager.roomId,
      player_name: this.stateManager.playerName,
      ...data
    });
  }
}