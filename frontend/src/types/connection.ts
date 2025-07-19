// frontend/src/types/connection.ts

export enum ConnectionStatus {
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  RECONNECTING = 'reconnecting'
}

export interface PlayerStatus {
  playerName: string;
  connectionStatus: ConnectionStatus;
  isBot: boolean;
  lastSeen?: Date;
  canReconnect: boolean;
}

export interface DisconnectEvent {
  playerName: string;
  aiActivated: boolean;
  phase: string;
  actionsTaken: string[];
  canReconnect: boolean;
  isBot: boolean;
  timestamp: string;
}

export interface ReconnectEvent {
  playerName: string;
  botDeactivated: boolean;
  phase: string;
  timestamp: string;
}

export interface ConnectionStateUpdate {
  roomId: string;
  players: Record<string, PlayerStatus>;
  timestamp: string;
}

export interface FullStateSync {
  phase: string;
  allowedActions: string[];
  phaseData: any;
  players: Record<string, any>;
  round: number;
  reconnectedPlayer: string;
  timestamp: string;
}