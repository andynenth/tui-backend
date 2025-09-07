import { useState, useEffect, useCallback } from 'react';
import { PlayHistory, PlayHistoryError } from '../types/playHistory';
import { playHistoryService } from '../services/api/playHistoryService';

interface UsePlayHistoryResult {
  data: PlayHistory | null;
  loading: boolean;
  error: PlayHistoryError | null;
  retry: () => void;
}

export const usePlayHistory = (roomId: string): UsePlayHistoryResult => {
  const [data, setData] = useState<PlayHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<PlayHistoryError | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const history = await playHistoryService.getHistory(roomId);
      setData(history);
    } catch (err) {
      // Type guard to ensure we have a PlayHistoryError
      if (isPlayHistoryError(err)) {
        setError(err);
      } else {
        // Fallback for unexpected errors
        setError({
          message: err instanceof Error ? err.message : 'Unknown error occurred',
          code: 'UNKNOWN_ERROR',
          canRetry: true
        });
      }
    } finally {
      setLoading(false);
    }
  }, [roomId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    data,
    loading,
    error,
    retry: fetchData
  };
};

// Type guard for PlayHistoryError
function isPlayHistoryError(error: unknown): error is PlayHistoryError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'message' in error &&
    'code' in error &&
    'canRetry' in error
  );
}
