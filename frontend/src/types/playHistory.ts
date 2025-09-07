// Immutable TypeScript interfaces for Play History

export interface PlayHistory {
  readonly roomId: string;
  readonly rounds: ReadonlyArray<Round>;
  readonly players: ReadonlyArray<Player>;
  readonly gameStatus: Readonly<GameStatus>;
  readonly totalRounds: number;
  readonly startTime: string;
  readonly endTime: string | null;
}

export interface Player {
  readonly name: string;
  readonly type: 'human' | 'bot';
  readonly position: number;
}

export interface GameStatus {
  readonly completed: boolean;
  readonly winner: string | null;
  readonly finalScores: Readonly<Record<string, number>>;
}

export interface Round {
  readonly roundNumber: number;
  readonly starter: string;
  readonly declarations: ReadonlyArray<Declaration>;
  readonly turns: ReadonlyArray<Turn>;
  readonly scoring: Readonly<RoundScoring>;
  readonly winner: string;
  readonly timestamp: string;
  readonly handsDealt?: Readonly<Record<string, ReadonlyArray<Piece>>>;
  readonly finalCaptures?: Readonly<Record<string, number>>;
}

export interface Declaration {
  readonly player: string;
  readonly declared: number;
  readonly hand: ReadonlyArray<Piece>;
  readonly timestamp: string;
}

export interface Turn {
  readonly turnNumber: number;
  readonly plays: ReadonlyArray<Play>;
  readonly winner: string;
  readonly winnerPieces: number;
  readonly timestamp: string;
}

export interface Play {
  readonly player: string;
  readonly pieces: ReadonlyArray<Piece>;
  readonly isStarter: boolean;
  readonly handBefore: ReadonlyArray<Piece>;
  readonly handAfter: ReadonlyArray<Piece>;
  readonly captured: number;
}

export interface Piece {
  readonly type: string;
  readonly point: number;
  readonly color: 'red' | 'black';
}

export interface RoundScoring {
  readonly players: Readonly<Record<string, PlayerRoundScore>>;
  readonly bonuses: ReadonlyArray<Bonus>;
}

export interface PlayerRoundScore {
  readonly declared: number;
  readonly captured: number;
  readonly score: number;
  readonly multiplier: number;
  readonly baseScore: number;
}

export interface Bonus {
  readonly player: string;
  readonly type: string;
  readonly points: number;
  readonly description: string;
}

// Error types
export interface PlayHistoryError {
  readonly message: string;
  readonly code: string;
  readonly canRetry: boolean;
}

// Validation function signatures
export type ValidationResult = {
  readonly valid: boolean;
  readonly errors?: ReadonlyArray<string>;
};

export type ValidatePlayHistory = (data: unknown) => data is PlayHistory;
export type ValidateRound = (data: unknown) => data is Round;
export type ValidatePiece = (data: unknown) => data is Piece;
