// frontend/src/pages/LobbyPage.stylex.jsx

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, layout, shadows, motion, gradients } from '../design-system/tokens.stylex';
import { useApp } from '../contexts/AppContext';
import { useTheme } from '../contexts/ThemeContext';
import Layout from '../components/Layout.stylex';
import { PlayerAvatar } from '../components/game/shared';
import { networkService } from '../services';
import { TIMING } from '../constants';

// Animations
const spin = stylex.keyframes({
  '0%': {
    transform: 'rotate(0deg)',
  },
  '100%': {
    transform: 'rotate(360deg)',
  },
});

const fadeIn = stylex.keyframes({
  '0%': {
    opacity: 0,
  },
  '100%': {
    opacity: 1,
  },
});

const pulse = stylex.keyframes({
  '0%, 100%': {
    opacity: 1,
  },
  '50%': {
    opacity: 0.5,
  },
});

// LobbyPage styles
const styles = stylex.create({
  pageContainer: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundImage: gradients.gray,
  },
  
  gameContainer: {
    position: 'relative',
    width: '100%',
    maxWidth: '800px',
    padding: '2rem',
  },
  
  playerInfoBadge: {
    position: 'absolute',
    top: '1rem',
    left: '1rem',
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    backgroundColor: '#ffffff',
    padding: `'0.25rem' '1rem'`,
    borderRadius: '9999px',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    fontSize: '0.875rem',
    fontWeight: '500',
  },
  
  connectionStatus: {
    position: 'absolute',
    top: '1rem',
    right: '1rem',
    display: 'flex',
    alignItems: 'center',
    gap: '0.25rem',
    padding: `'0.25rem' '1rem'`,
    backgroundColor: '#ffffff',
    borderRadius: '9999px',
    boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    fontSize: '0.75rem',
    fontWeight: '500',
  },
  
  statusDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    backgroundColor: '#198754',
  },
  
  statusDotDisconnected: {
    backgroundColor: '#dc3545',
    animation: `${pulse} 2s 'cubic-bezier(0.4, 0, 0.2, 1)' infinite`,
  },
  
  lobbyHeader: {
    textAlign: 'center',
    marginBottom: '2rem',
  },
  
  lobbyTitle: {
    fontSize: '1.875rem',
    fontWeight: '700',
    color: '#212529',
    marginBottom: '0.5rem',
  },
  
  lobbySubtitle: {
    fontSize: '1rem',
    color: '#6c757d',
  },
  
  actionBar: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1.5rem',
    gap: '1rem',
  },
  
  actionButtonsLeft: {
    display: 'flex',
    gap: '0.5rem',
    flex: 1,
  },
  
  button: {
    padding: `'0.5rem' '1rem'`,
    fontSize: '0.875rem',
    fontWeight: '500',
    borderRadius: '0.375rem',
    border: 'none',
    cursor: 'pointer',
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.25rem',
    transition: `all '150ms' 'cubic-bezier(0.4, 0, 0.2, 1)'`,
    ':disabled': {
      opacity: 0.5,
      cursor: 'not-allowed',
    },
  },
  
  successButton: {
    backgroundColor: '#198754',
    color: '#ffffff',
    ':hover:not(:disabled)': {
      backgroundColor: '#146c43',
      transform: 'translateY(-2px)',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    },
  },
  
  secondaryButton: {
    backgroundColor: '#e9ecef',
    color: '#495057',
    ':hover:not(:disabled)': {
      backgroundColor: '#dee2e6',
      transform: 'translateY(-2px)',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    },
  },
  
  iconButton: {
    padding: '0.5rem',
    minWidth: '36px',
    minHeight: '36px',
  },
  
  refreshIcon: {
    display: 'inline-block',
    transition: `transform '300ms' 'cubic-bezier(0.4, 0, 0.2, 1)'`,
  },
  
  refreshIconLoading: {
    animation: `${spin} 1s linear infinite`,
  },
  
  roomListSection: {
    backgroundColor: '#ffffff',
    borderRadius: '0.5rem',
    padding: '1.5rem',
    boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    marginBottom: '1.5rem',
  },
  
  roomListHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1rem',
  },
  
  roomCount: {
    fontSize: '1.125rem',
    fontWeight: '600',
    color: '#212529',
  },
  
  lastUpdated: {
    fontSize: '0.75rem',
    color: '#adb5bd',
  },
  
  roomList: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
    gap: '1rem',
    maxHeight: '400px',
    overflowY: 'auto',
    padding: '0.25rem',
  },
  
  roomCard: {
    backgroundColor: '#ffffff',
    borderWidth: '2px',
    borderStyle: 'solid',
    borderColor: '#e9ecef',
    borderRadius: '0.375rem',
    padding: '1rem',
    cursor: 'pointer',
    transition: `all '150ms' 'cubic-bezier(0.4, 0, 0.2, 1)'`,
    ':hover': {
      borderColor: '#0d6efd',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
      transform: 'translateY(-2px)',
    },
  },
  
  roomCardFull: {
    opacity: 0.6,
    cursor: 'not-allowed',
    ':hover': {
      borderColor: '#e9ecef',
      boxShadow: 'none',
      transform: 'none',
    },
  },
  
  roomCardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: '0.5rem',
  },
  
  roomInfo: {
    flex: 1,
  },
  
  roomId: {
    fontSize: '0.875rem',
    fontWeight: '700',
    color: '#212529',
    marginBottom: '0.25rem',
  },
  
  hostName: {
    fontSize: '0.75rem',
    color: '#6c757d',
  },
  
  roomOccupancy: {
    fontSize: '0.875rem',
    fontWeight: '500',
    padding: `'0.25rem' '0.5rem'`,
    backgroundColor: '#f1f3f5',
    borderRadius: '0.125rem',
    color: '#495057',
  },
  
  roomOccupancyFull: {
    backgroundColor: '#fef2f2',
    color: '#dc3545',
  },
  
  roomPlayers: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '0.25rem',
    marginTop: '0.5rem',
  },
  
  playerSlot: {
    fontSize: '0.75rem',
    padding: '0.25rem',
    borderRadius: '0.125rem',
    textAlign: 'center',
  },
  
  playerSlotEmpty: {
    backgroundColor: '#f8f9fa',
    color: '#ced4da',
    borderWidth: '1px',
    borderStyle: 'dashed',
    borderColor: '#dee2e6',
  },
  
  playerSlotFilled: {
    backgroundColor: '#e7f1ff',
    color: '#0056b3',
    borderWidth: '1px',
    borderStyle: 'solid',
    borderColor: '#0d6efd',
  },
  
  playerSlotBot: {
    backgroundColor: '#f3e8ff',
    color: '#6b21a8',
    borderWidth: '1px',
    borderStyle: 'solid',
    borderColor: '#a855f7',
  },
  
  playerSlotContent: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.25rem',
  },
  
  playerSlotName: {
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  
  emptyState: {
    textAlign: 'center',
    padding: `'2rem' '1.5rem'`,
  },
  
  emptyIcon: {
    marginBottom: '1rem',
  },
  
  iconCircle: {
    width: '80px',
    height: '80px',
    margin: '0 auto',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  
  emptyText: {
    fontSize: '1rem',
    color: '#adb5bd',
  },
  
  footerActions: {
    textAlign: 'center',
  },
  
  modalOverlay: {
    position: 'fixed',
    inset: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    display: 'none',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 100,
  },
  
  modalOverlayShow: {
    display: 'flex',
    animation: `${fadeIn} 0.2s 'cubic-bezier(0, 0, 0.2, 1)'`,
  },
  
  modalContent: {
    backgroundColor: '#ffffff',
    borderRadius: '0.5rem',
    padding: '2rem',
    maxWidth: '400px',
    width: '90%',
    boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  },
  
  modalTitle: {
    fontSize: '1.125rem',
    fontWeight: '700',
    marginBottom: '1rem',
    textAlign: 'center',
  },
  
  modalInput: {
    width: '100%',
    padding: `'0.5rem' '1rem'`,
    fontSize: '1rem',
    borderWidth: '2px',
    borderStyle: 'solid',
    borderColor: '#dee2e6',
    borderRadius: '0.375rem',
    marginBottom: '1.5rem',
    textAlign: 'center',
    textTransform: 'uppercase',
    letterSpacing: '0.1em',
    ':focus': {
      outline: 'none',
      borderColor: '#0d6efd',
      boxShadow: `0 0 0 3px rgba(59, 130, 246, 0.1)`,
    },
  },
  
  modalButtons: {
    display: 'flex',
    gap: '0.5rem',
    justifyContent: 'center',
  },
  
  loadingOverlay: {
    position: 'absolute',
    inset: 0,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    display: 'none',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: '0.5rem',
  },
  
  loadingOverlayShow: {
    display: 'flex',
  },
  
  loadingSpinner: {
    width: '40px',
    height: '40px',
    border: '3px solid',
    borderColor: '#e9ecef',
    borderTopColor: '#0d6efd',
    borderRadius: '50%',
    animation: `${spin} 0.8s linear infinite`,
  },
});

const LobbyPage = () => {
  const navigate = useNavigate();
  const app = useApp();
  const { currentTheme } = useTheme();

  const [rooms, setRooms] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [showJoinModal, setShowJoinModal] = useState(false);
  const [isCreatingRoom, setIsCreatingRoom] = useState(false);
  const [isJoiningRoom, setIsJoiningRoom] = useState(false);
  const [joinRoomId, setJoinRoomId] = useState(');
  const [lastUpdateTime, setLastUpdateTime] = useState(Date.now());
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Initialize lobby connection and event listeners
  useEffect(() => {
    const initializeLobby = async () => {
      try {
        await networkService.connectToRoom('lobby');
        setIsConnected(true);
      } catch (error) {
        console.error('Failed to connect to lobby:', error);
        setIsConnected(false);
      }
    };

    initializeLobby();

    const unsubscribers = [];

    // Room list updates
    const handleRoomListUpdate = (event) => {
      const eventData = event.detail;
      const roomListData = eventData.data;
      console.log('Received room_list_update:', eventData);
      setRooms(roomListData.rooms || []);
      setLastUpdateTime(Date.now());
    };
    networkService.addEventListener('room_list_update', handleRoomListUpdate);
    unsubscribers.push(() =>
      networkService.removeEventListener('room_list_update', handleRoomListUpdate)
    );

    // Room created successfully
    const handleRoomCreated = (event) => {
      const eventData = event.detail;
      const roomData = eventData.data;
      console.log('Received room_created:', eventData);

      if (roomData.room_id && roomData.room_id !== 'lobby' && isCreatingRoom) {
        console.log('✅ Navigating to new room:', roomData.room_id);
        setIsCreatingRoom(false);
        app.goToRoom(roomData.room_id);
        networkService.disconnectFromRoom('lobby');
        navigate(`/room/${roomData.room_id}`);
      }
    };
    networkService.addEventListener('room_created', handleRoomCreated);
    unsubscribers.push(() =>
      networkService.removeEventListener('room_created', handleRoomCreated)
    );

    // Room joined successfully
    const handleRoomJoined = (event) => {
      const eventData = event.detail;
      const joinData = eventData.data;
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
      const errorData = eventData.data;
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

    // Cleanup
    return () => {
      unsubscribers.forEach((unsub) => unsub());
      networkService.disconnectFromRoom('lobby');
    };
  }, [isConnected, isCreatingRoom, app, navigate, isJoiningRoom]);

  // Refresh room list
  const refreshRooms = () => {
    if (isConnected) {
      networkService.send('lobby', 'get_rooms', {});
    }
  };

  // Create new room
  const createRoom = () => {
    setIsCreatingRoom(true);
    setTimeout(() => {
      networkService.send('lobby', 'create_room', {
        player_name: app.playerName,
      });
    }, TIMING.CREATE_ROOM_DELAY);
  };

  // Join room by ID
  const joinRoomById = () => {
    if (!joinRoomId.trim()) return;
    setIsJoiningRoom(true);
    networkService.send('lobby', 'join_room', {
      room_id: joinRoomId.trim(),
      player_name: app.playerName,
    });
  };

  // Join room from list
  const joinRoom = (roomId) => {
    setIsJoiningRoom(true);
    networkService.send('lobby', 'join_room', {
      room_id: roomId,
      player_name: app.playerName,
    });
  };

  const canJoinRoom = (room) => {
    const playerCount = room.players
      ? room.players.filter((player) => player !== null).length
      : room.occupied_slots || 0;
    const maxPlayers = room.total_slots || 4;
    return !room.started && playerCount < maxPlayers;
  };

  const handleRefreshRooms = async () => {
    setIsRefreshing(true);
    refreshRooms();
    setTimeout(() => {
      setIsRefreshing(false);
      setLastUpdateTime(Date.now());
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
        {...stylex.props(
          styles.roomCard,
          !canJoin && styles.roomCardFull
        )}
        onClick={() => canJoin && joinRoom(roomId)}
      >
        <div {...stylex.props(styles.roomCardHeader)}>
          <div {...stylex.props(styles.roomInfo)}>
            <div {...stylex.props(styles.roomId)}>{roomId}</div>
            <span {...stylex.props(styles.hostName)}>
              Host:{' '}
              {room.host_name ||
                room.players?.find((p) => p?.is_host)?.name ||
                'Unknown'}
            </span>
          </div>
          <div
            {...stylex.props(
              styles.roomOccupancy,
              playerCount === 4 && styles.roomOccupancyFull
            )}
          >
            {playerCount}/4
          </div>
        </div>

        <div {...stylex.props(styles.roomPlayers)}>
          {[0, 1, 2, 3].map((slot) => {
            const player = room.players?.[slot];
            return (
              <div
                key={slot}
                {...stylex.props(
                  styles.playerSlot,
                  player
                    ? player.is_bot
                      ? styles.playerSlotBot
                      : styles.playerSlotFilled
                    : styles.playerSlotEmpty
                )}
              >
                {player ? (
                  <div {...stylex.props(styles.playerSlotContent)}>
                    <PlayerAvatar
                      name={player.name || `Bot ${slot + 1}`}
                      isBot={player.is_bot}
                      size="mini"
                    />
                    <span {...stylex.props(styles.playerSlotName)}>
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
        <div {...stylex.props(styles.pageContainer)}>
          <div {...stylex.props(styles.gameContainer)}>
            {/* Player Info Badge */}
            <div {...stylex.props(styles.playerInfoBadge)}>
              <PlayerAvatar
                name={app.playerName || 'Anonymous'}
                size="mini"
                theme="yellow"
              />
              <span>{app.playerName}</span>
            </div>

            {/* Connection Status */}
            <div {...stylex.props(styles.connectionStatus)}>
              <span
                {...stylex.props(
                  styles.statusDot,
                  !isConnected && styles.statusDotDisconnected
                )}
              />
              {isConnected ? 'Connected' : 'Disconnected'}
            </div>

            {/* Lobby Header */}
            <div {...stylex.props(styles.lobbyHeader)}>
              <h1 {...stylex.props(styles.lobbyTitle)}>Game Lobby</h1>
              <p {...stylex.props(styles.lobbySubtitle)}>
                Find a room or create your own
              </p>
            </div>

            {/* Action Bar */}
            <div {...stylex.props(styles.actionBar)}>
              <div {...stylex.props(styles.actionButtonsLeft)}>
                <button
                  {...stylex.props(styles.button, styles.successButton)}
                  onClick={createRoom}
                  disabled={!isConnected || isCreatingRoom}
                >
                  <span>➕</span>{' '}
                  {isCreatingRoom ? 'Creating...' : 'Create Room'}
                </button>
                <button
                  {...stylex.props(styles.button, styles.secondaryButton)}
                  onClick={() => setShowJoinModal(true)}
                  disabled={!isConnected}
                >
                  <span>🔗</span> Join by ID
                </button>
              </div>
              <button
                {...stylex.props(
                  styles.button,
                  styles.secondaryButton,
                  styles.iconButton
                )}
                onClick={handleRefreshRooms}
                disabled={!isConnected || isRefreshing}
                title="Refresh room list"
              >
                <span
                  {...stylex.props(
                    styles.refreshIcon,
                    isRefreshing && styles.refreshIconLoading
                  )}
                >
                  🔄
                </span>
              </button>
            </div>

            {/* Room List Section */}
            <div {...stylex.props(styles.roomListSection)}>
              <div {...stylex.props(styles.roomListHeader)}>
                <h2 {...stylex.props(styles.roomCount)}>
                  Available Rooms ({rooms.length})
                </h2>
                <span {...stylex.props(styles.lastUpdated)}>
                  Updated: {formatLastUpdate()}
                </span>
              </div>

              {rooms.length === 0 ? (
                <div {...stylex.props(styles.emptyState)}>
                  <div {...stylex.props(styles.emptyIcon)}>
                    <div {...stylex.props(styles.iconCircle)}>
                      <img
                        src={currentTheme.uiElements.lobbyEmpty}
                        alt="Empty lobby"
                      />
                    </div>
                  </div>
                  <div {...stylex.props(styles.emptyText)}>
                    No rooms available right now
                  </div>
                </div>
              ) : (
                <div {...stylex.props(styles.roomList)}>
                  {rooms.map(renderRoomCard)}
                </div>
              )}
            </div>

            {/* Footer Actions */}
            <div {...stylex.props(styles.footerActions)}>
              <button
                {...stylex.props(styles.button, styles.secondaryButton)}
                onClick={() => navigate('/')}
              >
                <span>←</span> Back to Start Page
              </button>
            </div>

            {/* Join Modal */}
            <div
              {...stylex.props(
                styles.modalOverlay,
                showJoinModal && styles.modalOverlayShow
              )}
            >
              <div {...stylex.props(styles.modalContent)}>
                <h3 {...stylex.props(styles.modalTitle)}>Join Room by ID</h3>
                <input
                  type="text"
                  {...stylex.props(styles.modalInput)}
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
                <div {...stylex.props(styles.modalButtons)}>
                  <button
                    {...stylex.props(styles.button, styles.successButton)}
                    onClick={joinRoomById}
                    disabled={!joinRoomId.trim() || isJoiningRoom}
                  >
                    {isJoiningRoom ? 'Joining...' : 'Join'}
                  </button>
                  <button
                    {...stylex.props(styles.button, styles.secondaryButton)}
                    onClick={() => {
                      setShowJoinModal(false);
                      setJoinRoomId(');
                    }}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>

            {/* Loading Overlay */}
            <div
              {...stylex.props(
                styles.loadingOverlay,
                (isCreatingRoom || isJoiningRoom) && styles.loadingOverlayShow
              )}
            >
              <div {...stylex.props(styles.loadingSpinner)} />
            </div>
          </div>
        </div>
      </Layout>
    </>
  );
};

export default LobbyPage;