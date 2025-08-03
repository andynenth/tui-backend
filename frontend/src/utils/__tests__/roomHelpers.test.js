/**
 * Room Helpers Tests
 *
 * Tests for room-related utility functions including:
 * - Bot name generation
 * - Room status text generation
 * - Player display names
 * - Room occupancy text
 * - Room join eligibility
 */

import {
  getBotName,
  getRoomStatusText,
  getPlayerDisplayName,
  getRoomOccupancyText,
  canJoinRoom,
} from '../roomHelpers';

describe('Room Helpers Utilities', () => {
  describe('getBotName', () => {
    test('generates correct bot name for slot number', () => {
      expect(getBotName(1)).toBe('Bot 1');
      expect(getBotName(2)).toBe('Bot 2');
      expect(getBotName(3)).toBe('Bot 3');
      expect(getBotName(4)).toBe('Bot 4');
    });

    test('handles edge case slot numbers', () => {
      expect(getBotName(0)).toBe('Bot 0');
      expect(getBotName(10)).toBe('Bot 10');
      expect(getBotName(-1)).toBe('Bot -1');
    });

    test('handles non-numeric input', () => {
      expect(getBotName('1')).toBe('Bot 1');
      expect(getBotName('test')).toBe('Bot test');
      expect(getBotName(null)).toBe('Bot null');
      expect(getBotName(undefined)).toBe('Bot undefined');
    });
  });

  describe('getRoomStatusText', () => {
    test('returns ready message when room is full', () => {
      expect(getRoomStatusText(4, 4)).toBe(
        'All players ready - Start the game!'
      );
      expect(getRoomStatusText(2, 2)).toBe(
        'All players ready - Start the game!'
      );
    });

    test('returns waiting message when room is not full', () => {
      expect(getRoomStatusText(3, 4)).toBe('Waiting for players to join');
      expect(getRoomStatusText(0, 4)).toBe('Waiting for players to join');
      expect(getRoomStatusText(1, 2)).toBe('Waiting for players to join');
    });

    test('uses default maxPlayers of 4 when not specified', () => {
      expect(getRoomStatusText(4)).toBe('All players ready - Start the game!');
      expect(getRoomStatusText(3)).toBe('Waiting for players to join');
    });

    test('handles edge cases', () => {
      expect(getRoomStatusText(0, 0)).toBe(
        'All players ready - Start the game!'
      );
      expect(getRoomStatusText(-1, 4)).toBe('Waiting for players to join');
      expect(getRoomStatusText(5, 4)).toBe('Waiting for players to join'); // Over capacity still treated as not full
    });
  });

  describe('getPlayerDisplayName', () => {
    test('returns "Waiting..." for null player', () => {
      expect(getPlayerDisplayName(null, 1)).toBe('Waiting...');
      expect(getPlayerDisplayName(undefined, 2)).toBe('Waiting...');
    });

    test('returns bot name for bot players', () => {
      const botPlayer = { name: 'Bot1', is_bot: true };
      expect(getPlayerDisplayName(botPlayer, 1)).toBe('Bot 1');
      expect(getPlayerDisplayName(botPlayer, 3)).toBe('Bot 3');
    });

    test('returns player name for human players', () => {
      const humanPlayer = { name: 'Alice', is_bot: false };
      expect(getPlayerDisplayName(humanPlayer, 1)).toBe('Alice');

      const humanPlayerNoFlag = { name: 'Bob' }; // is_bot undefined
      expect(getPlayerDisplayName(humanPlayerNoFlag, 2)).toBe('Bob');
    });

    test('handles edge cases', () => {
      const playerWithEmptyName = { name: '', is_bot: false };
      expect(getPlayerDisplayName(playerWithEmptyName, 1)).toBe('');

      const playerWithNullName = { name: null, is_bot: false };
      expect(getPlayerDisplayName(playerWithNullName, 1)).toBeNull();

      const botWithHumanName = { name: 'Alice', is_bot: true };
      expect(getPlayerDisplayName(botWithHumanName, 2)).toBe('Bot 2'); // Ignores name for bots
    });
  });

  describe('getRoomOccupancyText', () => {
    test('returns "In Game" status for started rooms', () => {
      const startedRoom = {
        players: [{ name: 'Alice' }, { name: 'Bob' }, null, null],
        total_slots: 4,
        started: true,
      };
      expect(getRoomOccupancyText(startedRoom)).toBe('🎮 In Game (2/4)');

      const playingRoom = {
        players: [
          { name: 'Alice' },
          { name: 'Bob' },
          { name: 'Charlie' },
          null,
        ],
        total_slots: 4,
        status: 'playing',
      };
      expect(getRoomOccupancyText(playingRoom)).toBe('🎮 In Game (3/4)');
    });

    test('returns "Full" status for full rooms', () => {
      const fullRoom = {
        players: [
          { name: 'Alice' },
          { name: 'Bob' },
          { name: 'Charlie' },
          { name: 'Diana' },
        ],
        total_slots: 4,
        started: false,
      };
      expect(getRoomOccupancyText(fullRoom)).toBe('🔒 Full (4/4)');
    });

    test('returns "Waiting" status for partial rooms', () => {
      const partialRoom = {
        players: [{ name: 'Alice' }, { name: 'Bob' }, null, null],
        total_slots: 4,
        started: false,
      };
      expect(getRoomOccupancyText(partialRoom)).toBe('⏳ Waiting (2/4)');

      const emptyRoom = {
        players: [null, null, null, null],
        total_slots: 4,
        started: false,
      };
      expect(getRoomOccupancyText(emptyRoom)).toBe('⏳ Waiting (0/4)');
    });

    test('handles missing or malformed room data', () => {
      // No players array
      const noPlayersRoom = { total_slots: 4, started: false };
      expect(getRoomOccupancyText(noPlayersRoom)).toBe('⏳ Waiting (0/4)');

      // No total_slots (defaults to 4)
      const noSlotsRoom = {
        players: [{ name: 'Alice' }, null, null, null],
        started: false,
      };
      expect(getRoomOccupancyText(noSlotsRoom)).toBe('⏳ Waiting (1/4)');

      // Empty room object
      const emptyRoom = {};
      expect(getRoomOccupancyText(emptyRoom)).toBe('⏳ Waiting (0/4)');

      // Null room
      expect(() => getRoomOccupancyText(null)).toThrow();
    });

    test('handles different total_slots values', () => {
      const twoPlayerRoom = {
        players: [{ name: 'Alice' }, { name: 'Bob' }],
        total_slots: 2,
        started: false,
      };
      expect(getRoomOccupancyText(twoPlayerRoom)).toBe('🔒 Full (2/2)');

      const sixPlayerRoom = {
        players: [{ name: 'Alice' }, null, null, null, null, null],
        total_slots: 6,
        started: false,
      };
      expect(getRoomOccupancyText(sixPlayerRoom)).toBe('⏳ Waiting (1/6)');
    });

    test('prioritizes "started" over "status" field', () => {
      const conflictingRoom = {
        players: [{ name: 'Alice' }, { name: 'Bob' }, null, null],
        total_slots: 4,
        started: true,
        status: 'waiting', // Conflicting status
      };
      expect(getRoomOccupancyText(conflictingRoom)).toBe('🎮 In Game (2/4)');
    });
  });

  describe('canJoinRoom', () => {
    test('allows joining when room is not started and not full', () => {
      const joinableRoom = {
        players: [{ name: 'Alice' }, { name: 'Bob' }, null, null],
        total_slots: 4,
        started: false,
      };
      expect(canJoinRoom(joinableRoom)).toBe(true);

      const emptyRoom = {
        players: [null, null, null, null],
        total_slots: 4,
        started: false,
      };
      expect(canJoinRoom(emptyRoom)).toBe(true);
    });

    test('prevents joining when room is started', () => {
      const startedRoom = {
        players: [{ name: 'Alice' }, null, null, null],
        total_slots: 4,
        started: true,
      };
      expect(canJoinRoom(startedRoom)).toBe(false);
    });

    test('prevents joining when room is full', () => {
      const fullRoom = {
        players: [
          { name: 'Alice' },
          { name: 'Bob' },
          { name: 'Charlie' },
          { name: 'Diana' },
        ],
        total_slots: 4,
        started: false,
      };
      expect(canJoinRoom(fullRoom)).toBe(false);
    });

    test('prevents joining when room is both started and full', () => {
      const startedFullRoom = {
        players: [
          { name: 'Alice' },
          { name: 'Bob' },
          { name: 'Charlie' },
          { name: 'Diana' },
        ],
        total_slots: 4,
        started: true,
      };
      expect(canJoinRoom(startedFullRoom)).toBe(false);
    });

    test('handles missing or malformed room data', () => {
      // No players array
      const noPlayersRoom = { total_slots: 4, started: false };
      expect(canJoinRoom(noPlayersRoom)).toBe(true);

      // No total_slots (defaults to 4)
      const noSlotsRoom = {
        players: [{ name: 'Alice' }, null, null, null],
        started: false,
      };
      expect(canJoinRoom(noSlotsRoom)).toBe(true);

      // No started field (falsy)
      const noStartedRoom = {
        players: [{ name: 'Alice' }, null, null, null],
        total_slots: 4,
      };
      expect(canJoinRoom(noStartedRoom)).toBe(true);

      // Empty room object
      const emptyRoom = {};
      expect(canJoinRoom(emptyRoom)).toBe(true);

      // Null room
      expect(() => canJoinRoom(null)).toThrow();
    });

    test('handles edge cases with player count', () => {
      // Over capacity (should not be joinable)
      const overCapacityRoom = {
        players: [
          { name: 'A' },
          { name: 'B' },
          { name: 'C' },
          { name: 'D' },
          { name: 'E' },
        ],
        total_slots: 4,
        started: false,
      };
      expect(canJoinRoom(overCapacityRoom)).toBe(false);

      // Zero capacity room (0 < 0 is false, so can join)
      const zeroCapacityRoom = {
        players: [],
        total_slots: 0,
        started: false,
      };
      expect(canJoinRoom(zeroCapacityRoom)).toBe(true); // 0 < 0 is false, so technically joinable
    });

    test('handles different room configurations', () => {
      // 2-player room with 1 player
      const twoPlayerRoom = {
        players: [{ name: 'Alice' }, null],
        total_slots: 2,
        started: false,
      };
      expect(canJoinRoom(twoPlayerRoom)).toBe(true);

      // 2-player room full
      const fullTwoPlayerRoom = {
        players: [{ name: 'Alice' }, { name: 'Bob' }],
        total_slots: 2,
        started: false,
      };
      expect(canJoinRoom(fullTwoPlayerRoom)).toBe(false);

      // 6-player room with 3 players
      const sixPlayerRoom = {
        players: [
          { name: 'A' },
          { name: 'B' },
          { name: 'C' },
          null,
          null,
          null,
        ],
        total_slots: 6,
        started: false,
      };
      expect(canJoinRoom(sixPlayerRoom)).toBe(true);
    });
  });

  describe('Integration and Complex Scenarios', () => {
    test('functions work together consistently', () => {
      const room = {
        players: [
          { name: 'Alice', is_bot: false },
          { name: 'BotPlayer', is_bot: true },
          null,
          null,
        ],
        total_slots: 4,
        started: false,
      };

      // Check occupancy text
      expect(getRoomOccupancyText(room)).toBe('⏳ Waiting (2/4)');

      // Check if joinable
      expect(canJoinRoom(room)).toBe(true);

      // Check status text
      expect(getRoomStatusText(2, 4)).toBe('Waiting for players to join');

      // Check player display names
      expect(getPlayerDisplayName(room.players[0], 1)).toBe('Alice');
      expect(getPlayerDisplayName(room.players[1], 2)).toBe('Bot 2');
      expect(getPlayerDisplayName(room.players[2], 3)).toBe('Waiting...');
    });

    test('handles room state transitions', () => {
      const room = {
        players: [{ name: 'Alice' }, null, null, null],
        total_slots: 4,
        started: false,
      };

      // Initially joinable
      expect(canJoinRoom(room)).toBe(true);
      expect(getRoomOccupancyText(room)).toBe('⏳ Waiting (1/4)');

      // Add players until full
      room.players = [
        { name: 'Alice' },
        { name: 'Bob' },
        { name: 'Charlie' },
        { name: 'Diana' },
      ];
      expect(canJoinRoom(room)).toBe(false);
      expect(getRoomOccupancyText(room)).toBe('🔒 Full (4/4)');

      // Start the game
      room.started = true;
      expect(canJoinRoom(room)).toBe(false);
      expect(getRoomOccupancyText(room)).toBe('🎮 In Game (4/4)');
    });

    test('maintains consistency across different room sizes', () => {
      const roomSizes = [2, 4, 6, 8];

      roomSizes.forEach((size) => {
        const emptyRoom = {
          players: new Array(size).fill(null),
          total_slots: size,
          started: false,
        };

        expect(canJoinRoom(emptyRoom)).toBe(true);
        expect(getRoomOccupancyText(emptyRoom)).toBe(`⏳ Waiting (0/${size})`);
        expect(getRoomStatusText(0, size)).toBe('Waiting for players to join');

        const fullRoom = {
          players: new Array(size).fill({ name: 'Player' }),
          total_slots: size,
          started: false,
        };

        expect(canJoinRoom(fullRoom)).toBe(false);
        expect(getRoomOccupancyText(fullRoom)).toBe(
          `🔒 Full (${size}/${size})`
        );
        expect(getRoomStatusText(size, size)).toBe(
          'All players ready - Start the game!'
        );
      });
    });
  });
});
