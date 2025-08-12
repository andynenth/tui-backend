import {
  PlayHistory,
  Player,
  GameStatus,
  Round,
  Declaration,
  Turn,
  Play,
  Piece,
  RoundScoring,
  PlayerRoundScore,
  ValidatePlayHistory,
  ValidateRound,
  ValidatePiece
} from '../../types/playHistory';

/**
 * Type guard to check if a value is a valid PlayHistory object
 */
export const validatePlayHistory: ValidatePlayHistory = (data: unknown): data is PlayHistory => {
  if (!isObject(data)) return false;
  
  return (
    isString(data.roomId) &&
    isArray(data.rounds) &&
    data.rounds.every(validateRound) &&
    isArray(data.players) &&
    data.players.every(validatePlayer) &&
    validateGameStatus(data.gameStatus) &&
    isNumber(data.totalRounds) &&
    isString(data.startTime) &&
    (data.endTime === null || isString(data.endTime))
  );
};

/**
 * Type guard to check if a value is a valid Round object
 */
export const validateRound: ValidateRound = (data: unknown): data is Round => {
  if (!isObject(data)) return false;
  
  return (
    isNumber(data.roundNumber) &&
    isString(data.starter) &&
    isArray(data.declarations) &&
    data.declarations.every(validateDeclaration) &&
    isArray(data.turns) &&
    data.turns.every(validateTurn) &&
    validateRoundScoring(data.scoring) &&
    isString(data.winner) &&
    isString(data.timestamp)
  );
};

/**
 * Type guard to check if a value is a valid Piece object
 */
export const validatePiece: ValidatePiece = (data: unknown): data is Piece => {
  if (!isObject(data)) return false;
  
  return (
    isString(data.type) &&
    isNumber(data.point) &&
    (data.color === 'red' || data.color === 'black')
  );
};

// Helper validation functions
function validatePlayer(data: unknown): data is Player {
  if (!isObject(data)) return false;
  
  return (
    isString(data.name) &&
    (data.type === 'human' || data.type === 'bot') &&
    isNumber(data.position)
  );
}

function validateGameStatus(data: unknown): data is GameStatus {
  if (!isObject(data)) return false;
  
  return (
    typeof data.completed === 'boolean' &&
    (data.winner === null || isString(data.winner)) &&
    isObject(data.finalScores) &&
    Object.values(data.finalScores).every(isNumber)
  );
}

function validateDeclaration(data: unknown): data is Declaration {
  if (!isObject(data)) return false;
  
  return (
    isString(data.player) &&
    isNumber(data.declared) &&
    isArray(data.hand) &&
    data.hand.every(validatePiece) &&
    isString(data.timestamp)
  );
}

function validateTurn(data: unknown): data is Turn {
  if (!isObject(data)) return false;
  
  return (
    isNumber(data.turnNumber) &&
    isArray(data.plays) &&
    data.plays.every(validatePlay) &&
    isString(data.winner) &&
    isNumber(data.winnerPieces) &&
    isString(data.timestamp)
  );
}

function validatePlay(data: unknown): data is Play {
  if (!isObject(data)) return false;
  
  return (
    isString(data.player) &&
    isArray(data.pieces) &&
    data.pieces.every(validatePiece) &&
    typeof data.isStarter === 'boolean' &&
    isArray(data.handBefore) &&
    data.handBefore.every(validatePiece) &&
    isArray(data.handAfter) &&
    data.handAfter.every(validatePiece) &&
    isNumber(data.captured)
  );
}

function validateRoundScoring(data: unknown): data is RoundScoring {
  if (!isObject(data)) return false;
  
  return (
    isObject(data.players) &&
    Object.values(data.players).every(validatePlayerRoundScore) &&
    isArray(data.bonuses) &&
    data.bonuses.every(validateBonus)
  );
}

function validatePlayerRoundScore(data: unknown): data is PlayerRoundScore {
  if (!isObject(data)) return false;
  
  return (
    isNumber(data.declared) &&
    isNumber(data.captured) &&
    isNumber(data.score) &&
    isNumber(data.multiplier) &&
    isNumber(data.baseScore)
  );
}

function validateBonus(data: unknown): boolean {
  if (!isObject(data)) return false;
  
  return (
    isString(data.player) &&
    isString(data.type) &&
    isNumber(data.points) &&
    isString(data.description)
  );
}

// Type guard helpers
function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function isArray(value: unknown): value is unknown[] {
  return Array.isArray(value);
}

function isString(value: unknown): value is string {
  return typeof value === 'string';
}

function isNumber(value: unknown): value is number {
  return typeof value === 'number' && !isNaN(value);
}