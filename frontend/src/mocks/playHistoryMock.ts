import { PlayHistory } from '../types/playHistory';

export const mockPlayHistory: PlayHistory = {
  roomId: "23BEBA",
  totalRounds: 5,
  startTime: "2024-08-11T10:00:00Z",
  endTime: "2024-08-11T10:45:00Z",
  gameStatus: {
    completed: true,
    winner: "Bot 2",
    finalScores: {
      "Andy": 42,
      "Bot 1": 38,
      "Bot 2": 56,
      "Bot 3": 45
    }
  },
  players: [
    { name: "Andy", type: "human", position: 0 },
    { name: "Bot 1", type: "bot", position: 1 },
    { name: "Bot 2", type: "bot", position: 2 },
    { name: "Bot 3", type: "bot", position: 3 }
  ],
  rounds: [
    {
      roundNumber: 1,
      starter: "Bot 3",
      timestamp: "2024-08-11T10:01:00Z",
      winner: "Bot 2",
      declarations: [
        {
          player: "Bot 3",
          declared: 6,
          hand: [
            { type: "GENERAL", point: 14, color: "red" },
            { type: "ADVISOR", point: 12, color: "red" },
            { type: "ELEPHANT", point: 10, color: "red" },
            { type: "HORSE", point: 6, color: "red" },
            { type: "GENERAL", point: 14, color: "black" },
            { type: "ADVISOR", point: 11, color: "black" },
            { type: "ELEPHANT", point: 9, color: "black" },
            { type: "HORSE", point: 5, color: "black" }
          ],
          timestamp: "2024-08-11T10:01:10Z"
        },
        {
          player: "Andy",
          declared: 3,
          hand: [
            { type: "GENERAL", point: 13, color: "red" },
            { type: "ADVISOR", point: 12, color: "red" },
            { type: "ELEPHANT", point: 10, color: "red" },
            { type: "CHARIOT", point: 3, color: "red" },
            { type: "HORSE", point: 6, color: "black" },
            { type: "ELEPHANT", point: 9, color: "black" },
            { type: "CHARIOT", point: 3, color: "black" },
            { type: "SOLDIER", point: 1, color: "black" }
          ],
          timestamp: "2024-08-11T10:01:15Z"
        },
        {
          player: "Bot 1",
          declared: 5,
          hand: [
            { type: "ADVISOR", point: 12, color: "red" },
            { type: "ELEPHANT", point: 9, color: "red" },
            { type: "HORSE", point: 5, color: "red" },
            { type: "CHARIOT", point: 4, color: "red" },
            { type: "GENERAL", point: 13, color: "black" },
            { type: "ADVISOR", point: 11, color: "black" },
            { type: "HORSE", point: 6, color: "black" },
            { type: "SOLDIER", point: 2, color: "black" }
          ],
          timestamp: "2024-08-11T10:01:20Z"
        },
        {
          player: "Bot 2",
          declared: 4,
          hand: [
            { type: "ADVISOR", point: 11, color: "red" },
            { type: "ELEPHANT", point: 10, color: "red" },
            { type: "CHARIOT", point: 4, color: "red" },
            { type: "SOLDIER", point: 2, color: "red" },
            { type: "ADVISOR", point: 12, color: "black" },
            { type: "ELEPHANT", point: 10, color: "black" },
            { type: "HORSE", point: 5, color: "black" },
            { type: "CHARIOT", point: 3, color: "black" }
          ],
          timestamp: "2024-08-11T10:01:25Z"
        }
      ],
      turns: [
        {
          turnNumber: 1,
          timestamp: "2024-08-11T10:02:00Z",
          winner: "Bot 3",
          winnerPieces: 3,
          plays: [
            {
              player: "Bot 3",
              isStarter: true,
              pieces: [
                { type: "GENERAL", point: 14, color: "black" },
                { type: "ADVISOR", point: 11, color: "black" },
                { type: "ELEPHANT", point: 9, color: "black" }
              ],
              handBefore: [
                { type: "GENERAL", point: 14, color: "red" },
                { type: "ADVISOR", point: 12, color: "red" },
                { type: "ELEPHANT", point: 10, color: "red" },
                { type: "HORSE", point: 6, color: "red" },
                { type: "GENERAL", point: 14, color: "black" },
                { type: "ADVISOR", point: 11, color: "black" },
                { type: "ELEPHANT", point: 9, color: "black" },
                { type: "HORSE", point: 5, color: "black" }
              ],
              handAfter: [
                { type: "GENERAL", point: 14, color: "red" },
                { type: "ADVISOR", point: 12, color: "red" },
                { type: "ELEPHANT", point: 10, color: "red" },
                { type: "HORSE", point: 6, color: "red" },
                { type: "HORSE", point: 5, color: "black" }
              ],
              captured: 3
            },
            {
              player: "Andy",
              isStarter: false,
              pieces: [
                { type: "CHARIOT", point: 3, color: "red" },
                { type: "CHARIOT", point: 3, color: "black" },
                { type: "SOLDIER", point: 1, color: "black" }
              ],
              handBefore: [
                { type: "GENERAL", point: 13, color: "red" },
                { type: "ADVISOR", point: 12, color: "red" },
                { type: "ELEPHANT", point: 10, color: "red" },
                { type: "CHARIOT", point: 3, color: "red" },
                { type: "HORSE", point: 6, color: "black" },
                { type: "ELEPHANT", point: 9, color: "black" },
                { type: "CHARIOT", point: 3, color: "black" },
                { type: "SOLDIER", point: 1, color: "black" }
              ],
              handAfter: [
                { type: "GENERAL", point: 13, color: "red" },
                { type: "ADVISOR", point: 12, color: "red" },
                { type: "ELEPHANT", point: 10, color: "red" },
                { type: "HORSE", point: 6, color: "black" },
                { type: "ELEPHANT", point: 9, color: "black" }
              ],
              captured: 0
            },
            {
              player: "Bot 1",
              isStarter: false,
              pieces: [
                { type: "HORSE", point: 5, color: "red" },
                { type: "CHARIOT", point: 4, color: "red" },
                { type: "SOLDIER", point: 2, color: "black" }
              ],
              handBefore: [
                { type: "ADVISOR", point: 12, color: "red" },
                { type: "ELEPHANT", point: 9, color: "red" },
                { type: "HORSE", point: 5, color: "red" },
                { type: "CHARIOT", point: 4, color: "red" },
                { type: "GENERAL", point: 13, color: "black" },
                { type: "ADVISOR", point: 11, color: "black" },
                { type: "HORSE", point: 6, color: "black" },
                { type: "SOLDIER", point: 2, color: "black" }
              ],
              handAfter: [
                { type: "ADVISOR", point: 12, color: "red" },
                { type: "ELEPHANT", point: 9, color: "red" },
                { type: "GENERAL", point: 13, color: "black" },
                { type: "ADVISOR", point: 11, color: "black" },
                { type: "HORSE", point: 6, color: "black" }
              ],
              captured: 0
            },
            {
              player: "Bot 2",
              isStarter: false,
              pieces: [
                { type: "ADVISOR", point: 11, color: "red" },
                { type: "ELEPHANT", point: 10, color: "red" },
                { type: "CHARIOT", point: 4, color: "red" }
              ],
              handBefore: [
                { type: "ADVISOR", point: 11, color: "red" },
                { type: "ELEPHANT", point: 10, color: "red" },
                { type: "CHARIOT", point: 4, color: "red" },
                { type: "SOLDIER", point: 2, color: "red" },
                { type: "ADVISOR", point: 12, color: "black" },
                { type: "ELEPHANT", point: 10, color: "black" },
                { type: "HORSE", point: 5, color: "black" },
                { type: "CHARIOT", point: 3, color: "black" }
              ],
              handAfter: [
                { type: "SOLDIER", point: 2, color: "red" },
                { type: "ADVISOR", point: 12, color: "black" },
                { type: "ELEPHANT", point: 10, color: "black" },
                { type: "HORSE", point: 5, color: "black" },
                { type: "CHARIOT", point: 3, color: "black" }
              ],
              captured: 0
            }
          ]
        }
      ],
      scoring: {
        players: {
          "Bot 3": { declared: 6, captured: 3, baseScore: -3, multiplier: 1, score: -3 },
          "Andy": { declared: 3, captured: 0, baseScore: -3, multiplier: 1, score: -3 },
          "Bot 1": { declared: 5, captured: 0, baseScore: -5, multiplier: 1, score: -5 },
          "Bot 2": { declared: 4, captured: 0, baseScore: -4, multiplier: 1, score: -4 }
        },
        bonuses: []
      }
    }
  ]
};
