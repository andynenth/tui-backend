// frontend/src/pages/LobbyPage.jsx

import React, { useState, useEffect } from 'react';
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

  // Initialize lobby connection
  useEffect(() => {
    const initializeLobby = async () => {
      try {
        // Connect to lobby WebSocket
        await networkService.connectToRoom('lobby');
        setIsConnected(true);
      } catch (error) {
        console.error('Failed to connect to lobby:', error);
        setIsConnected(false);
      }
    };

    initializeLobby();

    // Cleanup - disconnect when component unmounts
    return () => {
      networkService.disconnectFromRoom('lobby');
    };
  }, []); // Only run once on mount

  // Set up event listeners
  useEffect(() => {

    const unsubscribers = [];

    // Room list updates
    const handleRoomListUpdate = (event) => {
      const eventData = event.detail;
      const roomListData = eventData.data; // The actual room_list_update data from backend
      console.log('Received room_list_update:', eventData);
      setRooms(roomListData.rooms || []);
      setLastUpdateTime(Date.now());
    };
    networkService.addEventListener('room_list_update', handleRoomListUpdate);
    unsubscribers.push(() =>
      networkService.removeEventListener(
        'room_list_update',
        handleRoomListUpdate
      )
    );

    // Room created successfully
    const handleRoomCreated = (event) => {
      const eventData = event.detail;
      const roomData = eventData.data; // The actual room_created data from backend
      console.log('Received room_created:', eventData);
      console.log(
        '🟢 Navigation: room_id =',
        roomData.room_id,
        'navigating to:',
        `/room/${roomData.room_id}`
      );

      // Only navigate if this is a real room ID (not 'lobby')
      if (roomData.room_id && roomData.room_id !== 'lobby') {
        console.log('✅ Navigating to new room:', roomData.room_id);
        setIsCreatingRoom(false);
        app.goToRoom(roomData.room_id);
        // Disconnect from lobby before navigating to room
        networkService.disconnectFromRoom('lobby');
        navigate(`/room/${roomData.room_id}`);
      } else {
        console.log('⏭️ Ignoring room_created event:', {
          roomId: roomData.room_id,
          reason: 'lobby event',
        });
      }
    };
    networkService.addEventListener('room_created', handleRoomCreated);
    unsubscribers.push(() =>
      networkService.removeEventListener('room_created', handleRoomCreated)
    );

    // Room joined successfully
    const handleRoomJoined = (event) => {
      const eventData = event.detail;
      const joinData = eventData.data; // The actual room_joined data from backend
      setIsJoiningRoom(false);
      setShowJoinModal(false);
      if (joinData.room_id) {
        app.goToRoom(joinData.room_id);
        navigate(`/room/${joinData.room_id}`);
      }
    };
    networkService.addEventListener('room_joined', handleRoomJoined);
    unsubscribers.push(() =>
      networkService.removeEventListener('room_joined', handleRoomJoined)
    );

    // Error handling
    const handleError = (event) => {
      const eventData = event.detail;
      const errorData = eventData.data; // The actual error data from backend
      setIsCreatingRoom(false);
      setIsJoiningRoom(false);
      console.error('Lobby error:', eventData);
      alert(errorData?.message || 'An error occurred');
    };
    networkService.addEventListener('error', handleError);
    unsubscribers.push(() =>
      networkService.removeEventListener('error', handleError)
    );

    // Request initial room list
    if (isConnected) {
      networkService.send('lobby', 'get_rooms', {});
    }

    // Cleanup event listeners
    return () => {
      unsubscribers.forEach((unsub) => unsub());
    };
  }, [isConnected]); // Re-run when connection status changes

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

  // Update timer
  useEffect(() => {
    const interval = setInterval(() => {
      // Force re-render to update time display
      setLastUpdateTime((prev) => prev);
    }, 1000);

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
