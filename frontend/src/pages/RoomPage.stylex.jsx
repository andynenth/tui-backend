// frontend/src/pages/RoomPage.stylex.jsx
// Room management page - configure room before starting game

import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, layout, shadows, motion, gradients } from '../design-system/tokens.stylex';
import { useApp } from '../contexts/AppContext';
import Layout from '../components/Layout.stylex';
import Button from '../components/Button.stylex';
import { PlayerAvatar } from '../components/game/shared';
import TruncatedName from '../components/shared/TruncatedName';
import { networkService } from '../services';

// Animations
const pulse = stylex.keyframes({
  '0%, 100%': {
    opacity: 1,
  },
  '50%': {
    opacity: 0.5,
  },
});

const fadeIn = stylex.keyframes({
  '0%': {
    opacity: 0,
    transform: 'scale(0.95)',
  },
  '100%': {
    opacity: 1,
    transform: 'scale(1)',
  },
});

// RoomPage styles
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
  
  roomHeader: {
    textAlign: 'center',
    marginBottom: spacing.xl,
  },
  
  roomTitle: {
    fontSize: typography.text3xl,
    fontWeight: typography.weightBold,
    color: colors.gray900,
    marginBottom: spacing.md,
  },
  
  roomIdBadge: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: spacing.sm,
    backgroundColor: colors.white,
    padding: `${spacing.sm} ${spacing.lg}`,
    borderRadius: layout.radiusFull,
    boxShadow: shadows.md,
  },
  
  roomIdLabel: {
    fontSize: typography.textSm,
    color: colors.gray600,
    fontWeight: typography.weightMedium,
  },
  
  roomIdValue: {
    fontSize: typography.textLg,
    color: colors.primary,
    fontWeight: typography.weightBold,
    letterSpacing: '0.05em',
  },
  
  playersSection: {
    backgroundColor: colors.white,
    borderRadius: layout.radiusLg,
    padding: spacing.lg,
    boxShadow: shadows.xl,
    marginBottom: spacing.lg,
  },
  
  sectionHeader: {
    display: 'flex',
    justifyContent: 'center',
    marginBottom: spacing.lg,
  },
  
  playerCount: {
    fontSize: typography.text2xl,
    fontWeight: typography.weightBold,
    color: colors.gray700,
    padding: `${spacing.sm} ${spacing.lg}`,
    backgroundColor: colors.gray100,
    borderRadius: layout.radiusFull,
  },
  
  playerCountFull: {
    color: colors.successDark,
    backgroundColor: '#dcfce7',
  },
  
  gameTable: {
    position: 'relative',
    width: '100%',
    maxWidth: '500px',
    margin: '0 auto',
    aspectRatio: '1',
  },
  
  tableSurface: {
    position: 'relative',
    width: '100%',
    height: '100%',
    backgroundColor: '#8b7355',
    borderRadius: '50%',
    boxShadow: 'inset 0 0 40px rgba(0,0,0,0.3), 0 10px 30px rgba(0,0,0,0.2)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  
  tableCenter: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    width: '120px',
    height: '120px',
    backgroundColor: '#654321',
    borderRadius: '50%',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    boxShadow: 'inset 0 2px 10px rgba(0,0,0,0.3)',
  },
  
  centerIcon: {
    fontSize: '48px',
    marginBottom: spacing.xs,
  },
  
  centerText: {
    fontSize: typography.textXs,
    color: 'rgba(255,255,255,0.8)',
    fontWeight: typography.weightMedium,
  },
  
  playerSlot: {
    position: 'absolute',
    width: '100px',
    backgroundColor: colors.white,
    borderRadius: layout.radiusMd,
    padding: spacing.sm,
    boxShadow: shadows.md,
    transition: `all ${motion.durationBase} ${motion.easeInOut}`,
    animation: `${fadeIn} 0.3s ${motion.easeOut}`,
  },
  
  slotTop: {
    top: '5%',
    left: '50%',
    transform: 'translateX(-50%)',
  },
  
  slotRight: {
    top: '50%',
    right: '5%',
    transform: 'translateY(-50%)',
  },
  
  slotBottom: {
    bottom: '5%',
    left: '50%',
    transform: 'translateX(-50%)',
  },
  
  slotLeft: {
    top: '50%',
    left: '5%',
    transform: 'translateY(-50%)',
  },
  
  slotEmpty: {
    backgroundColor: colors.gray50,
    border: `2px dashed ${colors.gray300}`,
  },
  
  slotBot: {
    backgroundColor: '#f3e8ff',
    border: '2px solid #a855f7',
  },
  
  slotHost: {
    border: '2px solid',
    borderColor: colors.warning,
    boxShadow: '0 0 20px rgba(251, 191, 36, 0.3)',
  },
  
  slotContent: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: spacing.xs,
  },
  
  playerName: {
    fontSize: typography.textSm,
    fontWeight: typography.weightMedium,
    textAlign: 'center',
  },
  
  emptyText: {
    fontSize: typography.textSm,
    color: colors.gray500,
  },
  
  hostBadge: {
    fontSize: typography.textXs,
    padding: `2px ${spacing.xs}`,
    backgroundColor: colors.warning,
    color: '#92400e',
    borderRadius: layout.radiusSm,
    fontWeight: typography.weightMedium,
  },
  
  slotActions: {
    marginTop: spacing.xs,
    display: 'flex',
    gap: spacing.xs,
  },
  
  slotButton: {
    fontSize: typography.textXs,
    padding: `${spacing.xs} ${spacing.sm}`,
    borderRadius: layout.radiusSm,
    border: 'none',
    cursor: 'pointer',
    transition: `all ${motion.durationFast} ${motion.easeInOut}`,
  },
  
  addBotButton: {
    backgroundColor: colors.gray200,
    color: colors.gray700,
    ':hover': {
      backgroundColor: colors.gray300,
    },
  },
  
  removeButton: {
    backgroundColor: '#fef2f2',
    color: colors.danger,
    ':hover': {
      backgroundColor: '#fee2e2',
    },
  },
  
  footer: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  
  footerButton: {
    padding: `${spacing.sm} ${spacing.lg}`,
    fontSize: typography.textBase,
    fontWeight: typography.weightMedium,
    borderRadius: layout.radiusMd,
    border: 'none',
    cursor: 'pointer',
    transition: `all ${motion.durationFast} ${motion.easeInOut}`,
    ':disabled': {
      opacity: 0.5,
      cursor: 'not-allowed',
    },
  },
  
  leaveButton: {
    backgroundColor: colors.gray200,
    color: colors.gray700,
    ':hover': {
      backgroundColor: colors.gray300,
    },
  },
  
  startButton: {
    backgroundColor: colors.success,
    color: colors.white,
    ':hover:not(:disabled)': {
      backgroundColor: colors.successDark,
      transform: 'scale(1.05)',
    },
  },
  
  centerMessage: {
    textAlign: 'center',
    padding: `${spacing.xl} ${spacing.lg}`,
  },
  
  messageTitle: {
    fontSize: typography.textXl,
    fontWeight: typography.weightSemibold,
    color: colors.gray900,
    marginBottom: spacing.sm,
  },
  
  messageText: {
    fontSize: typography.textBase,
    color: colors.gray600,
    marginBottom: spacing.lg,
  },
});

const RoomPage = () => {
  const navigate = useNavigate();
  const { roomId } = useParams();
  const app = useApp();

  const [roomData, setRoomData] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isStartingGame, setIsStartingGame] = useState(false);

  // Calculate room occupancy
  const occupiedSlots =
    roomData?.players?.filter((player) => player !== null).length || 0;
  const isRoomFull = occupiedSlots === 4;

  // Check if current player is the host
  const isCurrentPlayerHost =
    roomData?.players?.some(
      (player) => player?.name === app.playerName && player?.is_host
    ) || false;

  // Connect to room and get room state
  useEffect(() => {
    let mounted = true;

    const initializeRoom = async () => {
      try {
        await networkService.connectToRoom(roomId, {
          playerName: app.playerName,
        });
        if (mounted) {
          setIsConnected(true);
          networkService.send(roomId, 'get_room_state', {});
        }
      } catch (error) {
        console.error('Failed to connect to room:', error);
      }
    };

    if (roomId && app.playerName) {
      initializeRoom();
    }

    return () => {
      mounted = false;
      if (roomId) {
        networkService.disconnectFromRoom(roomId);
      }
    };
  }, [roomId, app.playerName]);

  // Event handlers for room updates and game start
  useEffect(() => {
    if (!isConnected) return;

    const handleRoomUpdate = (event) => {
      const eventData = event.detail;
      const roomUpdate = eventData.data;
      console.log('🏠 ROOM_UPDATE:', roomUpdate);
      setRoomData(roomUpdate);
    };

    const handleGameStarted = (event) => {
      console.log('Game started, navigating to game page');
      navigate(`/game/${roomId}`);
    };

    const handleRoomClosed = (event) => {
      console.log('🏠 ROOM_CLOSED: Room was closed, navigating to lobby');
      navigate('/lobby');
    };

    networkService.addEventListener('room_update', handleRoomUpdate);
    networkService.addEventListener('game_started', handleGameStarted);
    networkService.addEventListener('room_closed', handleRoomClosed);

    return () => {
      networkService.removeEventListener('room_update', handleRoomUpdate);
      networkService.removeEventListener('game_started', handleGameStarted);
      networkService.removeEventListener('room_closed', handleRoomClosed);
    };
  }, [isConnected, roomId, navigate]);

  const startGame = () => {
    console.log('🎮 START_GAME: Button clicked');
    setIsStartingGame(true);
    networkService.send(roomId, 'start_game', {});
  };

  const addBot = (slotId) => {
    console.log('🤖 ADD_BOT: Button clicked for slot', slotId);
    networkService.send(roomId, 'add_bot', { slot_id: slotId });
  };

  const removePlayer = (slotId) => {
    console.log('🗑️ REMOVE_PLAYER: Button clicked for slot', slotId);
    networkService.send(roomId, 'remove_player', { slot_id: slotId });
  };

  const leaveRoom = () => {
    console.log('🚪 LEAVE_ROOM: Button clicked');
    networkService.send(roomId, 'leave_room', {
      player_name: app.playerName,
    });
    navigate('/lobby');
  };

  // Render player slot
  const renderPlayerSlot = (slotId, position) => {
    const player = roomData?.players?.[slotId];
    const isHost = player?.is_host;
    const isBot = player?.is_bot;
    const isEmpty = !player;

    const positionStyle = 
      position === 'top' ? styles.slotTop :
      position === 'right' ? styles.slotRight :
      position === 'bottom' ? styles.slotBottom :
      styles.slotLeft;

    return (
      <div
        key={slotId}
        {...stylex.props(
          styles.playerSlot,
          positionStyle,
          isEmpty && styles.slotEmpty,
          isBot && styles.slotBot,
          isHost && styles.slotHost
        )}
      >
        <div {...stylex.props(styles.slotContent)}>
          {player ? (
            <>
              <PlayerAvatar
                name={player.name}
                isBot={isBot}
                size="small"
              />
              <div {...stylex.props(styles.playerName)}>
                <TruncatedName name={player.name} maxLength={10} />
              </div>
              {isHost && (
                <div {...stylex.props(styles.hostBadge)}>HOST</div>
              )}
              {isCurrentPlayerHost && player.name !== app.playerName && (
                <div {...stylex.props(styles.slotActions)}>
                  <button
                    {...stylex.props(styles.slotButton, styles.removeButton)}
                    onClick={() => removePlayer(slotId)}
                  >
                    Remove
                  </button>
                </div>
              )}
            </>
          ) : (
            <>
              <div {...stylex.props(styles.emptyText)}>Empty</div>
              {isCurrentPlayerHost && (
                <div {...stylex.props(styles.slotActions)}>
                  <button
                    {...stylex.props(styles.slotButton, styles.addBotButton)}
                    onClick={() => addBot(slotId)}
                  >
                    Add Bot
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    );
  };

  if (!app.playerName) {
    return (
      <Layout title="Room Access">
        <div {...stylex.props(styles.centerMessage)}>
          <h2 {...stylex.props(styles.messageTitle)}>
            Player Name Required
          </h2>
          <p {...stylex.props(styles.messageText)}>
            Please set your player name first.
          </p>
          <Button onClick={() => navigate('/')}>Go to Start Page</Button>
        </div>
      </Layout>
    );
  }

  return (
    <Layout title="" showConnection={false} showHeader={false}>
      <div {...stylex.props(styles.pageContainer)}>
        <div {...stylex.props(styles.gameContainer)}>
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

          {/* Room Header */}
          <div {...stylex.props(styles.roomHeader)}>
            <h1 {...stylex.props(styles.roomTitle)}>Game Room</h1>
            <div {...stylex.props(styles.roomIdBadge)}>
              <span {...stylex.props(styles.roomIdLabel)}>Room ID:</span>
              <span {...stylex.props(styles.roomIdValue)}>{roomId}</span>
            </div>
          </div>

          {/* Players Section with Table Visualization */}
          <div {...stylex.props(styles.playersSection)}>
            <div {...stylex.props(styles.sectionHeader)}>
              <div
                {...stylex.props(
                  styles.playerCount,
                  isRoomFull && styles.playerCountFull
                )}
              >
                {occupiedSlots} / 4
              </div>
            </div>

            {/* Game Table Visualization */}
            <div {...stylex.props(styles.gameTable)}>
              <div {...stylex.props(styles.tableSurface)}>
                {/* Center decoration */}
                <div {...stylex.props(styles.tableCenter)}>
                  <span {...stylex.props(styles.centerIcon)}>🎮</span>
                  <span {...stylex.props(styles.centerText)}>
                    {isRoomFull ? 'Ready!' : 'Waiting...'}
                  </span>
                </div>

                {/* Player slots around the table */}
                {renderPlayerSlot(0, 'top')}
                {renderPlayerSlot(1, 'right')}
                {renderPlayerSlot(2, 'bottom')}
                {renderPlayerSlot(3, 'left')}
              </div>
            </div>
          </div>

          {/* Footer Actions */}
          <div {...stylex.props(styles.footer)}>
            <button
              {...stylex.props(styles.footerButton, styles.leaveButton)}
              onClick={leaveRoom}
            >
              Leave Room
            </button>

            {isCurrentPlayerHost && (
              <button
                {...stylex.props(styles.footerButton, styles.startButton)}
                onClick={startGame}
                disabled={!isRoomFull || isStartingGame}
              >
                {isStartingGame ? 'Starting...' : 'Start Game'}
              </button>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default RoomPage;