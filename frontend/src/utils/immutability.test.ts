import { deepFreeze, updateImmutable, isFrozen } from './immutability';

describe('Immutability Helpers', () => {
  describe('deepFreeze', () => {
    it('should freeze primitive values', () => {
      expect(deepFreeze(42)).toBe(42);
      expect(deepFreeze('string')).toBe('string');
      expect(deepFreeze(true)).toBe(true);
      expect(deepFreeze(null)).toBe(null);
      expect(deepFreeze(undefined)).toBe(undefined);
    });

    it('should deep freeze objects', () => {
      const obj = { a: 1, b: { c: 2, d: { e: 3 } } };
      const frozen = deepFreeze(obj);

      expect(() => {
        // @ts-expect-error - Testing immutability
        frozen.a = 2;
      }).toThrow();

      expect(() => {
        // @ts-expect-error - Testing immutability
        frozen.b.c = 3;
      }).toThrow();

      expect(() => {
        // @ts-expect-error - Testing immutability
        frozen.b.d.e = 4;
      }).toThrow();
    });

    it('should deep freeze arrays', () => {
      const arr = [1, [2, [3, 4]], { a: 5 }];
      const frozen = deepFreeze(arr);

      expect(() => {
        // @ts-expect-error - Testing immutability
        frozen[0] = 10;
      }).toThrow();

      expect(() => {
        // @ts-expect-error - Testing immutability
        frozen[1][0] = 20;
      }).toThrow();

      expect(() => {
        // @ts-expect-error - Testing immutability
        frozen[1][1][0] = 30;
      }).toThrow();

      expect(() => {
        // @ts-expect-error - Testing immutability
        frozen[2].a = 50;
      }).toThrow();
    });

    it('should handle circular references', () => {
      const obj: any = { a: 1 };
      obj.self = obj;

      // Should not throw or cause infinite loop
      expect(() => deepFreeze(obj)).not.toThrow();
    });

    it('should preserve object prototype', () => {
      class CustomClass {
        value: number;
        constructor(val: number) {
          this.value = val;
        }
        getValue() {
          return this.value;
        }
      }

      const instance = new CustomClass(42);
      const frozen = deepFreeze(instance);

      expect(frozen).toBeInstanceOf(CustomClass);
      expect(frozen.getValue()).toBe(42);
    });
  });

  describe('updateImmutable', () => {
    it('should create immutable updates', () => {
      const original = { a: 1, b: 2, c: { d: 3 } };
      const updated = updateImmutable(original, { b: 20 });

      expect(original.b).toBe(2);
      expect(updated.b).toBe(20);
      expect(updated.a).toBe(1);
      expect(updated.c).toBe(original.c); // Unchanged properties are reused
      expect(original).not.toBe(updated);

      // Updated object should be frozen
      expect(() => {
        // @ts-expect-error - Testing immutability
        updated.a = 10;
      }).toThrow();
    });

    it('should handle nested updates', () => {
      const original = { a: 1, b: { c: 2, d: 3 } };
      const updated = updateImmutable(original, { b: { c: 20, d: 30 } });

      expect(original.b.c).toBe(2);
      expect(updated.b.c).toBe(20);
      expect(updated.b.d).toBe(30);
    });

    it('should add new properties', () => {
      const original: any = { a: 1 };
      const updated = updateImmutable(original, { b: 2 });

      expect(original.b).toBeUndefined();
      expect(updated.b).toBe(2);
    });
  });

  describe('isFrozen', () => {
    it('should return true for primitives', () => {
      expect(isFrozen(42)).toBe(true);
      expect(isFrozen('string')).toBe(true);
      expect(isFrozen(true)).toBe(true);
      expect(isFrozen(null)).toBe(true);
      expect(isFrozen(undefined)).toBe(true);
    });

    it('should detect frozen objects', () => {
      const obj = { a: 1 };
      expect(isFrozen(obj)).toBe(false);

      Object.freeze(obj);
      expect(isFrozen(obj)).toBe(true);
    });

    it('should detect deep frozen objects', () => {
      const obj = { a: 1, b: { c: 2 } };
      Object.freeze(obj);

      // Only shallow frozen
      expect(isFrozen(obj)).toBe(false);

      Object.freeze(obj.b);
      expect(isFrozen(obj)).toBe(true);
    });

    it('should detect frozen arrays', () => {
      const arr = [1, [2, 3], { a: 4 }];
      expect(isFrozen(arr)).toBe(false);

      deepFreeze(arr);
      expect(isFrozen(arr)).toBe(true);
    });

    it('should handle empty objects and arrays', () => {
      expect(isFrozen(Object.freeze({}))).toBe(true);
      expect(isFrozen(Object.freeze([]))).toBe(true);
    });
  });

  // Integration test
  describe('Integration', () => {
    it('should work with complex game data structures', () => {
      const gameData = {
        roomId: '23BEBA',
        rounds: [
          {
            roundNumber: 1,
            turns: [
              {
                turnNumber: 1,
                plays: [
                  {
                    player: 'Andy',
                    pieces: [
                      { type: 'GENERAL', point: 14, color: 'red' as const }
                    ]
                  }
                ]
              }
            ]
          }
        ]
      };

      const frozen = deepFreeze(gameData);

      expect(isFrozen(frozen)).toBe(true);

      // Test various mutations should throw
      expect(() => {
        // @ts-expect-error - Testing immutability
        frozen.roomId = 'CHANGED';
      }).toThrow();

      expect(() => {
        // @ts-expect-error - Testing immutability
        frozen.rounds[0].roundNumber = 2;
      }).toThrow();

      expect(() => {
        // @ts-expect-error - Testing immutability
        frozen.rounds[0].turns[0].plays[0].pieces[0].point = 15;
      }).toThrow();
    });
  });
});
