import { PlayHistory, PlayHistoryError } from '../../types/playHistory';
import { deepFreeze } from '../../utils/immutability';
import { validatePlayHistory } from './validation';
import { transformPlayHistoryResponse } from './transformers';

export interface PlayHistoryService {
  getHistory(roomId: string): Promise<PlayHistory>;
}

class PlayHistoryServiceImpl implements PlayHistoryService {
  private baseUrl = '/api/rooms';

  async getHistory(roomId: string): Promise<PlayHistory> {
    try {
      const response = await fetch(`${this.baseUrl}/${roomId}/play-history`);

      if (!response.ok) {
        if (response.status === 404) {
          throw this.createError('Game history not found', 'NOT_FOUND', true);
        }
        throw this.createError(
          `HTTP error! status: ${response.status}`,
          'HTTP_ERROR',
          response.status >= 500
        );
      }

      const rawData = await response.json();

      // Transform the API response to match our expected format
      const transformedData = transformPlayHistoryResponse(rawData);

      if (!validatePlayHistory(transformedData)) {
        throw this.createError('Invalid game history data', 'INVALID_DATA', false);
      }

      // Deep freeze the data to ensure immutability
      return deepFreeze(transformedData);
    } catch (error) {
      // Re-throw if it's already a PlayHistoryError
      if (this.isPlayHistoryError(error)) {
        throw error;
      }

      // Handle network errors
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw this.createError('Network error', 'NETWORK_ERROR', true);
      }

      // Handle JSON parse errors
      if (error instanceof SyntaxError) {
        throw this.createError('Invalid response format', 'PARSE_ERROR', false);
      }

      // Generic error
      throw this.createError(
        error instanceof Error ? error.message : 'Unknown error',
        'UNKNOWN_ERROR',
        true
      );
    }
  }

  private createError(message: string, code: string, canRetry: boolean): PlayHistoryError {
    return {
      message,
      code,
      canRetry
    };
  }

  private isPlayHistoryError(error: unknown): error is PlayHistoryError {
    return (
      typeof error === 'object' &&
      error !== null &&
      'message' in error &&
      'code' in error &&
      'canRetry' in error
    );
  }
}

// Export singleton instance
export const playHistoryService = new PlayHistoryServiceImpl();
