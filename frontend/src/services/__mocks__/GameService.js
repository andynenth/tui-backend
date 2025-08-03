// Mock GameService for Jest testing
import { networkService } from './NetworkService.js';

export class GameService {
  static instance = null;

  constructor() {
    throw new Error('GameService is a singleton. Use getInstance() instead.');
  }

  static getInstance() {
    if (!GameService.instance) {
      GameService.instance = Object.create(GameService.prototype);
      GameService.instance._init();
    }
    return GameService.instance;
  }

  _init() {
    this.state = {
      roomId: null,
      playerName: '',
      isConnected: false,
      isConnecting: false,
      error: null,
      phase: 'lobby',
      players: [],
      myHand: [],
      currentPlayer: '',
      currentDeclarer: '',
      declarations: {},
      turnPlays: {},
      pileCount: 0,
    };
    this.stateListeners = [];
    this.isDestroyed = false;
    this.networkListeners = new Map();
  }

  getState() {
    if (this.isDestroyed) {
      throw new Error('GameService has been destroyed');
    }
    return { ...this.state };
  }

  setState(newState, reason = 'MANUAL_UPDATE') {
    const oldState = { ...this.state };
    this.state = { ...this.state, ...newState };

    this.stateListeners.forEach((listener) => {
      listener({
        type: reason,
        oldState,
        newState: this.getState(),
      });
    });
  }

  async joinRoom(roomId, playerName) {
    if (this.isDestroyed) {
      throw new Error('GameService has been destroyed');
    }

    try {
      await networkService.connectToRoom(roomId);
      this.setState(
        {
          roomId,
          playerName,
          isConnected: true,
          isConnecting: false,
          error: null,
        },
        'ROOM_JOINED'
      );
    } catch (error) {
      this.setState(
        {
          error: `Failed to join room: ${error.message}`,
          isConnected: false,
          isConnecting: false,
        },
        'JOIN_ERROR'
      );
      throw error;
    }
  }

  async leaveRoom() {
    if (this.state.roomId) {
      await networkService.disconnectFromRoom(this.state.roomId);
      this.setState(
        {
          roomId: null,
          isConnected: false,
          error: null,
          phase: 'lobby',
        },
        'ROOM_LEFT'
      );
    }
  }

  // Game actions
  acceptRedeal() {
    if (this.state.phase !== 'preparation') {
      throw new Error(
        `Invalid action ACCEPT_REDEAL for phase ${this.state.phase}`
      );
    }
    networkService.send(this.state.roomId, 'accept_redeal', {
      player_name: this.state.playerName,
    });
  }

  declineRedeal() {
    if (this.state.phase !== 'preparation') {
      throw new Error(
        `Invalid action DECLINE_REDEAL for phase ${this.state.phase}`
      );
    }
    networkService.send(this.state.roomId, 'decline_redeal', {
      player_name: this.state.playerName,
    });
  }

  makeDeclaration(value) {
    if (this.state.phase !== 'declaration') {
      throw new Error(`Invalid action DECLARE for phase ${this.state.phase}`);
    }
    if (this.state.currentDeclarer !== this.state.playerName) {
      throw new Error('Not your turn to declare');
    }
    if (typeof value !== 'number' || value < 0 || value > 8) {
      throw new Error(`Invalid declaration value: ${value}`);
    }

    // Check if last player would make total equal 8
    const currentTotal = Object.values(this.state.declarations).reduce(
      (sum, val) => sum + val,
      0
    );
    const isLastPlayer = Object.keys(this.state.declarations).length === 3;
    if (isLastPlayer && currentTotal + value === 8) {
      throw new Error('Last player cannot make total equal 8');
    }

    networkService.send(this.state.roomId, 'declare', {
      value,
      player_name: this.state.playerName,
    });
  }

  playPieces(pieceIndices) {
    if (this.state.phase !== 'turn') {
      throw new Error(
        `Invalid action PLAY_PIECES for phase ${this.state.phase}`
      );
    }
    if (this.state.currentPlayer !== this.state.playerName) {
      throw new Error('Not your turn to play');
    }
    if (!Array.isArray(pieceIndices) || pieceIndices.length === 0) {
      throw new Error('Must select at least one piece');
    }

    // Validate piece indices
    for (const index of pieceIndices) {
      if (
        typeof index !== 'number' ||
        index < 0 ||
        index >= this.state.myHand.length
      ) {
        throw new Error(`Invalid piece index: ${index}`);
      }
    }

    networkService.send(this.state.roomId, 'play_pieces', {
      piece_indexes: pieceIndices,
      player_name: this.state.playerName,
    });
  }

  addStateListener(listener) {
    this.stateListeners.push(listener);
  }

  removeStateListener(listener) {
    const index = this.stateListeners.indexOf(listener);
    if (index > -1) {
      this.stateListeners.splice(index, 1);
    }
  }

  destroy() {
    if (this.state.roomId) {
      networkService.disconnectFromRoom(this.state.roomId);
    }
    this.stateListeners = [];
    this.isDestroyed = true;
    GameService.instance = null;
  }
}
