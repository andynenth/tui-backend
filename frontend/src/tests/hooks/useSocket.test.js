import React from 'react';
import { renderHook, act } from '@testing-library/react';
import useSocket from '../../hooks/useSocket.js';

// Mock SocketManager
const mockSocketManager = {
  connect: jest.fn(),
  disconnect: jest.fn(),
  send: jest.fn(),
  on: jest.fn(),
  off: jest.fn(),
  isConnected: jest.fn(() => false)
};

jest.mock('../../network/SocketManager.js', () => ({
  default: jest.fn(() => mockSocketManager)
}));

describe('useSocket Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('initializes with disconnected status', () => {
    const { result } = renderHook(() => useSocket());
    
    expect(result.current.connectionStatus).toBe('disconnected');
    expect(result.current.isConnected).toBe(false);
  });

  test('connects to socket', () => {
    const { result } = renderHook(() => useSocket());
    
    act(() => {
      result.current.connect();
    });

    expect(mockSocketManager.connect).toHaveBeenCalled();
  });

  test('disconnects from socket', () => {
    const { result } = renderHook(() => useSocket());
    
    act(() => {
      result.current.disconnect();
    });

    expect(mockSocketManager.disconnect).toHaveBeenCalled();
  });

  test('sends message through socket', () => {
    const { result } = renderHook(() => useSocket());
    const testMessage = { type: 'test', data: 'hello' };
    
    act(() => {
      result.current.send(testMessage);
    });

    expect(mockSocketManager.send).toHaveBeenCalledWith(testMessage);
  });

  test('registers event listeners', () => {
    const { result } = renderHook(() => useSocket());
    const handler = jest.fn();
    
    act(() => {
      result.current.on('test-event', handler);
    });

    expect(mockSocketManager.on).toHaveBeenCalledWith('test-event', handler);
  });

  test('unregisters event listeners', () => {
    const { result } = renderHook(() => useSocket());
    const handler = jest.fn();
    
    act(() => {
      result.current.off('test-event', handler);
    });

    expect(mockSocketManager.off).toHaveBeenCalledWith('test-event', handler);
  });

  test('updates connection status when connected', () => {
    mockSocketManager.isConnected.mockReturnValue(true);
    const { result } = renderHook(() => useSocket());
    
    // Simulate connection status change
    act(() => {
      result.current.connect();
    });

    expect(result.current.isConnected).toBe(true);
  });
});