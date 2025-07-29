// frontend/src/pages/LobbyPage.jsx

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../contexts/AppContext';
import { useTheme } from '../contexts/ThemeContext';
import { Layout } from '../components';
import { PlayerAvatar } from '../components/game/shared';
// Phase 1-4 Enterprise Architecture
import { networkService } from '../services';
import { TIMING } from '../constants';
// CSS classes are imported globally

const LobbyPage = () => {
  const navigate = useNavigate();
  const app = useApp();
  const { currentTheme } = useTheme();

  const [rooms, setRooms] = useState([]);
  const [isConnected, setIsConnected] = useState(false);

  const [showJoinModal, setShowJoinModal] = useState(false);
  const [isCreatingRoom, setIsCreatingRoom] = useState(false);
  const [isJoiningRoom, setIsJoiningRoom] = useState(false);
  const [joinRoomId, setJoinRoomId] = useState('');
  const [lastUpdateTime, setLastUpdateTime] = useState(Date.now());

  // Stable event handler references to prevent recreation
  const handleRoomListUpdateRef = useRef();
  const handleRoomCreatedRef = useRef();
  const handleRoomJoinedRef = useRef();
  const handleErrorRef = useRef();

  // Room list update handler with functional state updates
  const handleRoomListUpdate = useCallback((event) => {
    const eventData = event.detail;
    const roomListData = eventData.data;
    console.log('🔄 [LOBBY UPDATE] Received room_list_update:', eventData);
    console.log('🔄 [LOBBY UPDATE] Rooms data:', roomListData.rooms);
    console.log('🔄 [LOBBY UPDATE] Room count:', roomListData.rooms?.length || 0);
    
    // Use functional state update to ensure fresh state
    setRooms(prevRooms => {
      const newRooms = roomListData.rooms || [];
      console.log('🔄 [LOBBY UPDATE] State update - prev count:', prevRooms.length, '→ new count:', newRooms.length);
      return newRooms;
    });
    
    setLastUpdateTime(Date.now());
  }, []);

  // Store handler reference for cleanup
  handleRoomListUpdateRef.current = handleRoomListUpdate;

  // Initialize lobby connection and event listeners (stable dependencies)
  useEffect(() => {
    const initializeLobby = async () => {
      try {
        console.log('🔗 [LOBBY] Initializing lobby connection...');
        await networkService.connectToRoom('lobby');
        console.log('✅ [LOBBY] Connected to lobby successfully');
        setIsConnected(true);
      } catch (error) {
        console.error('❌ [LOBBY] Failed to connect to lobby:', error);
        setIsConnected(false);
      }
    };

    initializeLobby();

    const unsubscribers = [];

    // Room list updates - use stable handler reference
    const roomListHandler = (event) => handleRoomListUpdateRef.current?.(event);
    networkService.addEventListener('room_list_update', roomListHandler);
    unsubscribers.push(() =>
      networkService.removeEventListener('room_list_update', roomListHandler)
    );

    // Room created successfully - stable handler
    const roomCreatedHandler = (event) => {
      const eventData = event.detail;
      const roomData = eventData.data;
      console.log('🏠 [ROOM CREATED] Received room_created:', eventData);
      console.log('🏠 [ROOM CREATED] Navigation: room_id =', roomData.room_id);

      // Get current state to avoid stale closure
      const currentIsCreating = handleRoomCreatedRef.current?.isCreatingRoom;
      
      if (roomData.room_id && roomData.room_id !== 'lobby' && currentIsCreating) {
        console.log('✅ [ROOM CREATED] Navigating to new room:', roomData.room_id);
        setIsCreatingRoom(false);
        app.goToRoom(roomData.room_id);
        networkService.disconnectFromRoom('lobby');
        navigate(`/room/${roomData.room_id}`);
      } else {
        console.log('⏭️ [ROOM CREATED] Ignoring event:', {
          roomId: roomData.room_id,
          isCreatingRoom: currentIsCreating,
          reason: roomData.room_id === 'lobby' ? 'lobby event' : 'not creating room',
        });
      }
    };
    networkService.addEventListener('room_created', roomCreatedHandler);
    unsubscribers.push(() =>
      networkService.removeEventListener('room_created', roomCreatedHandler)
    );

    // Room joined successfully - stable handler
    const roomJoinedHandler = (event) => {
      const eventData = event.detail;
      const joinData = eventData.data;
      console.log('🚪 [ROOM JOINED] Received room_joined:', eventData);
      setIsJoiningRoom(false);
      setShowJoinModal(false);
      if (joinData.room_id) {
        app.goToRoom(joinData.room_id);
        navigate(`/room/${joinData.room_id}`);
      }
    };
    networkService.addEventListener('room_joined', roomJoinedHandler);
    unsubscribers.push(() =>
      networkService.removeEventListener('room_joined', roomJoinedHandler)
    );

    // Error handling - stable handler
    const errorHandler = (event) => {
      const eventData = event.detail;
      const errorData = eventData.data;
      console.error('❌ [LOBBY ERROR] Received error:', eventData);
      setIsCreatingRoom(false);
      setIsJoiningRoom(false);
      alert(errorData?.message || 'An error occurred');
    };
    networkService.addEventListener('error', errorHandler);
    unsubscribers.push(() =>
      networkService.removeEventListener('error', errorHandler)
    );

    // Cleanup
    return () => {
      console.log('🧹 [CLEANUP] Cleaning up lobby event listeners');
      unsubscribers.forEach((unsub) => unsub());
      networkService.disconnectFromRoom('lobby');
    };
  }, [app, navigate]); // Stable dependencies only

  // Update handler references when state changes (without recreating listeners)
  useEffect(() => {
    if (handleRoomCreatedRef.current) {
      handleRoomCreatedRef.current.isCreatingRoom = isCreatingRoom;
    }
  }, [isCreatingRoom]);

  // Send get_rooms request when connected
  useEffect(() => {
    if (isConnected) {
      networkService.send('lobby', 'get_rooms', {});
    }
  }, [isConnected]);

  // Refresh room list
  const refreshRooms = () => {
    if (isConnected) {
      networkService.send('lobby', 'get_rooms', {});
    }
  };

  // Create new room
  const createRoom = () => {
    setIsCreatingRoom(true);

    // Add delay to ensure connection stability before sending
    setTimeout(() => {
      networkService.send('lobby', 'create_room', {
        player_name: app.playerName,
      });
    }, TIMING.CREATE_ROOM_DELAY);
  };

  // Join room by ID
  const joinRoomById = () => {
    if (!joinRoomId.trim()) return;

    networkService.send('lobby', 'join_room', {
      room_id: joinRoomId.trim(),
      player_name: app.playerName,
    });
  };

  // Join room from list
  const joinRoom = (roomId) => {
    networkService.send('lobby', 'join_room', {
      room_id: roomId,
      player_name: app.playerName,
    });
  };

  const canJoinRoom = (room) => {
    // Use players array if available, fallback to occupied_slots
    const playerCount = room.players
      ? room.players.filter((player) => player !== null).length
      : room.occupied_slots || 0;
    const maxPlayers = room.total_slots || 4;

    return !room.started && playerCount < maxPlayers;
  };

  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefreshRooms = async () => {
    setIsRefreshing(true);
    refreshRooms();
    setTimeout(() => {
      setIsRefreshing(false);
      setLastUpdateTime(Date.now());
      // Show checkmark briefly
      const icon = document.querySelector('.lp-refreshIcon');
      if (icon) {
        const originalText = icon.textContent;
        icon.textContent = '✓';
        setTimeout(() => {
          icon.textContent = originalText;
        }, TIMING.CHECKMARK_DISPLAY_DURATION);
      }
    }, TIMING.REFRESH_ANIMATION_DURATION);
  };

  // Format last update time
  const formatLastUpdate = () => {
    const now = Date.now();
    const diff = Math.floor((now - lastUpdateTime) / 1000);

    if (diff < 5) return 'just now';
    if (diff < 60) return `${diff}s ago`;
    return `${Math.floor(diff / 60)}m ago`;
  };

  // Update timer - optimized to reduce re-renders
  useEffect(() => {
    const interval = setInterval(() => {
      // Only trigger re-render if component is visible and has rooms
      if (document.visibilityState === 'visible') {
        setLastUpdateTime((prev) => prev); // Trigger re-render for time display
      }
    }, 2000); // Reduced frequency from 1s to 2s

    return () => clearInterval(interval);
  }, []);

  const renderRoomCard = (room) => {
    const playerCount = room.players?.filter((p) => p !== null).length || 0;
    const canJoin = canJoinRoom(room);
    const roomId = room.room_id || room.id;

    return (
      <div
        key={roomId}
        className={`lp-roomCard ${!canJoin ? 'lp-full' : ''}`}
        onClick={() => canJoin && joinRoom(roomId)}
      >
        <div className="lp-roomCardHeader">
          <div className="lp-roomInfo">
            <div className="lp-roomId">{roomId}</div>
            <span className="lp-hostName">
              Host:{' '}
              {room.host_name ||
                room.players?.find((p) => p?.is_host)?.name ||
                'Unknown'}
            </span>
          </div>
          <div
            className={`lp-roomOccupancy ${playerCount === 4 ? 'lp-full' : ''}`}
          >
            {playerCount}/4
          </div>
        </div>

        <div className="lp-roomPlayers">
          {[0, 1, 2, 3].map((slot) => {
            const player = room.players?.[slot];
            return (
              <div
                key={slot}
                className={`lp-playerSlot ${player ? (player.is_bot ? 'lp-bot' : 'lp-filled') : 'lp-empty'}`}
              >
                {player ? (
                  <div className="lp-playerSlotContent">
                    <PlayerAvatar
                      name={player.name || `Bot ${slot + 1}`}
                      isBot={player.is_bot}
                      size="mini"
                    />
                    <span className="lp-playerSlotName">
                      {player.is_bot ? `Bot ${slot + 1}` : player.name}
                    </span>
                  </div>
                ) : (
                  'Empty'
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <>
      <Layout title="" showConnection={false} showHeader={false}>
        <div
          className="min-h-screen flex items-center justify-center"
          style={{ background: 'var(--gradient-gray)' }}
        >
          <div className="lp-gameContainer">
            {/* Player Info Badge */}
            <div className="lp-playerInfoBadge">
              <PlayerAvatar
                name={app.playerName || 'Anonymous'}
                size="mini"
                theme="yellow"
              />
              <span>{app.playerName}</span>
            </div>

            {/* Connection Status */}
            <div
              className={`connection-status ${!isConnected ? 'disconnected' : ''}`}
            >
              <span className="status-dot"></span>
              {isConnected ? 'Connected' : 'Disconnected'}
            </div>

            {/* Lobby Header */}
            <div className="lp-lobbyHeader">
              <h1 className="lp-lobbyTitle">Game Lobby</h1>
              <p className="lp-lobbySubtitle">Find a room or create your own</p>
            </div>

            {/* Action Bar */}
            <div className="lp-actionBar">
              <div className="lp-actionButtonsLeft">
                <button
                  className="btn btn-success btn-sm"
                  onClick={createRoom}
                  disabled={!isConnected || isCreatingRoom}
                >
                  <span>➕</span>{' '}
                  {isCreatingRoom ? 'Creating...' : 'Create Room'}
                </button>
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => setShowJoinModal(true)}
                  disabled={!isConnected}
                >
                  <span>🔗</span> Join by ID
                </button>
              </div>
              <button
                className={`btn btn-secondary btn-sm btn-icon-only ${isRefreshing ? 'lp-loading' : ''}`}
                onClick={handleRefreshRooms}
                disabled={!isConnected || isRefreshing}
                title="Refresh room list"
              >
                <span className="lp-refreshIcon">🔄</span>
              </button>
            </div>

            {/* Room List Section */}
            <div className="lp-roomListSection">
              <div className="lp-roomListHeader">
                <h2 className="lp-roomCount">
                  Available Rooms ({rooms.length})
                </h2>
                <span className="lp-lastUpdated">
                  Updated: {formatLastUpdate()}
                </span>
              </div>

              {rooms.length === 0 ? (
                <div className="lp-emptyState">
                  <div className="lp-emptyIcon">
                    <div className="lp-iconCircle">
                      <img
                        src={currentTheme.uiElements.lobbyEmpty}
                        alt="Empty lobby"
                      />
                    </div>
                  </div>
                  <div className="lp-emptyText">
                    No rooms available right now
                  </div>
                </div>
              ) : (
                <div className="lp-roomList custom-scrollbar">
                  {rooms.map(renderRoomCard)}
                </div>
              )}
            </div>

            {/* Footer Actions */}
            <div className="lp-footerActions">
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => navigate('/')}
              >
                <span>←</span> Back to Start Page
              </button>
            </div>

            {/* Join Modal (Custom styled) */}
            <div className={`lp-modalOverlay ${showJoinModal ? 'show' : ''}`}>
              <div className="lp-modalContent">
                <h3 className="lp-modalTitle">Join Room by ID</h3>
                <input
                  type="text"
                  className="lp-modalInput"
                  placeholder="Enter Room ID"
                  maxLength="6"
                  value={joinRoomId}
                  onChange={(e) => setJoinRoomId(e.target.value.toUpperCase())}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && joinRoomId.trim()) {
                      joinRoomById();
                    }
                  }}
                />
                <div className="lp-modalButtons">
                  <button
                    className="btn btn-info btn-sm"
                    onClick={joinRoomById}
                    disabled={!joinRoomId.trim() || isJoiningRoom}
                  >
                    {isJoiningRoom ? 'Joining...' : 'Join'}
                  </button>
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => {
                      setShowJoinModal(false);
                      setJoinRoomId('');
                    }}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>

            {/* Loading Overlay */}
            <div
              className={`lp-loadingOverlay ${isCreatingRoom || isJoiningRoom ? 'show' : ''}`}
            >
              <div className="lp-loadingSpinner"></div>
            </div>
          </div>
        </div>
      </Layout>
    </>
  );
};

export default LobbyPage;
