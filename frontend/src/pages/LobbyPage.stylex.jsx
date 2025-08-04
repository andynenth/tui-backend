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
    padding: spacing.xl,
  },
  
  playerInfoBadge: {
    position: 'absolute',
    top: spacing.md,
    left: spacing.md,
    display: 'flex',
    alignItems: 'center',
    gap: spacing.sm,
    backgroundColor: colors.white,
    padding: `${spacing.xs} ${spacing.md}`,
    borderRadius: layout.radiusFull,
    boxShadow: shadows.md,
    fontSize: typography.textSm,
    fontWeight: typography.weightMedium,
  },
  
  connectionStatus: {
    position: 'absolute',
    top: spacing.md,
    right: spacing.md,
    display: 'flex',
    alignItems: 'center',
    gap: spacing.xs,
    padding: `${spacing.xs} ${spacing.md}`,
    backgroundColor: colors.white,
    borderRadius: layout.radiusFull,
    boxShadow: shadows.sm,
    fontSize: typography.textXs,
    fontWeight: typography.weightMedium,
  },
  
  statusDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    backgroundColor: colors.success,
  },
  
  statusDotDisconnected: {
    backgroundColor: colors.danger,
    animation: `${pulse} 2s ${motion.easeInOut} infinite`,
  },
  
  lobbyHeader: {
    textAlign: 'center',
    marginBottom: spacing.xl,
  },
  
  lobbyTitle: {
    fontSize: typography.text3xl,
    fontWeight: typography.weightBold,
    color: colors.gray900,
    marginBottom: spacing.sm,
  },
  
  lobbySubtitle: {
    fontSize: typography.textBase,
    color: colors.gray600,
  },
  
  actionBar: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.lg,
    gap: spacing.md,
  },
  
  actionButtonsLeft: {
    display: 'flex',
    gap: spacing.sm,
    flex: 1,
  },
  
  button: {
    padding: `${spacing.sm} ${spacing.md}`,
    fontSize: typography.textSm,
    fontWeight: typography.weightMedium,
    borderRadius: layout.radiusMd,
    border: 'none',
    cursor: 'pointer',
    display: 'inline-flex',
    alignItems: 'center',
    gap: spacing.xs,
    transition: `all ${motion.durationFast} ${motion.easeInOut}`,
    ':disabled': {
      opacity: 0.5,
      cursor: 'not-allowed',
    },
  },
  
  successButton: {
    backgroundColor: colors.success,
    color: colors.white,
    ':hover:not(:disabled)': {
      backgroundColor: colors.successDark,
      transform: 'translateY(-2px)',
      boxShadow: shadows.md,
    },
  },
  
  secondaryButton: {
    backgroundColor: colors.gray200,
    color: colors.gray700,
    ':hover:not(:disabled)': {
      backgroundColor: colors.gray300,
      transform: 'translateY(-2px)',
      boxShadow: shadows.md,
    },
  },
  
  iconButton: {
    padding: spacing.sm,
    minWidth: '36px',
    minHeight: '36px',
  },
  
  refreshIcon: {
    display: 'inline-block',
    transition: `transform ${motion.durationBase} ${motion.easeInOut}`,
  },
  
  refreshIconLoading: {
    animation: `${spin} 1s linear infinite`,
  },
  
  roomListSection: {
    backgroundColor: colors.white,
    borderRadius: layout.radiusLg,
    padding: spacing.lg,
    boxShadow: shadows.lg,
    marginBottom: spacing.lg,
  },
  
  roomListHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  
  roomCount: {
    fontSize: typography.textLg,
    fontWeight: typography.weightSemibold,
    color: colors.gray900,
  },
  
  lastUpdated: {
    fontSize: typography.textXs,
    color: colors.gray500,
  },
  
  roomList: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
    gap: spacing.md,
    maxHeight: '400px',
    overflowY: 'auto',
    padding: spacing.xs,
  },
  
  roomCard: {
    backgroundColor: colors.white,
    border: `2px solid ${colors.gray200}`,
    borderRadius: layout.radiusMd,
    padding: spacing.md,
    cursor: 'pointer',
    transition: `all ${motion.durationFast} ${motion.easeInOut}`,
    ':hover': {
      borderColor: colors.primary,
      boxShadow: shadows.md,
      transform: 'translateY(-2px)',
    },
  },
  
  roomCardFull: {
    opacity: 0.6,
    cursor: 'not-allowed',
    ':hover': {
      borderColor: colors.gray200,
      boxShadow: 'none',
      transform: 'none',
    },
  },
  
  roomCardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: spacing.sm,
  },
  
  roomInfo: {
    flex: 1,
  },
  
  roomId: {
    fontSize: typography.textSm,
    fontWeight: typography.weightBold,
    color: colors.gray900,
    marginBottom: spacing.xs,
  },
  
  hostName: {
    fontSize: typography.textXs,
    color: colors.gray600,
  },
  
  roomOccupancy: {
    fontSize: typography.textSm,
    fontWeight: typography.weightMedium,
    padding: `${spacing.xs} ${spacing.sm}`,
    backgroundColor: colors.gray100,
    borderRadius: layout.radiusSm,
    color: colors.gray700,
  },
  
  roomOccupancyFull: {
    backgroundColor: '#fef2f2',
    color: colors.danger,
  },
  
  roomPlayers: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: spacing.xs,
    marginTop: spacing.sm,
  },
  
  playerSlot: {
    fontSize: typography.textXs,
    padding: spacing.xs,
    borderRadius: layout.radiusSm,
    textAlign: 'center',
  },
  
  playerSlotEmpty: {
    backgroundColor: colors.gray50,
    color: colors.gray400,
    border: `1px dashed ${colors.gray300}`,
  },
  
  playerSlotFilled: {
    backgroundColor: colors.primaryLight,
    color: colors.primaryDark,
    border: `1px solid ${colors.primary}`,
  },
  
  playerSlotBot: {
    backgroundColor: '#f3e8ff',
    color: '#6b21a8',
    border: '1px solid #a855f7',
  },
  
  playerSlotContent: {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.xs,
  },
  
  playerSlotName: {
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  
  emptyState: {
    textAlign: 'center',
    padding: `${spacing.xl} ${spacing.lg}`,
  },
  
  emptyIcon: {
    marginBottom: spacing.md,
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
    fontSize: typography.textBase,
    color: colors.gray500,
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
    animation: `${fadeIn} 0.2s ${motion.easeOut}`,
  },
  
  modalContent: {
    backgroundColor: colors.white,
    borderRadius: layout.radiusLg,
    padding: spacing.xl,
    maxWidth: '400px',
    width: '90%',
    boxShadow: shadows.xl,
  },
  
  modalTitle: {
    fontSize: typography.textLg,
    fontWeight: typography.weightBold,
    marginBottom: spacing.md,
    textAlign: 'center',
  },
  
  modalInput: {
    width: '100%',
    padding: `${spacing.sm} ${spacing.md}`,
    fontSize: typography.textBase,
    border: `2px solid ${colors.gray300}`,
    borderRadius: layout.radiusMd,
    marginBottom: spacing.lg,
    textAlign: 'center',
    textTransform: 'uppercase',
    letterSpacing: '0.1em',
    ':focus': {
      outline: 'none',
      borderColor: colors.primary,
      boxShadow: `0 0 0 3px rgba(59, 130, 246, 0.1)`,
    },
  },
  
  modalButtons: {
    display: 'flex',
    gap: spacing.sm,
    justifyContent: 'center',
  },
  
  loadingOverlay: {
    position: 'absolute',
    inset: 0,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    display: 'none',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: layout.radiusLg,
  },
  
  loadingOverlayShow: {
    display: 'flex',
  },
  
  loadingSpinner: {
    width: '40px',
    height: '40px',
    border: '3px solid',
    borderColor: colors.gray200,
    borderTopColor: colors.primary,
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
  const [joinRoomId, setJoinRoomId] = useState('');
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