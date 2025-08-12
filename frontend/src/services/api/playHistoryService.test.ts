import { playHistoryService } from './playHistoryService';
import * as validationModule from './validation';
import * as immutabilityModule from '../../utils/immutability';
import { mockPlayHistory } from '../../mocks/playHistoryMock';

// Mock fetch globally
global.fetch = jest.fn();

// Mock validation and immutability modules
jest.mock('./validation');
jest.mock('../../utils/immutability');

describe('PlayHistoryService', () => {
  const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;
  const mockValidatePlayHistory = validationModule.validatePlayHistory as jest.MockedFunction<typeof validationModule.validatePlayHistory>;
  const mockDeepFreeze = immutabilityModule.deepFreeze as jest.MockedFunction<typeof immutabilityModule.deepFreeze>;
  
  beforeEach(() => {
    jest.clearAllMocks();
    // Default mock implementations
    mockValidatePlayHistory.mockReturnValue(true);
    mockDeepFreeze.mockImplementation((obj) => obj);
  });
  
  afterEach(() => {
    jest.resetAllMocks();
  });
  
  it('should fetch play history successfully', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockPlayHistory
    } as Response);
    
    const result = await playHistoryService.getHistory('23BEBA');
    
    expect(mockFetch).toHaveBeenCalledWith('/api/rooms/23BEBA/play-history');
    expect(mockValidatePlayHistory).toHaveBeenCalledWith(mockPlayHistory);
    expect(mockDeepFreeze).toHaveBeenCalledWith(mockPlayHistory);
    expect(result).toEqual(mockPlayHistory);
  });
  
  it('should handle 404 - room not found', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404
    } as Response);
    
    await expect(playHistoryService.getHistory('invalid'))
      .rejects.toEqual({
        message: 'Game history not found',
        code: 'NOT_FOUND',
        canRetry: true
      });
  });
  
  it('should handle 500 server errors', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500
    } as Response);
    
    await expect(playHistoryService.getHistory('23BEBA'))
      .rejects.toEqual({
        message: 'HTTP error! status: 500',
        code: 'HTTP_ERROR',
        canRetry: true
      });
  });
  
  it('should handle 400 client errors', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 400
    } as Response);
    
    await expect(playHistoryService.getHistory('23BEBA'))
      .rejects.toEqual({
        message: 'HTTP error! status: 400',
        code: 'HTTP_ERROR',
        canRetry: false
      });
  });
  
  it('should handle network errors', async () => {
    mockFetch.mockRejectedValueOnce(new TypeError('Failed to fetch'));
    
    await expect(playHistoryService.getHistory('23BEBA'))
      .rejects.toEqual({
        message: 'Network error',
        code: 'NETWORK_ERROR',
        canRetry: true
      });
  });
  
  it('should handle invalid JSON response', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => {
        throw new SyntaxError('Unexpected token < in JSON');
      }
    } as Response);
    
    await expect(playHistoryService.getHistory('23BEBA'))
      .rejects.toEqual({
        message: 'Invalid response format',
        code: 'PARSE_ERROR',
        canRetry: false
      });
  });
  
  it('should validate response structure', async () => {
    const invalidData = { invalid: 'data' };
    
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => invalidData
    } as Response);
    
    mockValidatePlayHistory.mockReturnValueOnce(false);
    
    await expect(playHistoryService.getHistory('23BEBA'))
      .rejects.toEqual({
        message: 'Invalid game history data',
        code: 'INVALID_DATA',
        canRetry: false
      });
    
    expect(mockValidatePlayHistory).toHaveBeenCalledWith(invalidData);
  });
  
  it('should deep freeze the returned data', async () => {
    const frozenData = Object.freeze({ ...mockPlayHistory });
    
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockPlayHistory
    } as Response);
    
    mockDeepFreeze.mockReturnValueOnce(frozenData);
    
    const result = await playHistoryService.getHistory('23BEBA');
    
    expect(mockDeepFreeze).toHaveBeenCalledWith(mockPlayHistory);
    expect(result).toBe(frozenData);
    expect(Object.isFrozen(result)).toBe(true);
  });
  
  it('should re-throw PlayHistoryError without modification', async () => {
    const playHistoryError = {
      message: 'Custom error',
      code: 'CUSTOM_ERROR',
      canRetry: false
    };
    
    mockFetch.mockRejectedValueOnce(playHistoryError);
    
    await expect(playHistoryService.getHistory('23BEBA'))
      .rejects.toEqual(playHistoryError);
  });
  
  it('should handle generic errors', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Generic error'));
    
    await expect(playHistoryService.getHistory('23BEBA'))
      .rejects.toEqual({
        message: 'Generic error',
        code: 'UNKNOWN_ERROR',
        canRetry: true
      });
  });
  
  it('should handle non-Error objects', async () => {
    mockFetch.mockRejectedValueOnce('String error');
    
    await expect(playHistoryService.getHistory('23BEBA'))
      .rejects.toEqual({
        message: 'Unknown error',
        code: 'UNKNOWN_ERROR',
        canRetry: true
      });
  });
});