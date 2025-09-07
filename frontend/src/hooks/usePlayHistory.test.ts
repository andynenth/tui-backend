import { renderHook, act, waitFor } from '@testing-library/react';
import { usePlayHistory } from './usePlayHistory';
import * as playHistoryServiceModule from '../services/api/playHistoryService';
import { mockPlayHistory } from '../mocks/playHistoryMock';

// Mock the service
jest.mock('../services/api/playHistoryService');

describe('usePlayHistory', () => {
  const mockPlayHistoryService = playHistoryServiceModule.playHistoryService as jest.Mocked<typeof playHistoryServiceModule.playHistoryService>;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch data on mount', async () => {
    mockPlayHistoryService.getHistory.mockResolvedValueOnce(mockPlayHistory);

    const { result } = renderHook(() => usePlayHistory('23BEBA'));

    // Initial state
    expect(result.current).toEqual({
      data: null,
      loading: true,
      error: null,
      retry: expect.any(Function)
    });

    // After fetch
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
      expect(result.current.data).toEqual(mockPlayHistory);
      expect(result.current.error).toBe(null);
    });

    expect(mockPlayHistoryService.getHistory).toHaveBeenCalledWith('23BEBA');
    expect(mockPlayHistoryService.getHistory).toHaveBeenCalledTimes(1);
  });

  it('should handle errors with retry capability', async () => {
    const mockError = {
      message: 'Network error',
      code: 'NETWORK_ERROR',
      canRetry: true
    };

    mockPlayHistoryService.getHistory.mockRejectedValueOnce(mockError);

    const { result } = renderHook(() => usePlayHistory('23BEBA'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toEqual(mockError);
      expect(result.current.data).toBe(null);
    });

    // Test retry
    mockPlayHistoryService.getHistory.mockResolvedValueOnce(mockPlayHistory);

    act(() => {
      result.current.retry();
    });

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
      expect(result.current.data).toEqual(mockPlayHistory);
      expect(result.current.error).toBe(null);
    });

    expect(mockPlayHistoryService.getHistory).toHaveBeenCalledTimes(2);
  });

  it('should ensure data immutability', async () => {
    const frozenData = Object.freeze(mockPlayHistory);
    mockPlayHistoryService.getHistory.mockResolvedValueOnce(frozenData);

    const { result } = renderHook(() => usePlayHistory('23BEBA'));

    await waitFor(() => {
      expect(result.current.data).toBeTruthy();
    });

    // Attempt to mutate should fail if data is properly frozen
    expect(() => {
      if (result.current.data) {
        // @ts-expect-error - Testing immutability
        result.current.data.rounds[0].winner = 'hacked';
      }
    }).toThrow();
  });

  it('should handle non-PlayHistoryError errors', async () => {
    const genericError = new Error('Something went wrong');
    mockPlayHistoryService.getHistory.mockRejectedValueOnce(genericError);

    const { result } = renderHook(() => usePlayHistory('23BEBA'));

    await waitFor(() => {
      expect(result.current.error).toEqual({
        message: 'Something went wrong',
        code: 'UNKNOWN_ERROR',
        canRetry: true
      });
    });
  });

  it('should refetch when roomId changes', async () => {
    mockPlayHistoryService.getHistory.mockResolvedValueOnce(mockPlayHistory);

    const { result, rerender } = renderHook(
      ({ roomId }) => usePlayHistory(roomId),
      { initialProps: { roomId: '23BEBA' } }
    );

    await waitFor(() => {
      expect(result.current.data).toEqual(mockPlayHistory);
    });

    expect(mockPlayHistoryService.getHistory).toHaveBeenCalledWith('23BEBA');

    // Change roomId
    mockPlayHistoryService.getHistory.mockResolvedValueOnce({
      ...mockPlayHistory,
      roomId: 'NEW123'
    });

    rerender({ roomId: 'NEW123' });

    await waitFor(() => {
      expect(result.current.data?.roomId).toBe('NEW123');
    });

    expect(mockPlayHistoryService.getHistory).toHaveBeenCalledWith('NEW123');
    expect(mockPlayHistoryService.getHistory).toHaveBeenCalledTimes(2);
  });

  it('should handle unknown error types', async () => {
    // Test with a non-Error object
    mockPlayHistoryService.getHistory.mockRejectedValueOnce('String error');

    const { result } = renderHook(() => usePlayHistory('23BEBA'));

    await waitFor(() => {
      expect(result.current.error).toEqual({
        message: 'Unknown error occurred',
        code: 'UNKNOWN_ERROR',
        canRetry: true
      });
    });
  });
});
