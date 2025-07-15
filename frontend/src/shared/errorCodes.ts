/**
 * Standardized Error Classification System
 * 
 * This module defines a unified error code system that is shared between
 * the frontend and backend to ensure consistent error handling and user experience.
 */

export enum ErrorCode {
  // Validation Errors (1000-1999)
  VALIDATION_REQUIRED_FIELD = 1001,
  VALIDATION_INVALID_FORMAT = 1002,
  VALIDATION_OUT_OF_RANGE = 1003,
  VALIDATION_INVALID_TYPE = 1004,
  VALIDATION_DUPLICATE_VALUE = 1005,
  VALIDATION_CONSTRAINT_VIOLATION = 1006,
  
  // Authentication/Authorization (2000-2999)
  AUTH_INVALID_CREDENTIALS = 2001,
  AUTH_SESSION_EXPIRED = 2002,
  AUTH_INSUFFICIENT_PERMISSIONS = 2003,
  AUTH_ACCOUNT_LOCKED = 2004,
  
  // Game Logic Errors (3000-3999)
  GAME_INVALID_ACTION = 3001,
  GAME_NOT_YOUR_TURN = 3002,
  GAME_INVALID_PIECES = 3003,
  GAME_INVALID_PHASE = 3004,
  GAME_ALREADY_DECLARED = 3005,
  GAME_ROOM_FULL = 3006,
  GAME_ROOM_NOT_FOUND = 3007,
  GAME_PLAYER_NOT_IN_ROOM = 3008,
  GAME_INSUFFICIENT_PIECES = 3009,
  GAME_DECLARATION_CONSTRAINT = 3010,
  GAME_WEAK_HAND_INVALID = 3011,
  
  // Network/Connection (4000-4999)
  NETWORK_CONNECTION_LOST = 4001,
  NETWORK_TIMEOUT = 4002,
  NETWORK_WEBSOCKET_ERROR = 4003,
  NETWORK_MESSAGE_QUEUE_FULL = 4004,
  NETWORK_INVALID_MESSAGE = 4005,
  NETWORK_RECONNECTION_FAILED = 4006,
  
  // System Errors (5000-5999)
  SYSTEM_INTERNAL_ERROR = 5001,
  SYSTEM_SERVICE_UNAVAILABLE = 5002,
  SYSTEM_DATABASE_ERROR = 5003,
  SYSTEM_MEMORY_ERROR = 5004,
  SYSTEM_CONFIGURATION_ERROR = 5005
}

export const ErrorSeverity = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  CRITICAL: 'critical'
} as const;

export type ErrorSeverityType = typeof ErrorSeverity[keyof typeof ErrorSeverity];

export interface StandardErrorData {
  code: ErrorCode;
  message: string;
  details?: string;
  context?: Record<string, any>;
  retryable: boolean;
  severity: ErrorSeverityType;
  timestamp: number;
  requestId?: string;
}

export class StandardError extends Error {
  public readonly code: ErrorCode;
  public readonly details?: string;
  public readonly context: Record<string, any>;
  public readonly retryable: boolean;
  public readonly severity: ErrorSeverityType;
  public readonly timestamp: number;
  public readonly requestId?: string;

  constructor(data: Partial<StandardErrorData> & { code: ErrorCode; message: string }) {
    super(data.message);
    this.name = 'StandardError';
    
    const metadata = getErrorMetadata(data.code);
    
    this.code = data.code;
    this.details = data.details;
    this.context = data.context || {};
    this.retryable = data.retryable ?? metadata.retryable;
    this.severity = data.severity ?? metadata.severity;
    this.timestamp = data.timestamp ?? Date.now();
    this.requestId = data.requestId;
  }

  toDict(): StandardErrorData {
    return {
      code: this.code,
      message: this.message,
      details: this.details,
      context: this.context,
      retryable: this.retryable,
      severity: this.severity,
      timestamp: this.timestamp,
      requestId: this.requestId
    };
  }

  toWebSocketMessage(): { event: string; data: StandardErrorData } {
    return {
      event: 'error',
      data: this.toDict()
    };
  }

  static fromDict(data: StandardErrorData): StandardError {
    return new StandardError(data);
  }

  static fromWebSocketMessage(message: { event: string; data: StandardErrorData }): StandardError {
    if (message.event !== 'error') {
      throw new Error('Invalid WebSocket error message format');
    }
    return StandardError.fromDict(message.data);
  }
}

// Error code metadata for determining behavior
interface ErrorMetadata {
  retryable: boolean;
  severity: ErrorSeverityType;
  userMessage: string;
}

const ERROR_METADATA: Record<ErrorCode, ErrorMetadata> = {
  // Validation errors - usually not retryable, low to medium severity
  [ErrorCode.VALIDATION_REQUIRED_FIELD]: {
    retryable: false,
    severity: ErrorSeverity.LOW,
    userMessage: 'Required field is missing'
  },
  [ErrorCode.VALIDATION_INVALID_FORMAT]: {
    retryable: false,
    severity: ErrorSeverity.LOW,
    userMessage: 'Invalid format provided'
  },
  [ErrorCode.VALIDATION_OUT_OF_RANGE]: {
    retryable: false,
    severity: ErrorSeverity.LOW,
    userMessage: 'Value is out of acceptable range'
  },
  [ErrorCode.VALIDATION_INVALID_TYPE]: {
    retryable: false,
    severity: ErrorSeverity.LOW,
    userMessage: 'Invalid data type provided'
  },
  [ErrorCode.VALIDATION_DUPLICATE_VALUE]: {
    retryable: false,
    severity: ErrorSeverity.LOW,
    userMessage: 'Duplicate value not allowed'
  },
  [ErrorCode.VALIDATION_CONSTRAINT_VIOLATION]: {
    retryable: false,
    severity: ErrorSeverity.MEDIUM,
    userMessage: 'Data constraint violation'
  },

  // Authentication/Authorization errors
  [ErrorCode.AUTH_INVALID_CREDENTIALS]: {
    retryable: false,
    severity: ErrorSeverity.MEDIUM,
    userMessage: 'Invalid credentials provided'
  },
  [ErrorCode.AUTH_SESSION_EXPIRED]: {
    retryable: false,
    severity: ErrorSeverity.MEDIUM,
    userMessage: 'Session has expired, please log in again'
  },
  [ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS]: {
    retryable: false,
    severity: ErrorSeverity.MEDIUM,
    userMessage: 'Insufficient permissions for this action'
  },
  [ErrorCode.AUTH_ACCOUNT_LOCKED]: {
    retryable: false,
    severity: ErrorSeverity.HIGH,
    userMessage: 'Account is temporarily locked'
  },

  // Game logic errors - context-dependent retryability
  [ErrorCode.GAME_INVALID_ACTION]: {
    retryable: false,
    severity: ErrorSeverity.MEDIUM,
    userMessage: 'This action is not allowed right now'
  },
  [ErrorCode.GAME_NOT_YOUR_TURN]: {
    retryable: false,
    severity: ErrorSeverity.LOW,
    userMessage: "It's not your turn yet"
  },
  [ErrorCode.GAME_INVALID_PIECES]: {
    retryable: false,
    severity: ErrorSeverity.LOW,
    userMessage: 'Invalid pieces selected'
  },
  [ErrorCode.GAME_INVALID_PHASE]: {
    retryable: false,
    severity: ErrorSeverity.MEDIUM,
    userMessage: 'Action not available in current game phase'
  },
  [ErrorCode.GAME_ALREADY_DECLARED]: {
    retryable: false,
    severity: ErrorSeverity.LOW,
    userMessage: 'You have already made your declaration'
  },
  [ErrorCode.GAME_ROOM_FULL]: {
    retryable: true,
    severity: ErrorSeverity.MEDIUM,
    userMessage: 'Game room is full, please try again later'
  },
  [ErrorCode.GAME_ROOM_NOT_FOUND]: {
    retryable: false,
    severity: ErrorSeverity.MEDIUM,
    userMessage: 'Game room not found'
  },
  [ErrorCode.GAME_PLAYER_NOT_IN_ROOM]: {
    retryable: false,
    severity: ErrorSeverity.MEDIUM,
    userMessage: 'Player is not in the game room'
  },
  [ErrorCode.GAME_INSUFFICIENT_PIECES]: {
    retryable: false,
    severity: ErrorSeverity.LOW,
    userMessage: 'Not enough pieces for this action'
  },
  [ErrorCode.GAME_DECLARATION_CONSTRAINT]: {
    retryable: false,
    severity: ErrorSeverity.LOW,
    userMessage: 'Declaration violates game constraints'
  },
  [ErrorCode.GAME_WEAK_HAND_INVALID]: {
    retryable: false,
    severity: ErrorSeverity.LOW,
    userMessage: 'Weak hand criteria not met'
  },

  // Network errors - usually retryable, higher severity
  [ErrorCode.NETWORK_CONNECTION_LOST]: {
    retryable: true,
    severity: ErrorSeverity.HIGH,
    userMessage: 'Connection lost, attempting to reconnect...'
  },
  [ErrorCode.NETWORK_TIMEOUT]: {
    retryable: true,
    severity: ErrorSeverity.MEDIUM,
    userMessage: 'Request timed out, please try again'
  },
  [ErrorCode.NETWORK_WEBSOCKET_ERROR]: {
    retryable: true,
    severity: ErrorSeverity.HIGH,
    userMessage: 'WebSocket connection error'
  },
  [ErrorCode.NETWORK_MESSAGE_QUEUE_FULL]: {
    retryable: true,
    severity: ErrorSeverity.MEDIUM,
    userMessage: 'Message queue is full, please try again'
  },
  [ErrorCode.NETWORK_INVALID_MESSAGE]: {
    retryable: false,
    severity: ErrorSeverity.MEDIUM,
    userMessage: 'Invalid network message format'
  },
  [ErrorCode.NETWORK_RECONNECTION_FAILED]: {
    retryable: true,
    severity: ErrorSeverity.HIGH,
    userMessage: 'Failed to reconnect, please refresh the page'
  },

  // System errors - retryable for transient issues, critical severity
  [ErrorCode.SYSTEM_INTERNAL_ERROR]: {
    retryable: true,
    severity: ErrorSeverity.CRITICAL,
    userMessage: 'An unexpected error occurred, please try again'
  },
  [ErrorCode.SYSTEM_SERVICE_UNAVAILABLE]: {
    retryable: true,
    severity: ErrorSeverity.HIGH,
    userMessage: 'Service is temporarily unavailable'
  },
  [ErrorCode.SYSTEM_DATABASE_ERROR]: {
    retryable: true,
    severity: ErrorSeverity.CRITICAL,
    userMessage: 'Database error, please try again later'
  },
  [ErrorCode.SYSTEM_MEMORY_ERROR]: {
    retryable: true,
    severity: ErrorSeverity.CRITICAL,
    userMessage: 'System memory error'
  },
  [ErrorCode.SYSTEM_CONFIGURATION_ERROR]: {
    retryable: false,
    severity: ErrorSeverity.CRITICAL,
    userMessage: 'System configuration error'
  }
};

export function getErrorMetadata(code: ErrorCode): ErrorMetadata {
  return ERROR_METADATA[code] || {
    retryable: false,
    severity: ErrorSeverity.MEDIUM,
    userMessage: 'An error occurred'
  };
}

export function createStandardError(
  code: ErrorCode,
  message: string,
  options: {
    details?: string;
    context?: Record<string, any>;
    requestId?: string;
  } = {}
): StandardError {
  return new StandardError({
    code,
    message,
    details: options.details,
    context: options.context,
    requestId: options.requestId
  });
}

export function getUserFriendlyMessage(code: ErrorCode): string {
  return getErrorMetadata(code).userMessage;
}