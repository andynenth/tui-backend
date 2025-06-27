/**
 * 🔷 **Service Type Definitions**
 * 
 * TypeScript interfaces for NetworkService and GameService
 * Provides type safety for complex game state management
 */

// ===== NETWORK SERVICE TYPES =====

export interface NetworkConfig {
  baseUrl?: string;
  heartbeatInterval?: number;
  maxReconnectAttempts?: number;
  reconnectBackoff?: number[];
  messageQueueLimit?: number;
  connectionTimeout?: number;
}

export interface ConnectionData {
  websocket: WebSocket;
  roomId: string;
  url: string;
  status: 'connected' | 'disconnected' | 'connecting' | 'reconnecting';
  connectedAt: number;
  messagesSent: number;
  messagesReceived: number;
  lastActivity: number;
  latency: number | null;
}

export interface ReconnectState {
  attempts: number;
  isReconnecting: boolean;
  abortController: AbortController | null;
}

export interface NetworkMessage {
  event: string;
  data: Record<string, any>;
  sequence: number;
  timestamp: number;
  id: string;
}

export interface ConnectionStatus {
  roomId: string;
  status: string;
  connected: boolean;
  connectedAt?: number;
  uptime?: number;
  messagesSent?: number;
  messagesReceived?: number;
  lastActivity?: number;
  latency?: number | null;
  queueSize: number;
  reconnecting: boolean;
  reconnectAttempts?: number;
}

export interface NetworkStatus {
  isDestroyed: boolean;
  activeConnections: number;
  totalQueuedMessages: number;
  rooms: Record<string, ConnectionStatus>;
}

// ===== GAME SERVICE TYPES =====

export interface GamePiece {
  type: string;
  color: 'red' | 'black';
  value: number;
  id?: string;
}

export interface Player {
  name: string;
  score: number;
  is_bot: boolean;
  pile_count?: number;
  zero_declares_in_a_row?: number;
}

export interface TurnPlay {
  player: string;
  pieces: GamePiece[];
  indices?: number[];
  timestamp?: number;
}

export interface GameState {
  // Connection state
  isConnected: boolean;
  roomId: string | null;
  playerName: string | null;
  
  // Game state
  phase: 'waiting' | 'preparation' | 'declaration' | 'turn' | 'turn_results' | 'scoring';
  currentRound: number;
  players: Player[];
  roundStarter: string | null;
  
  // Preparation phase state
  weakHands: string[];
  currentWeakPlayer: string | null;
  redealRequests: Record<string, boolean>;
  redealMultiplier: number;
  
  // Declaration phase state
  myHand: GamePiece[];
  declarations: Record<string, number>;
  declarationOrder: string[];
  currentDeclarer: string | null;
  declarationTotal: number;
  
  // Turn phase state
  currentTurnStarter: string | null;
  turnOrder: string[];
  currentTurnPlays: TurnPlay[];
  requiredPieceCount: number | null;
  currentTurnNumber: number;
  
  // Scoring phase state
  roundScores: Record<string, number>;
  totalScores: Record<string, number>;
  winners: string[];
  
  // UI state
  isMyTurn: boolean;
  allowedActions: string[];
  validOptions: number[] | number[][];
  
  // Calculated UI state (computed from backend data)
  // Preparation phase
  isMyDecision?: boolean;
  isMyHandWeak?: boolean;
  handValue?: number;
  highestCardValue?: number;
  
  // Declaration phase
  currentTotal?: number;
  declarationProgress?: { declared: number; total: number };
  isLastPlayer?: boolean;
  estimatedPiles?: number;
  handStrength?: number;
  
  // Turn phase
  canPlayAnyCount?: boolean;
  selectedPlayValue?: number;
  
  // Scoring phase
  playersWithScores?: any[];
  
  // Turn results phase
  turnWinner?: string | null;
  winningPlay?: {
    pieces: string[];
    value: number;
    type: string;
    pilesWon: number;
  } | null;
  playerPiles?: Record<string, number>;
  turnNumber?: number;
  nextStarter?: string | null;
  allHandsEmpty?: boolean;
  willContinue?: boolean;
  
  // Meta state
  lastEventSequence: number;
  error: string | null;
  gameOver: boolean;
}

export interface PhaseData {
  phase?: string;
  round?: number;
  players?: Player[];
  my_hand?: GamePiece[];
  round_starter?: string;
  redeal_multiplier?: number;
  
  // Preparation phase
  weak_hands?: string[];
  current_weak_player?: string;
  
  // Declaration phase
  declaration_order?: string[];
  current_declarer?: string;
  declarations?: Record<string, number>;
  
  // Turn phase
  turn_order?: string[];
  current_turn_starter?: string;
  current_turn_plays?: TurnPlay[];
  current_turn_number?: number;
  
  // Scoring phase
  round_scores?: Record<string, number>;
  total_scores?: Record<string, number>;
  final_scores?: Record<string, number>;
  winners?: string[];
}

export interface GameEvent {
  type: string;
  data: any;
  roomId?: string;
  timestamp?: number;
}

export interface StateChangeEvent {
  oldState: GameState;
  newState: GameState;
  reason: string;
  sequence: number;
  timestamp: number;
}

export type GameEventType = 
  | 'phase_change'
  | 'weak_hands_found'
  | 'redeal_decision_needed'
  | 'redeal_executed'
  | 'declare'
  | 'play'
  | 'turn_complete'
  | 'turn_resolved'
  | 'score_update'
  | 'round_complete'
  | 'game_ended';

export type GameAction = 
  | 'acceptRedeal'
  | 'declineRedeal'
  | 'makeDeclaration'
  | 'playPieces'
  | 'startNextRound';

// ===== EVENT TYPES =====

export interface NetworkEventDetail {
  roomId: string;
  data?: any;
  message?: NetworkMessage;
  error?: string;
  timestamp: number;
}

export interface ConnectionEventDetail {
  roomId: string;
  url?: string;
  intentional?: boolean;
  code?: number;
  reason?: string;
  wasClean?: boolean;
  timestamp: number;
}

export interface ReconnectionEventDetail {
  roomId: string;
  attempt?: number;
  attempts?: number;
  error?: string;
  reason?: string;
  timestamp: number;
}

// ===== SERVICE HEALTH TYPES =====

export interface ServiceHealth {
  network: {
    healthy: boolean;
    connections: number;
    queuedMessages: number;
  };
  game: {
    healthy: boolean;
    connected: boolean;
    phase: string;
    roomId: string | null;
  };
}

// ===== UTILITY TYPES =====

export type StateListener = (state: GameState) => void;
export type CleanupFunction = () => void;

// Type guards
export function isGamePiece(obj: any): obj is GamePiece {
  return obj && typeof obj.type === 'string' && typeof obj.value === 'number';
}

export function isPlayer(obj: any): obj is Player {
  return obj && typeof obj.name === 'string' && typeof obj.score === 'number';
}

export function isTurnPlay(obj: any): obj is TurnPlay {
  return obj && typeof obj.player === 'string' && Array.isArray(obj.pieces);
}

// ===== RECOVERY SERVICE TYPES =====

export interface RecoveryOptions {
  snapshotInterval?: number;
  maxEventBuffer?: number;
  recoveryTimeout?: number;
  enablePersistence?: boolean;
  maxRetries?: number;
  gapDetectionThreshold?: number;
}

export interface EventSequence {
  sequence: number;
  type: string;
  data: any;
  timestamp: number;
  id: string;
}

export interface RecoverySnapshot {
  sequence: number;
  timestamp: number;
  gameState: GameState;
  roomId: string;
}

export interface SequenceGap {
  start: number;
  end: number;
  detected: number;
}

export interface RecoveryState {
  roomId: string;
  lastSequence: number;
  expectedSequence: number;
  snapshots: RecoverySnapshot[];
  isRecovering: boolean;
  recoveryAttempts: number;
  gapsDetected: SequenceGap[];
  lastSnapshotSequence: number;
  recoveryStartTime: number | null;
}

export interface EventBuffer {
  events: EventSequence[];
  maxSize: number;
  nextExpectedSequence: number;
}

export interface RecoveryStatus {
  roomId: string;
  initialized: boolean;
  isRecovering: boolean;
  lastSequence: number;
  expectedSequence: number;
  gapsDetected: number;
  snapshotCount: number;
  eventBufferSize: number;
  recoveryAttempts: number;
  lastSnapshotSequence?: number;
  recoveryStartTime?: number | null;
}

export interface RecoveryEventDetail {
  roomId: string;
  attempt?: number;
  error?: string;
  gap?: SequenceGap;
  timestamp: number;
}

// ===== SERVICE INTEGRATION TYPES =====

export interface IntegrationConfig {
  healthCheckInterval?: number;
  errorRetention?: number;
  autoRecovery?: boolean;
  recoveryTimeout?: number;
  maxRecoveryAttempts?: number;
  errorThreshold?: number;
  errorWindowMs?: number;
  enableMetrics?: boolean;
}

export type ErrorSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface ServiceError {
  type: string;
  severity: ErrorSeverity;
  message: string;
  source: string;
  timestamp: number;
  context?: any;
}

export interface RecoveryStrategy {
  name: string;
  execute: (gameState: GameState) => Promise<void>;
}

export interface ErrorRecoveryResult {
  success: boolean;
  appliedStrategies: string[];
  timestamp: number;
  errorType: string;
  error?: string;
}

export interface ServiceMetrics {
  totalErrors: number;
  recoveryAttempts: number;
  successfulRecoveries: number;
  uptime: number;
  lastHealthCheck: number;
}

export interface NetworkHealthInfo {
  healthy: boolean;
  connections: number;
  queuedMessages: number;
  status: string;
}

export interface GameHealthInfo {
  healthy: boolean;
  connected: boolean;
  phase: string;
  roomId: string | null;
  playersCount: number;
  status: string;
}

export interface RecoveryHealthInfo {
  healthy: boolean;
  initialized: boolean;
  isRecovering: boolean;
  eventBufferSize: number;
  gapsDetected: number;
  status: string;
}

export interface IntegrationStatus {
  initialized: boolean;
  destroyed: boolean;
  errorCount: number;
  lastError: ServiceError | null;
  healthCheckEnabled: boolean;
  autoRecoveryEnabled: boolean;
}

export interface ServiceHealthStatus {
  overall: {
    healthy: boolean;
    issues: string[];
  };
  network: NetworkHealthInfo;
  game: GameHealthInfo;
  recovery: RecoveryHealthInfo | null;
  integration: IntegrationStatus;
  metrics: ServiceMetrics;
  errors: ServiceError[];
}

export interface IntegrationEventDetail {
  timestamp: number;
  roomId?: string;
  playerName?: string;
  error?: ServiceError;
  healthStatus?: ServiceHealthStatus;
  recoveryResult?: ErrorRecoveryResult;
  errorCount?: number;
  windowMs?: number;
}