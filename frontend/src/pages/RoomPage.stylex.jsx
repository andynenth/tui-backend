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
    padding: '2rem',
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
  
  roomHeader: {
    textAlign: 'center',
    marginBottom: '2rem',
  },
  
  roomTitle: {
    fontSize: '1.875rem',
    fontWeight: '700',
    color: '#212529',
    marginBottom: '1rem',
  },
  
  roomIdBadge: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.5rem',
    backgroundColor: '#ffffff',
    padding: `'0.5rem' '1.5rem'`,
    borderRadius: '9999px',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  },
  
  roomIdLabel: {
    fontSize: '0.875rem',
    color: '#6c757d',
    fontWeight: '500',
  },
  
  roomIdValue: {
    fontSize: '1.125rem',
    color: '#0d6efd',
    fontWeight: '700',
    letterSpacing: '0.05em',
  },
  
  playersSection: {
    backgroundColor: '#ffffff',
    borderRadius: '0.5rem',
    padding: '1.5rem',
    boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    marginBottom: '1.5rem',
  },
  
  sectionHeader: {
    display: 'flex',
    justifyContent: 'center',
    marginBottom: '1.5rem',
  },
  
  playerCount: {
    fontSize: '1.5rem',
    fontWeight: '700',
    color: '#495057',
    padding: `'0.5rem' '1.5rem'`,
    backgroundColor: '#f1f3f5',
    borderRadius: '9999px',
  },
  
  playerCountFull: {
    color: '#146c43',
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
    marginBottom: '0.25rem',
  },
  
  centerText: {
    fontSize: '0.75rem',
    color: 'rgba(255,255,255,0.8)',
    fontWeight: '500',
  },
  
  playerSlot: {
    position: 'absolute',
    width: '100px',
    backgroundColor: '#ffffff',
    borderRadius: '0.375rem',
    padding: '0.5rem',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    transition: `all '300ms' 'cubic-bezier(0.4, 0, 0.2, 1)'`,
    animation: `${fadeIn} 0.3s 'cubic-bezier(0, 0, 0.2, 1)'`,
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
    backgroundColor: '#f8f9fa',
    borderWidth: '2px',
    borderStyle: 'dashed',
    borderColor: '#dee2e6',
  },
  
  slotBot: {
    backgroundColor: '#f3e8ff',
    borderWidth: '2px',
    borderStyle: 'solid',
    borderColor: '#a855f7',
  },
  
  slotHost: {
    border: '2px solid',
    borderColor: '#ffc107',
    boxShadow: '0 0 20px rgba(251, 191, 36, 0.3)',
  },
  
  slotContent: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '0.25rem',
  },
  
  playerName: {
    fontSize: '0.875rem',
    fontWeight: '500',
    textAlign: 'center',
  },
  
  emptyText: {
    fontSize: '0.875rem',
    color: '#adb5bd',
  },
  
  hostBadge: {
    fontSize: '0.75rem',
    padding: `2px '0.25rem'`,
    backgroundColor: '#ffc107',
    color: '#92400e',
    borderRadius: '0.125rem',
    fontWeight: '500',
  },
  
  slotActions: {
    marginTop: '0.25rem',
    display: 'flex',
    gap: '0.25rem',
  },
  
  slotButton: {
    fontSize: '0.75rem',
    padding: `'0.25rem' '0.5rem'`,
    borderRadius: '0.125rem',
    border: 'none',
    cursor: 'pointer',
    transition: `all '150ms' 'cubic-bezier(0.4, 0, 0.2, 1)'`,
  },
  
  addBotButton: {
    backgroundColor: '#e9ecef',
    color: '#495057',
    ':hover': {
      backgroundColor: '#dee2e6',
    },
  },
  
  removeButton: {
    backgroundColor: '#fef2f2',
    color: '#dc3545',
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
    padding: `'0.5rem' '1.5rem'`,
    fontSize: '1rem',
    fontWeight: '500',
    borderRadius: '0.375rem',
    border: 'none',
    cursor: 'pointer',
    transition: `all '150ms' 'cubic-bezier(0.4, 0, 0.2, 1)'`,
    ':disabled': {
      opacity: 0.5,
      cursor: 'not-allowed',
    },
  },
  
  leaveButton: {
    backgroundColor: '#e9ecef',
    color: '#495057',
    ':hover': {
      backgroundColor: '#dee2e6',
    },
  },
  
  startButton: {
    backgroundColor: '#198754',
    color: '#ffffff',
    ':hover:not(:disabled)': {
      backgroundColor: '#146c43',
      transform: 'scale(1.05)',
    },
  },
  
  centerMessage: {
    textAlign: 'center',
    padding: `'2rem' '1.5rem'`,
  },
  
  messageTitle: {
    fontSize: '1.25rem',
    fontWeight: '600',
    color: '#212529',
    marginBottom: '0.5rem',
  },
  
  messageText: {
    fontSize: '1rem',
    color: '#6c757d',
    marginBottom: '1.5rem',
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