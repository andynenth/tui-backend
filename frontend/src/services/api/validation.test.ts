import {
  validatePlayHistory,
  validateRound,
  validatePiece
} from './validation';
import { mockPlayHistory } from '../../mocks/playHistoryMock';

describe('Validation Functions', () => {
  describe('validatePlayHistory', () => {
    it('should validate complete play history', () => {
      expect(validatePlayHistory(mockPlayHistory)).toBe(true);
    });

    it('should reject null or undefined', () => {
      expect(validatePlayHistory(null)).toBe(false);
      expect(validatePlayHistory(undefined)).toBe(false);
    });

    it('should reject non-object types', () => {
      expect(validatePlayHistory('string')).toBe(false);
      expect(validatePlayHistory(123)).toBe(false);
      expect(validatePlayHistory([])).toBe(false);
    });

    it('should reject missing required fields', () => {
      const invalidData = { ...mockPlayHistory };
      delete invalidData.roomId;
      expect(validatePlayHistory(invalidData)).toBe(false);

      const missingRounds = { ...mockPlayHistory, rounds: undefined };
      expect(validatePlayHistory(missingRounds)).toBe(false);

      const missingPlayers = { ...mockPlayHistory, players: undefined };
      expect(validatePlayHistory(missingPlayers)).toBe(false);
    });

    it('should reject invalid rounds', () => {
      const invalidRounds = {
        ...mockPlayHistory,
        rounds: [{ invalid: 'round' }]
      };
      expect(validatePlayHistory(invalidRounds)).toBe(false);
    });

    it('should accept null endTime for ongoing games', () => {
      const ongoingGame = {
        ...mockPlayHistory,
        endTime: null
      };
      expect(validatePlayHistory(ongoingGame)).toBe(true);
    });
  });

  describe('validateRound', () => {
    const validRound = mockPlayHistory.rounds[0];

    it('should validate a complete round', () => {
      expect(validateRound(validRound)).toBe(true);
    });

    it('should reject invalid round structures', () => {
      expect(validateRound(null)).toBe(false);
      expect(validateRound({})).toBe(false);
      expect(validateRound({ roundNumber: 1 })).toBe(false);
    });

    it('should reject missing required fields', () => {
      const invalidRound = { ...validRound };
      delete invalidRound.roundNumber;
      expect(validateRound(invalidRound)).toBe(false);

      const noStarter = { ...validRound, starter: undefined };
      expect(validateRound(noStarter)).toBe(false);

      const noTurns = { ...validRound, turns: undefined };
      expect(validateRound(noTurns)).toBe(false);
    });

    it('should reject invalid declarations', () => {
      const invalidDeclarations = {
        ...validRound,
        declarations: [{ player: 'test' }] // missing required fields
      };
      expect(validateRound(invalidDeclarations)).toBe(false);
    });

    it('should reject invalid turns', () => {
      const invalidTurns = {
        ...validRound,
        turns: [{ turnNumber: 1 }] // missing required fields
      };
      expect(validateRound(invalidTurns)).toBe(false);
    });
  });

  describe('validatePiece', () => {
    it('should validate red pieces', () => {
      expect(validatePiece({
        type: 'GENERAL',
        point: 14,
        color: 'red'
      })).toBe(true);
    });

    it('should validate black pieces', () => {
      expect(validatePiece({
        type: 'ADVISOR',
        point: 12,
        color: 'black'
      })).toBe(true);
    });

    it('should reject invalid piece structures', () => {
      expect(validatePiece(null)).toBe(false);
      expect(validatePiece({})).toBe(false);
      expect(validatePiece({ type: 'GENERAL' })).toBe(false);
    });

    it('should reject invalid colors', () => {
      expect(validatePiece({
        type: 'GENERAL',
        point: 14,
        color: 'blue' // invalid color
      })).toBe(false);
    });

    it('should reject non-number points', () => {
      expect(validatePiece({
        type: 'GENERAL',
        point: '14', // string instead of number
        color: 'red'
      })).toBe(false);
    });

    it('should reject NaN points', () => {
      expect(validatePiece({
        type: 'GENERAL',
        point: NaN,
        color: 'red'
      })).toBe(false);
    });
  });

  // Test helper functions for edge cases
  describe('Edge Cases', () => {
    it('should handle deeply nested invalid data', () => {
      const deeplyInvalid = {
        ...mockPlayHistory,
        rounds: [{
          ...mockPlayHistory.rounds[0],
          turns: [{
            ...mockPlayHistory.rounds[0].turns[0],
            plays: [{
              player: 'test',
              pieces: [{ invalid: 'piece' }] // invalid piece structure
            }]
          }]
        }]
      };
      expect(validatePlayHistory(deeplyInvalid)).toBe(false);
    });

    it('should handle empty arrays', () => {
      const emptyRounds = {
        ...mockPlayHistory,
        rounds: []
      };
      expect(validatePlayHistory(emptyRounds)).toBe(true); // empty arrays are valid

      const emptyPlayers = {
        ...mockPlayHistory,
        players: []
      };
      expect(validatePlayHistory(emptyPlayers)).toBe(true);
    });

    it('should validate complex scoring structures', () => {
      const validScoring = mockPlayHistory.rounds[0].scoring;
      expect(validScoring.players).toBeDefined();
      expect(Object.values(validScoring.players).every(score =>
        typeof score.declared === 'number' &&
        typeof score.captured === 'number' &&
        typeof score.score === 'number'
      )).toBe(true);
    });
  });
});
