// frontend/tests/game/GameStateManager.test.js

import { GameStateManager } from '../../game/GameStateManager.js';

describe('GameStateManager', () => {
  let stateManager;
  
  const mockGameData = {
    round: 1,
    starter: 'Player1',
    players: [
      { name: 'Player1', score: 0, is_bot: false },
      { name: 'Player2', score: 0, is_bot: false },
      { name: 'Bot3', score: 0, is_bot: true },
      { name: 'Bot4', score: 0, is_bot: true }
    ],
    hands: {
      'Player1': ['GENERAL_RED(14)', 'SOLDIER_RED(2)', 'HORSE_BLACK(5)']
    }
  };
  
  beforeEach(() => {
    stateManager = new GameStateManager('TEST123', 'Player1', mockGameData);
  });
  
  describe('Initialization', () => {
    test('should initialize with correct state', () => {
      expect(stateManager.roomId).toBe('TEST123');
      expect(stateManager.playerName).toBe('Player1');
      expect(stateManager.currentRound).toBe(1);
      expect(stateManager.players).toHaveLength(4);
      expect(stateManager.myHand).toHaveLength(3);
    });
    
    test('should identify player data correctly', () => {
      const myPlayer = stateManager.getMyPlayer();
      expect(myPlayer).toBeDefined();
      expect(myPlayer.name).toBe('Player1');
      expect(myPlayer.is_bot).toBe(false);
    });
    
    test('should set declaration order based on starter', () => {
      expect(stateManager.declarationOrder[0].name).toBe('Player1');
      expect(stateManager.declarationOrder[1].name).toBe('Player2');
    });
  });
  
  describe('Declaration Management', () => {
    test('should track player declarations', () => {
      stateManager.addDeclaration('Player1', 3);
      expect(stateManager.declarations['Player1']).toBe(3);
    });
    
    test('should emit event when declaration added', (done) => {
      stateManager.on('declarationAdded', (data) => {
        expect(data.player).toBe('Player2');
        expect(data.value).toBe(2);
        done();
      });
      
      stateManager.addDeclaration('Player2', 2);
    });
    
    test('should detect when all players declared', (done) => {
      stateManager.on('allPlayersDeclarated', (data) => {
        expect(data.total).toBe(10);
        done();
      });
      
      stateManager.addDeclaration('Player1', 3);
      stateManager.addDeclaration('Player2', 2);
      stateManager.addDeclaration('Bot3', 4);
      stateManager.addDeclaration('Bot4', 1);
    });
    
    test('should calculate valid declaration options', () => {
      // Normal case
      let options = stateManager.getValidDeclarationOptions(false);
      expect(options).toContain(0);
      expect(options).toContain(8);
      
      // Last player with total that would make 8
      stateManager.addDeclaration('Player2', 3);
      stateManager.addDeclaration('Bot3', 2);
      stateManager.addDeclaration('Bot4', 1);
      
      options = stateManager.getValidDeclarationOptions(true);
      expect(options).not.toContain(2); // Would make total 8
    });
    
    test('should enforce zero streak rule', () => {
      // Simulate player with zero streak
      stateManager.myPlayerData.zero_declares_in_a_row = 2;
      
      const options = stateManager.getValidDeclarationOptions(false);
      expect(options).not.toContain(0);
      expect(options[0]).toBeGreaterThan(0);
    });
  });
  
  describe('Turn Management', () => {
    test('should start new turn correctly', () => {
      stateManager.startNewTurn('Player2');
      
      expect(stateManager.currentTurnNumber).toBe(1);
      expect(stateManager.currentTurnStarter).toBe('Player2');
      expect(stateManager.turnOrder[0].name).toBe('Player2');
    });
    
    test('should track turn plays', () => {
      stateManager.startNewTurn('Player1');
      
      stateManager.addTurnPlay('Player1', ['GENERAL_RED', 'SOLDIER_RED'], true);
      expect(stateManager.currentTurnPlays).toHaveLength(1);
      expect(stateManager.requiredPieceCount).toBe(2);
    });
    
    test('should determine if its my turn', () => {
      stateManager.startNewTurn('Player1');
      
      // First player's turn
      expect(stateManager.isMyTurnToPlay()).toBe(true);
      
      // After playing
      stateManager.addTurnPlay('Player1', ['GENERAL_RED'], true);
      expect(stateManager.isMyTurnToPlay()).toBe(false);
    });
  });
  
  describe('Hand Management', () => {
    test('should update hand and emit event', (done) => {
      const newHand = ['CANNON_BLACK(3)', 'HORSE_RED(6)'];
      
      stateManager.on('handUpdated', (data) => {
        expect(data.oldHand).toHaveLength(3);
        expect(data.newHand).toHaveLength(2);
        done();
      });
      
      stateManager.updateHand(newHand);
    });
    
    test('should remove pieces from hand', () => {
      const removed = stateManager.removeFromHand([0, 2]);
      
      expect(removed).toHaveLength(2);
      expect(removed[0]).toBe('GENERAL_RED(14)');
      expect(removed[1]).toBe('HORSE_BLACK(5)');
      expect(stateManager.myHand).toHaveLength(1);
      expect(stateManager.myHand[0]).toBe('SOLDIER_RED(2)');
    });
  });
  
  describe('Progress Tracking', () => {
    test('should track declaration progress', () => {
      stateManager.addDeclaration('Player1', 3);
      stateManager.addDeclaration('Player2', 2);
      
      const progress = stateManager.getDeclarationProgress();
      expect(progress.declared).toBe(2);
      expect(progress.total).toBe(4);
      expect(progress.percentage).toBe(50);
    });
    
    test('should track turn progress', () => {
      stateManager.startNewTurn('Player1');
      stateManager.addTurnPlay('Player1', ['GENERAL_RED'], true);
      stateManager.addTurnPlay('Player2', ['SOLDIER_BLACK'], true);
      
      const progress = stateManager.getTurnProgress();
      expect(progress.played).toBe(2);
      expect(progress.total).toBe(4);
      expect(progress.percentage).toBe(50);
    });
  });
  
  describe('Round Reset', () => {
    test('should reset state for new round', () => {
      // Set up some state
      stateManager.addDeclaration('Player1', 3);
      stateManager.startNewTurn('Player1');
      
      // Reset for new round
      stateManager.resetForNewRound({
        round: 2,
        starter: 'Player2',
        hands: {
          'Player1': ['CANNON_RED(4)', 'ELEPHANT_BLACK(9)']
        }
      });
      
      expect(stateManager.currentRound).toBe(2);
      expect(stateManager.roundStarter).toBe('Player2');
      expect(stateManager.myHand).toHaveLength(2);
      expect(stateManager.declarations).toEqual({});
      expect(stateManager.currentTurnNumber).toBe(0);
    });
  });
});