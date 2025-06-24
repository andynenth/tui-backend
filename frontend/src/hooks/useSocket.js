// frontend/src/hooks/useSocket.js

import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { SocketManager } from '../../network/SocketManager.js';

/**
 * React hook for WebSocket connection using existing SocketManager
 * Provides connection state and event handling for React components
 */
export function useSocket(roomId, options = {}) {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isReconnecting, setIsReconnecting] = useState(false);
  const [connectionError, setConnectionError] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState({});
  const [lastMessage, setLastMessage] = useState(null);
  
  const socketManagerRef = useRef(null);
  const eventHandlersRef = useRef({});

  // Initialize SocketManager
  useEffect(() => {
    if (!roomId) return;

    const manager = new SocketManager({
      baseUrl: options.baseUrl || `ws://localhost:5050/ws`,
      enableReconnection: options.enableReconnection !== false,
      enableMessageQueue: options.enableMessageQueue !== false,
      maxQueueSize: options.maxQueueSize || 100,
      reconnection: options.reconnection || {}
    });

    socketManagerRef.current = manager;

    // Set up event listeners for connection state
    const handleConnected = (data) => {
      setIsConnected(true);
      setIsConnecting(false);
      setIsReconnecting(false);
      setConnectionError(null);
      console.log('React hook: Connected to room', data.roomId);
    };

    const handleDisconnected = (data) => {
      setIsConnected(false);
      setIsConnecting(false);
      if (data.intentional) {
        setIsReconnecting(false);
        setConnectionError(null);
      }
      console.log('React hook: Disconnected', data);
    };

    const handleReconnecting = (status) => {
      setIsReconnecting(true);
      setConnectionError(null);
      console.log('React hook: Reconnecting...', status);
    };

    const handleReconnected = (data) => {
      setIsReconnecting(false);
      setConnectionError(null);
      console.log('React hook: Reconnected to room', data.roomId);
    };

    const handleConnectionFailed = (data) => {
      setIsConnected(false);
      setIsConnecting(false);
      setIsReconnecting(false);
      setConnectionError(data.error);
      console.error('React hook: Connection failed', data.error);
    };

    const handleReconnectionFailed = (data) => {
      setIsReconnecting(false);
      setConnectionError(data.error);
      console.error('React hook: Reconnection failed after attempts', data.attempts);
    };

    const handleMessage = (data) => {
      setLastMessage({ ...data, timestamp: Date.now() });
    };

    const handleError = (error) => {
      setConnectionError(error);
      console.error('React hook: Socket error', error);
    };

    // Register event listeners
    manager.on('connected', handleConnected);
    manager.on('disconnected', handleDisconnected);
    manager.on('reconnecting', handleReconnecting);
    manager.on('reconnected', handleReconnected);
    manager.on('connection_failed', handleConnectionFailed);
    manager.on('reconnection_failed', handleReconnectionFailed);
    manager.on('message', handleMessage);
    manager.on('error', handleError);

    // Update connection status periodically
    const statusInterval = setInterval(() => {
      setConnectionStatus(manager.getStatus());
    }, 1000);

    // Connect automatically
    setIsConnecting(true);
    manager.connect(roomId).catch(err => {
      console.error('Initial connection failed:', err);
    });

    // Cleanup
    return () => {
      clearInterval(statusInterval);
      manager.disconnect();
    };
  }, [roomId, options.baseUrl, options.enableReconnection, options.enableMessageQueue]);

  // Send message function
  const send = useCallback((event, data = {}) => {
    if (!socketManagerRef.current) return false;
    return socketManagerRef.current.send(event, data);
  }, []);

  // Connect function (manual connection)
  const connect = useCallback(async () => {
    if (!socketManagerRef.current || !roomId) return false;

    setIsConnecting(true);
    setConnectionError(null);

    try {
      await socketManagerRef.current.connect(roomId);
      return true;
    } catch (error) {
      setConnectionError(error);
      setIsConnecting(false);
      return false;
    }
  }, [roomId]);

  // Disconnect function
  const disconnect = useCallback(() => {
    if (!socketManagerRef.current) return;
    socketManagerRef.current.disconnect();
  }, []);

  // Event listener management
  const on = useCallback((event, callback) => {
    if (!socketManagerRef.current) return () => {};

    // Store reference for cleanup
    if (!eventHandlersRef.current[event]) {
      eventHandlersRef.current[event] = [];
    }
    eventHandlersRef.current[event].push(callback);

    // Register with socket manager
    socketManagerRef.current.on(event, callback);

    // Return cleanup function
    return () => {
      if (socketManagerRef.current) {
        socketManagerRef.current.off(event, callback);
      }
      // Remove from our reference
      const handlers = eventHandlersRef.current[event];
      if (handlers) {
        const index = handlers.indexOf(callback);
        if (index > -1) {
          handlers.splice(index, 1);
        }
      }
    };
  }, []);

  const off = useCallback((event, callback) => {
    if (!socketManagerRef.current) return;
    socketManagerRef.current.off(event, callback);
  }, []);

  // Get detailed status
  const getStatus = useCallback(() => {
    if (!socketManagerRef.current) return {};
    return socketManagerRef.current.getStatus();
  }, []);

  // Memoize the return object to prevent unnecessary re-renders
  return useMemo(() => ({
    // Connection state
    isConnected,
    isConnecting,
    isReconnecting,
    connectionError,
    connectionStatus,
    lastMessage,
    
    // Actions
    send,
    connect,
    disconnect,
    on,
    off,
    getStatus,
    
    // Direct access to manager (for advanced usage)
    manager: socketManagerRef.current
  }), [isConnected, isConnecting, isReconnecting, connectionError, connectionStatus, lastMessage, send, connect, disconnect, on, off, getStatus]);
}

/**
 * Hook for managing multiple socket connections (lobby + room)
 */
export function useMultiSocket(lobbyOptions = {}, roomOptions = {}) {
  const lobbySocket = useSocket('lobby', lobbyOptions);
  const [roomId, setRoomId] = useState(null);
  const roomSocket = useSocket(roomId, roomOptions);

  const connectToRoom = useCallback((id) => {
    setRoomId(id);
  }, []);

  const disconnectFromRoom = useCallback(() => {
    roomSocket.disconnect();
    setRoomId(null);
  }, [roomSocket]);

  return {
    lobby: lobbySocket,
    room: {
      ...roomSocket,
      roomId,
      connectToRoom,
      disconnectFromRoom
    }
  };
}