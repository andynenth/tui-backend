// frontend/game/GamePhaseManager.js

export const GamePhases = {
  ROUND_PREPARATION: "ROUND_PREPARATION",
  REDEAL_CHECK: "REDEAL_CHECK", 
  DECLARATION: "DECLARATION",
  TURN_PLAY: "TURN_PLAY",
  TURN_RESOLUTION: "TURN_RESOLUTION",
  ROUND_SCORING: "ROUND_SCORING",
  GAME_OVER: "GAME_OVER"
};

export class GamePhaseManager {
  constructor(gameScene) {
    this.gameScene = gameScene;
    this.currentPhase = null;
    this.phaseData = {};
    
    // Track turn-specific data
    this.currentTurn = {
      number: 0,
      requiredPieceCount: null,
      firstPlayer: null,
      plays: [],
      turnOrder: []
    };
  }

  setPhase(phase, data = {}) {
    console.log(`📊 Phase transition: ${this.currentPhase} → ${phase}`, data);
    this.currentPhase = phase;
    this.phaseData = data;
    
    // Notify GameScene of phase change
    this.gameScene.onPhaseChange(phase, data);
  }

  getCurrentPhase() {
    return this.currentPhase;
  }

  getPhaseData() {
    return this.phaseData;
  }

  // Turn management methods
  startNewTurn(firstPlayer) {
    this.currentTurn = {
      number: this.currentTurn.number + 1,
      requiredPieceCount: null,
      firstPlayer: firstPlayer,
      plays: [],
      turnOrder: this.generateTurnOrder(firstPlayer)
    };
  }

  generateTurnOrder(firstPlayer) {
    // Generate turn order starting from firstPlayer
    const players = this.gameScene.players;
    const firstIndex = players.findIndex(p => p.name === firstPlayer);
    
    if (firstIndex === -1) return players;
    
    return [
      ...players.slice(firstIndex),
      ...players.slice(0, firstIndex)
    ];
  }

  setRequiredPieceCount(count) {
    this.currentTurn.requiredPieceCount = count;
  }

  recordPlay(playerName, pieces, isValid) {
    this.currentTurn.plays.push({
      player: playerName,
      pieces: pieces,
      isValid: isValid,
      timestamp: Date.now()
    });
  }

  allPlayersPlayed() {
    return this.currentTurn.plays.length === this.gameScene.players.length;
  }

  resetTurn() {
    this.currentTurn.plays = [];
  }

  // Validation methods
  canPlayerDeclare(playerName) {
    return this.currentPhase === GamePhases.DECLARATION &&
           !this.gameScene.declarations[playerName];
  }

  canPlayerPlay(playerName) {
    if (this.currentPhase !== GamePhases.TURN_PLAY) return false;
    
    // Check if player already played this turn
    const alreadyPlayed = this.currentTurn.plays.some(p => p.player === playerName);
    return !alreadyPlayed;
  }

  isFirstPlayerOfTurn(playerName) {
    return this.currentTurn.firstPlayer === playerName;
  }

  validatePieceCount(pieces) {
    if (!this.currentTurn.requiredPieceCount) {
      // First player can play 1-6 pieces
      return pieces.length >= 1 && pieces.length <= 6;
    }
    // Other players must match the count
    return pieces.length === this.currentTurn.requiredPieceCount;
  }
}