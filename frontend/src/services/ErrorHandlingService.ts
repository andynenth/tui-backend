/**
 * Centralized Error Handling Service
 *
 * Provides a unified interface for error handling, logging, user notification,
 * and retry logic across the frontend application.
 */

import {
  ErrorCode,
  ErrorSeverity,
  ErrorSeverityType,
  StandardError,
  StandardErrorData,
  getErrorMetadata,
  getUserFriendlyMessage,
  createStandardError,
} from '../shared/errorCodes';

interface RetryStrategy {
  maxAttempts: number;
  backoffMs: number[];
  jitter: boolean;
}

interface ErrorContext {
  component?: string;
  action?: string;
  userId?: string;
  sessionId?: string;
  gamePhase?: string;
  roomId?: string;
  timestamp?: number;
  url?: string;
  userAgent?: string;
}

interface ErrorHandlingConfig {
  enableConsoleLogging: boolean;
  enableRemoteLogging: boolean;
  enableUserNotifications: boolean;
  logLevel: ErrorSeverityType;
  maxRetryAttempts: number;
  baseRetryDelayMs: number;
}

type ErrorListener = (error: StandardError) => void;
type UserNotificationHandler = (
  message: string,
  severity: ErrorSeverityType
) => void;
type RemoteLogger = (error: StandardError, context: ErrorContext) => void;

export class ErrorHandlingService {
  private static instance: ErrorHandlingService | null = null;
  private config: ErrorHandlingConfig;
  private errorListeners: Set<ErrorListener> = new Set();
  private userNotificationHandler: UserNotificationHandler | null = null;
  private remoteLogger: RemoteLogger | null = null;
  private retryStrategies: Map<ErrorCode, RetryStrategy> = new Map();

  private constructor() {
    this.config = {
      enableConsoleLogging: process.env.NODE_ENV === 'development',
      enableRemoteLogging: process.env.NODE_ENV === 'production',
      enableUserNotifications: true,
      logLevel: ErrorSeverity.LOW,
      maxRetryAttempts: 3,
      baseRetryDelayMs: 1000,
    };

    this.initializeRetryStrategies();
  }

  public static getInstance(): ErrorHandlingService {
    if (!ErrorHandlingService.instance) {
      ErrorHandlingService.instance = new ErrorHandlingService();
    }
    return ErrorHandlingService.instance;
  }

  private initializeRetryStrategies(): void {
    // Network errors - aggressive retry with exponential backoff
    this.retryStrategies.set(ErrorCode.NETWORK_CONNECTION_LOST, {
      maxAttempts: 5,
      backoffMs: [1000, 2000, 4000, 8000, 16000],
      jitter: true,
    });

    this.retryStrategies.set(ErrorCode.NETWORK_TIMEOUT, {
      maxAttempts: 3,
      backoffMs: [500, 1000, 2000],
      jitter: true,
    });

    this.retryStrategies.set(ErrorCode.NETWORK_WEBSOCKET_ERROR, {
      maxAttempts: 3,
      backoffMs: [1000, 3000, 5000],
      jitter: true,
    });

    // System errors - moderate retry
    this.retryStrategies.set(ErrorCode.SYSTEM_SERVICE_UNAVAILABLE, {
      maxAttempts: 3,
      backoffMs: [2000, 4000, 8000],
      jitter: true,
    });

    this.retryStrategies.set(ErrorCode.SYSTEM_INTERNAL_ERROR, {
      maxAttempts: 2,
      backoffMs: [1000, 3000],
      jitter: true,
    });

    // Game errors - limited retry
    this.retryStrategies.set(ErrorCode.GAME_ROOM_FULL, {
      maxAttempts: 2,
      backoffMs: [2000, 5000],
      jitter: false,
    });
  }

  public configure(config: Partial<ErrorHandlingConfig>): void {
    this.config = { ...this.config, ...config };
  }

  public setUserNotificationHandler(handler: UserNotificationHandler): void {
    this.userNotificationHandler = handler;
  }

  public setRemoteLogger(logger: RemoteLogger): void {
    this.remoteLogger = logger;
  }

  public addErrorListener(listener: ErrorListener): void {
    this.errorListeners.add(listener);
  }

  public removeErrorListener(listener: ErrorListener): void {
    this.errorListeners.delete(listener);
  }

  /**
   * Report an error to the error handling system
   */
  public reportError(
    error: StandardError | Error | ErrorCode,
    context: Partial<ErrorContext> = {}
  ): StandardError {
    let standardError: StandardError;

    if (error instanceof StandardError) {
      standardError = error;
    } else if (error instanceof Error) {
      // Convert generic Error to StandardError
      standardError = createStandardError(
        ErrorCode.SYSTEM_INTERNAL_ERROR,
        error.message,
        { details: error.stack }
      );
    } else {
      // Error code provided
      const metadata = getErrorMetadata(error);
      standardError = createStandardError(error, metadata.userMessage);
    }

    const fullContext: ErrorContext = {
      timestamp: Date.now(),
      url: window.location.href,
      userAgent: navigator.userAgent,
      ...context,
    };

    // Merge context into error
    standardError.context = { ...standardError.context, ...fullContext };

    this.processError(standardError, fullContext);
    return standardError;
  }

  private processError(error: StandardError, context: ErrorContext): void {
    // Console logging
    if (this.config.enableConsoleLogging && this.shouldLog(error.severity)) {
      this.logToConsole(error, context);
    }

    // Remote logging
    if (this.config.enableRemoteLogging && this.remoteLogger) {
      try {
        this.remoteLogger(error, context);
      } catch (loggingError) {
        console.error('Failed to log error remotely:', loggingError);
      }
    }

    // User notification
    if (this.config.enableUserNotifications && this.shouldNotifyUser(error)) {
      this.notifyUser(error);
    }

    // Notify listeners
    this.errorListeners.forEach((listener) => {
      try {
        listener(error);
      } catch (listenerError) {
        console.error('Error listener failed:', listenerError);
      }
    });
  }

  private shouldLog(severity: ErrorSeverityType): boolean {
    const severityLevels = [
      ErrorSeverity.LOW,
      ErrorSeverity.MEDIUM,
      ErrorSeverity.HIGH,
      ErrorSeverity.CRITICAL,
    ];

    const errorLevel = severityLevels.indexOf(severity);
    const configLevel = severityLevels.indexOf(this.config.logLevel);

    return errorLevel >= configLevel;
  }

  private shouldNotifyUser(error: StandardError): boolean {
    // Don't notify for low severity validation errors
    if (
      error.severity === ErrorSeverity.LOW &&
      error.code >= 1000 &&
      error.code < 2000
    ) {
      return false;
    }

    return true;
  }

  private logToConsole(error: StandardError, context: ErrorContext): void {
    const logMethod = this.getConsoleMethod(error.severity);

    logMethod(
      `[${error.severity.toUpperCase()}] ${error.code}: ${error.message}`,
      {
        error: error.toDict(),
        context,
        details: error.details,
        stack: error.stack,
      }
    );
  }

  private getConsoleMethod(severity: ErrorSeverityType): typeof console.log {
    switch (severity) {
      case ErrorSeverity.LOW:
        return console.log;
      case ErrorSeverity.MEDIUM:
        return console.warn;
      case ErrorSeverity.HIGH:
      case ErrorSeverity.CRITICAL:
        return console.error;
      default:
        return console.log;
    }
  }

  private notifyUser(error: StandardError): void {
    if (this.userNotificationHandler) {
      const userMessage = getUserFriendlyMessage(error.code);
      this.userNotificationHandler(userMessage, error.severity);
    }
  }

  /**
   * Get retry strategy for an error code
   */
  public getRetryStrategy(error: StandardError): RetryStrategy | null {
    if (!error.retryable) {
      return null;
    }

    return (
      this.retryStrategies.get(error.code) || {
        maxAttempts: this.config.maxRetryAttempts,
        backoffMs: [this.config.baseRetryDelayMs],
        jitter: false,
      }
    );
  }

  /**
   * Execute a function with automatic retry logic
   */
  public async withRetry<T>(
    operation: () => Promise<T>,
    context: Partial<ErrorContext> = {}
  ): Promise<T> {
    let lastError: StandardError | null = null;
    let attempt = 0;

    while (attempt === 0) {
      // First attempt always runs
      try {
        return await operation();
      } catch (error) {
        lastError = this.reportError(error, context);

        const retryStrategy = this.getRetryStrategy(lastError);
        if (!retryStrategy || attempt >= retryStrategy.maxAttempts) {
          throw lastError;
        }

        const delay = this.calculateRetryDelay(retryStrategy, attempt);
        await this.sleep(delay);
        attempt++;
      }
    }

    throw lastError;
  }

  private calculateRetryDelay(
    strategy: RetryStrategy,
    attempt: number
  ): number {
    const baseDelay =
      strategy.backoffMs[Math.min(attempt, strategy.backoffMs.length - 1)];

    if (strategy.jitter) {
      // Add ±25% jitter to prevent thundering herd
      const jitterRange = baseDelay * 0.25;
      const jitter = (Math.random() - 0.5) * 2 * jitterRange;
      return Math.max(0, baseDelay + jitter);
    }

    return baseDelay;
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Create a standardized error from various input types
   */
  public createError(
    code: ErrorCode,
    message?: string,
    options: {
      details?: string;
      context?: Record<string, any>;
      requestId?: string;
    } = {}
  ): StandardError {
    const finalMessage = message || getUserFriendlyMessage(code);
    return createStandardError(code, finalMessage, options);
  }

  /**
   * Check if an error should be retried
   */
  public shouldRetry(error: StandardError): boolean {
    return error.retryable && this.retryStrategies.has(error.code);
  }

  /**
   * Get user-friendly error message
   */
  public getUserMessage(error: StandardError): string {
    return getUserFriendlyMessage(error.code);
  }

  /**
   * Handle WebSocket error messages
   */
  public handleWebSocketError(message: {
    event: string;
    data: StandardErrorData;
  }): StandardError {
    const error = StandardError.fromWebSocketMessage(message);
    this.processError(error, { component: 'WebSocket' });
    return error;
  }

  /**
   * Handle HTTP API errors
   */
  public handleApiError(
    response: Response,
    errorData?: any,
    context: Partial<ErrorContext> = {}
  ): StandardError {
    let code: ErrorCode;
    let message: string;

    // Map HTTP status codes to error codes
    switch (response.status) {
      case 400:
        code = ErrorCode.VALIDATION_INVALID_FORMAT;
        break;
      case 401:
        code = ErrorCode.AUTH_INVALID_CREDENTIALS;
        break;
      case 403:
        code = ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS;
        break;
      case 404:
        code = ErrorCode.GAME_ROOM_NOT_FOUND;
        break;
      case 408:
        code = ErrorCode.NETWORK_TIMEOUT;
        break;
      case 429:
        code = ErrorCode.NETWORK_MESSAGE_QUEUE_FULL;
        break;
      case 500:
        code = ErrorCode.SYSTEM_INTERNAL_ERROR;
        break;
      case 503:
        code = ErrorCode.SYSTEM_SERVICE_UNAVAILABLE;
        break;
      default:
        code = ErrorCode.SYSTEM_INTERNAL_ERROR;
    }

    message = errorData?.message || response.statusText || 'HTTP error';

    const error = createStandardError(code, message, {
      details: `HTTP ${response.status}: ${response.statusText}`,
      context: { ...context, httpStatus: response.status, url: response.url },
    });

    this.processError(error, context);
    return error;
  }
}
