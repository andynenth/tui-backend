// frontend/game/GameStateManager.js

import { EventEmitter } from '../network/core/EventEmitter.js';

/**
 * Centralized game state management
 * Single source of truth for all game data
 * 
 * Responsibilities:
 * - Store and update game state
 * - Emit events when state changes
 * - Provide computed properties
 * - Validate state transitions
 */
export class GameStateManager extends EventEmitter {
  constructor(roomId, playerName, initialGameData) {
    super();
    
    // Core identifiers
    this.roomId = roomId;
    this.playerName = playerName;
    
    // Game configuration
    this.gameData = initialGameData;
    
    // Round information
    this.currentRound = initialGameData.round || 1;
    this.roundStarter = initialGameData.starter || null;
    this.redealMultiplier = initialGameData.multiplier || 1;
    
    // Players
    this.players = initialGameData.players || [];
    this.myPlayerData = this.players.find(p => p.name === playerName) || null;
    
    // Hand management
    this.myHand = initialGameData.hands?.[playerName] || [];
    
    // Phase tracking
    this.currentPhase = 'INITIALIZATION';
    
    // Declaration phase state
    this.declarations = {};
    this.declarationOrder = [];
    
    // Turn phase state
    this.currentTurnNumber = 0;
    this.currentTurnStarter = null;
    this.currentTurnPlays = [];
    this.requiredPieceCount = null;
    this.turnOrder = [];
    
    // Score tracking
    this.roundScores = {};
    this.totalScores = {};
    
    // Initialize derived state
    this._initializeDerivedState();
  }

  /**
   * Initialize derived state from initial data
   */
  _initializeDerivedState() {
    // Initialize player scores
    this.players.forEach(player => {
      this.totalScores[player.name] = player.score || 0;
    });
    
    // Set declaration order based on round starter
    this._updateDeclarationOrder();
  }

  /**
   * Update declaration order based on round starter
   */
  _updateDeclarationOrder() {
    if (!this.roundStarter) return;
    
    const starterIndex = this.players.findIndex(p => p.name === this.roundStarter);
    if (starterIndex === -1) return;
    
    this.declarationOrder = [
      ...this.players.slice(starterIndex),
      ...this.players.slice(0, starterIndex)
    ];
  }

  // ===== PHASE MANAGEMENT =====

  setPhase(phaseName) {
    const oldPhase = this.currentPhase;
    this.currentPhase = phaseName;
    this.emit('phaseChanged', { oldPhase, newPhase: phaseName });
  }

  // ===== HAND MANAGEMENT =====

  updateHand(newHand) {
    const oldHand = [...this.myHand];
    this.myHand = newHand;
    this.emit('handUpdated', { oldHand, newHand });
  }

  removeFromHand(indices) {
    const removedPieces = indices.map(i => this.myHand[i]);
    
    // Remove in reverse order to maintain indices
    const sortedIndices = [...indices].sort((a, b) => b - a);
    sortedIndices.forEach(i => {
      this.myHand.splice(i, 1);
    });
    
    this.emit('piecesRemoved', { indices, pieces: removedPieces });
    return removedPieces;
  }

  // ===== DECLARATION PHASE =====

  addDeclaration(playerName, value) {
    this.declarations[playerName] = value;
    this.emit('declarationAdded', { player: playerName, value });
    
    // Check if all declared
    if (this.areAllPlayersDeclarated()) {
      const total = Object.values(this.declarations).reduce((sum, v) => sum + v, 0);
      this.emit('allPlayersDeclarated', { declarations: this.declarations, total });
    }
  }

  getValidDeclarationOptions(isLastPlayer = false) {
    let options = [0, 1, 2, 3, 4, 5, 6, 7, 8];
    
    if (isLastPlayer) {
      const declaredSoFar = Object.values(this.declarations)
        .filter(v => v !== null && v !== undefined)
        .reduce((sum, v) => sum + v, 0);
      
      const forbidden = 8 - declaredSoFar;
      options = options.filter(v => v !== forbidden);
    }
    
    // Check zero streak
    if (this.myPlayerData?.zero_declares_in_a_row >= 2) {
      options = options.filter(v => v > 0);
    }
    
    return options;
  }

  isMyTurnToDeclare() {
    if (!this.declarationOrder.length) return false;
    if (this.declarations[this.playerName] !== undefined) return false;
    
    // Check if all players before me have declared
    for (const player of this.declarationOrder) {
      if (player.name === this.playerName) return true;
      if (this.declarations[player.name] === undefined) return false;
    }
    
    return false;
  }

  areAllPlayersDeclarated() {
    return this.players.every(p => 
      this.declarations[p.name] !== undefined && 
      this.declarations[p.name] !== null
    );
  }

  // ===== TURN PHASE =====

  startNewTurn(starter) {
    this.currentTurnNumber++;
    this.currentTurnStarter = starter;
    this.currentTurnPlays = [];
    this.requiredPieceCount = null;
    
    // Update turn order
    const starterIndex = this.players.findIndex(p => p.name === starter);
    this.turnOrder = [
      ...this.players.slice(starterIndex),
      ...this.players.slice(0, starterIndex)
    ];
    
    this.emit('turnStarted', { 
      turnNumber: this.currentTurnNumber, 
      starter,
      turnOrder: this.turnOrder.map(p => p.name)
    });
  }

  addTurnPlay(playerName, pieces, isValid) {
    // Set required count from first play
    if (this.currentTurnPlays.length === 0) {
      this.requiredPieceCount = pieces.length;
    }
    
    this.currentTurnPlays.push({
      player: playerName,
      pieces,
      valid: isValid
    });
    
    this.emit('turnPlayAdded', { 
      player: playerName, 
      pieces, 
      valid: isValid,
      playsCount: this.currentTurnPlays.length
    });
  }

  isMyTurnToPlay() {
    if (!this.turnOrder.length) return false;
    
    const myOrderIndex = this.turnOrder.findIndex(p => p.name === this.playerName);
    const playsCompleted = this.currentTurnPlays.length;
    
    // Check if I've already played
    const alreadyPlayed = this.currentTurnPlays.some(play => 
      play.player === this.playerName
    );
    
    return myOrderIndex === playsCompleted && !alreadyPlayed;
  }

  isFirstPlayerInTurn() {
    return this.currentTurnPlays.length === 0;
  }

  // ===== SCORING =====

  updateRoundScores(scoreData) {
    this.roundScores = scoreData.scores || {};
    
    // Update total scores
    Object.entries(this.roundScores).forEach(([player, data]) => {
      if (data.total !== undefined) {
        this.totalScores[player] = data.total;
      }
    });
    
    this.emit('scoresUpdated', { 
      roundScores: this.roundScores, 
      totalScores: this.totalScores 
    });
  }

  // ===== GETTERS =====

  getMyPlayer() {
    return this.myPlayerData;
  }

  getPlayerByName(name) {
    return this.players.find(p => p.name === name);
  }

  getDeclarationProgress() {
    const declared = Object.keys(this.declarations).length;
    const total = this.players.length;
    return { declared, total, percentage: (declared / total) * 100 };
  }

  getTurnProgress() {
    const played = this.currentTurnPlays.length;
    const total = this.players.length;
    return { played, total, percentage: (played / total) * 100 };
  }

  // ===== RESET METHODS =====

  resetForNewRound(roundData) {
    this.currentRound = roundData.round;
    this.roundStarter = roundData.starter;
    this.myHand = roundData.hands?.[this.playerName] || [];
    
    // Reset round-specific state
    this.declarations = {};
    this.currentTurnNumber = 0;
    this.currentTurnPlays = [];
    this.requiredPieceCount = null;
    
    // Update derived state
    this._updateDeclarationOrder();
    
    this.emit('roundReset', { round: this.currentRound });
  }

  // ===== DEBUG =====

  getDebugInfo() {
    return {
      phase: this.currentPhase,
      round: this.currentRound,
      hand: this.myHand.length,
      declarations: Object.keys(this.declarations).length,
      turnNumber: this.currentTurnNumber,
      scores: this.totalScores
    };
  }
}