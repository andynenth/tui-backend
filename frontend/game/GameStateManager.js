// frontend/game/GameStateManager.js

import { EventEmitter } from '../network/core/EventEmitter.js';

/**
 * Manages all game state
 * Single source of truth for game data
 * 
 * Responsibilities:
 * - Store game state
 * - Emit state change events
 * - Provide state access methods
 * - Validate state changes
 */
export class GameStateManager extends EventEmitter {
  constructor(roomId, playerName, initialData) {
    super();
    
    // Core identifiers
    this.roomId = roomId;
    this.playerName = playerName;
    
    // Game state
    this.currentRound = initialData.round || 1;
    this.players = initialData.players || [];
    this.myHand = initialData.hands?.[playerName] || [];
    
    // Round state
    this.declarations = {};
    this.currentTurnPlays = [];
    this.requiredPieceCount = null;
    this.starter = initialData.starter || null;
    this.currentPlayerTurn = null;
    
    // Phase tracking
    this.currentPhase = 'INITIALIZATION';
    
    // Scoring
    this.scores = {};
    this.roundScores = {};
    
    // Initialize player scores
    this.players.forEach(player => {
      this.scores[player.name] = player.score || 0;
    });
    
    // Derived data
    this.myPlayerData = this.players.find(p => p.name === playerName) || {
      name: playerName,
      score: 0,
      is_bot: false
    };
    
    console.log('GameStateManager initialized with:', { 
      roomId, 
      playerName, 
      round: this.currentRound,
      players: this.players.length,
      hand: this.myHand.length
    });
  }
  
  // ===== HAND MANAGEMENT =====
  
  /**
   * Update player's hand
   */
  updateHand(newHand) {
    const oldHandSize = this.myHand.length;
    this.myHand = newHand;
    this.emit('handUpdated', { 
      hand: newHand,
      oldSize: oldHandSize,
      newSize: newHand.length
    });
  }
  
  /**
   * Remove cards from hand
   */
  removeFromHand(cards) {
    const cardsToRemove = Array.isArray(cards) ? cards : [cards];
    this.myHand = this.myHand.filter(card => !cardsToRemove.includes(card));
    this.emit('handUpdated', { 
      hand: this.myHand,
      removed: cardsToRemove
    });
  }
  
  // ===== DECLARATION MANAGEMENT =====
  
  /**
   * Add a player's declaration
   */
  addDeclaration(playerName, value) {
    this.declarations[playerName] = value;
    this.emit('declarationAdded', { 
      player: playerName, 
      value,
      totalDeclared: Object.keys(this.declarations).length
    });
    
    // Check if all players have declared
    if (Object.keys(this.declarations).length === this.players.length) {
      this.emit('allPlayersDeclared', { declarations: this.declarations });
    }
  }
  
  /**
   * Clear all declarations
   */
  clearDeclarations() {
    this.declarations = {};
    this.emit('declarationsCleared');
  }
  
  // ===== TURN MANAGEMENT =====
  
  /**
   * Set current player's turn
   */
  setCurrentTurn(playerName) {
    this.currentPlayerTurn = playerName;
    this.emit('turnChanged', { 
      player: playerName,
      isMyTurn: playerName === this.playerName
    });
  }
  
  /**
   * Add play to current turn
   */
  addTurnPlay(playerName, cards) {
    this.currentTurnPlays.push({
      player: playerName,
      cards: Array.isArray(cards) ? cards : [cards]
    });
    
    this.emit('playMade', {
      player: playerName,
      cards,
      totalPlays: this.currentTurnPlays.length
    });
  }
  
  /**
   * Clear current turn plays
   */
  clearTurnPlays() {
    this.currentTurnPlays = [];
    this.emit('turnPlaysCleared');
  }
  
  // ===== SCORE MANAGEMENT =====
  
  /**
   * Update player score
   */
  updateScore(playerName, newScore) {
    const oldScore = this.scores[playerName] || 0;
    this.scores[playerName] = newScore;
    
    // Update player object
    const player = this.players.find(p => p.name === playerName);
    if (player) {
      player.score = newScore;
    }
    
    this.emit('scoreUpdated', {
      player: playerName,
      oldScore,
      newScore,
      difference: newScore - oldScore
    });
  }
  
  /**
   * Set round scores
   */
  setRoundScores(roundScores) {
    this.roundScores = roundScores;
    
    // Update total scores
    Object.entries(roundScores).forEach(([player, roundScore]) => {
      const currentScore = this.scores[player] || 0;
      this.updateScore(player, currentScore + roundScore);
    });
    
    this.emit('roundScoresSet', { roundScores });
  }
  
  // ===== GAME STATE =====
  
  /**
   * Start new round
   */
  startNewRound(roundData) {
    this.currentRound = roundData.round;
    this.starter = roundData.starter;
    this.myHand = roundData.hands?.[this.playerName] || [];
    
    // Clear round state
    this.clearDeclarations();
    this.clearTurnPlays();
    this.roundScores = {};
    
    this.emit('newRoundStarted', {
      round: this.currentRound,
      starter: this.starter,
      handSize: this.myHand.length
    });
  }
  
  /**
   * End game
   */
  endGame(gameData) {
    this.emit('gameEnded', gameData);
  }
  
  /**
   * Handle room closed
   */
  roomClosed(data) {
    this.emit('roomClosed', data);
  }
  
  /**
   * Handle player quit
   */
  playerQuit(playerName) {
    if (playerName === this.playerName) {
      this.emit('playerQuit');
    } else {
      this.emit('otherPlayerQuit', { player: playerName });
    }
  }
  
  // ===== UTILITY METHODS =====
  
  /**
   * Get player by name
   */
  getPlayer(playerName) {
    return this.players.find(p => p.name === playerName);
  }
  
  /**
   * Check if it's my turn
   */
  isMyTurn() {
    return this.currentPlayerTurn === this.playerName;
  }
  
  /**
   * Get current game state summary
   */
  getStateSummary() {
    return {
      roomId: this.roomId,
      playerName: this.playerName,
      round: this.currentRound,
      phase: this.currentPhase,
      players: this.players.length,
      handSize: this.myHand.length,
      declarations: Object.keys(this.declarations).length,
      currentTurn: this.currentPlayerTurn
    };
  }
  
  /**
   * Remove all event listeners (extends from EventEmitter)
   */
  removeAllListeners() {
    this.clear(); // EventEmitter's method to clear all listeners
  }
}