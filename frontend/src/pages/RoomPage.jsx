// frontend/src/pages/RoomPage.jsx

import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useApp } from '../contexts/AppContext';
import { useSocket } from '../hooks/useSocket';
import { Layout, Button, PlayerSlot, Modal, LoadingOverlay } from '../components';

const RoomPage = () => {
  const navigate = useNavigate();
  const { roomId } = useParams();
  const app = useApp();
  const socket = useSocket(roomId);
  
  const [roomData, setRoomData] = useState(null);
  const [isHost, setIsHost] = useState(false);
  const [isStartingGame, setIsStartingGame] = useState(false);
  const [showLeaveModal, setShowLeaveModal] = useState(false);
  

  // Set up socket event listeners
  useEffect(() => {
    if (!socket.isConnected) return;

    const unsubscribers = [];

    // Room state updates
    const unsubRoomUpdate = socket.on('room_update', (data) => {
      setRoomData(data);
      // Check if current player is host - handle object format {P1: ..., P2: ...}
      const playersObj = data.players || data.slots || {};
      
      // Find current player in P1-P4 slots
      let currentPlayer = null;
      for (const slot of ['P1', 'P2', 'P3', 'P4']) {
        const player = playersObj[slot];
        if (player && player.name === app.playerName) {
          currentPlayer = player;
          break;
        }
      }
      setIsHost(currentPlayer?.is_host || false);
    });
    unsubscribers.push(unsubRoomUpdate);

    // Game started
    const unsubGameStarted = socket.on('game_started', (data) => {
      setIsStartingGame(false);
      navigate(`/game/${roomId}`);
    });
    unsubscribers.push(unsubGameStarted);

    // Player joined/left
    const unsubPlayerJoined = socket.on('player_joined', (data) => {
      console.log('Player joined:', data.player_name);
    });
    unsubscribers.push(unsubPlayerJoined);

    const unsubPlayerLeft = socket.on('player_left', (data) => {
      console.log('Player left:', data.player_name);
    });
    unsubscribers.push(unsubPlayerLeft);

    // Room closed
    const unsubRoomClosed = socket.on('room_closed', () => {
      alert('Room was closed by the host');
      app.leaveRoom();
      navigate('/lobby');
    });
    unsubscribers.push(unsubRoomClosed);

    // Error handling
    const unsubError = socket.on('error', (data) => {
      setIsStartingGame(false);
      console.error('Room error:', data);
      alert(data.message || 'An error occurred');
    });
    unsubscribers.push(unsubError);

    // Request room state
    socket.send('get_room_state');

    // Cleanup
    return () => {
      unsubscribers.forEach(unsub => unsub());
    };
  }, [socket.isConnected, app, navigate, roomId]);

  // Sync app room ID with URL parameter
  useEffect(() => {
    if (roomId && roomId !== app.currentRoomId) {
      app.goToRoom(roomId);
    }
  }, [roomId, app]);

  // Room management actions
  const addBot = (slotId) => {
    socket.send('add_bot', { slot_id: slotId });
  };

  const removePlayer = (slotId) => {
    socket.send('remove_player', { slot_id: slotId });
  };

  const startGame = () => {
    setIsStartingGame(true);
    socket.send('start_game');
  };

  const leaveRoom = () => {
    setShowLeaveModal(false);
    socket.send('leave_room', { player_name: app.playerName });
    app.leaveRoom();
    navigate('/lobby');
  };

  // Get player slots (4 slots total)
  const getPlayerSlots = () => {
    const slots = [];
    const playersObj = roomData?.players || roomData?.slots || {};
    
    for (let i = 1; i <= 4; i++) {
      // Handle object format {P1: ..., P2: ..., P3: ..., P4: ...}
      const player = playersObj[`P${i}`] || null;
      slots.push({
        slotId: i,
        occupant: player
      });
    }
    return slots;
  };

  const canStartGame = () => {
    if (!isHost || !roomData) return false;
    const playersObj = roomData?.players || roomData?.slots || {};
    const playerCount = Object.values(playersObj).filter(p => p !== null).length;
    return playerCount === 4; // Need exactly 4 players to start
  };

  const getGameStartTooltip = () => {
    if (!isHost) return 'Only the host can start the game';
    const playersObj = roomData?.players || roomData?.slots || {};
    const playerCount = Object.values(playersObj).filter(p => p !== null).length;
    if (playerCount < 4) return `Need ${4 - playerCount} more players to start`;
    return 'Start the game';
  };

  return (
    <>
      <Layout
        title={`Room ${roomId}`}
        showConnection={true}
        connectionProps={{
          isConnected: socket.isConnected,
          isConnecting: socket.isConnecting,
          isReconnecting: socket.isReconnecting,
          error: socket.connectionError,
          roomId: roomId
        }}
        headerContent={
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-600">
              {app.playerName} {isHost && '(Host)'}
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowLeaveModal(true)}
            >
              Leave Room
            </Button>
          </div>
        }
      >
        <div className="max-w-4xl mx-auto px-4 py-8">
          {/* Room header */}
          <div className="text-center mb-8">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Room {roomId}
            </h1>
            <p className="text-gray-600">
              {(() => {
                const playersObj = roomData?.players || roomData?.slots || {};
                const count = Object.values(playersObj).filter(p => p !== null).length;
                return `${count} / 4 players`;
              })()} 
              {isHost && ' • You are the host'}
            </p>
          </div>

          {/* Player slots */}
          <div className="grid grid-cols-2 gap-6 mb-8">
            {getPlayerSlots().map((slot) => (
              <PlayerSlot
                key={slot.slotId}
                slotId={slot.slotId}
                occupant={slot.occupant}
                isHost={slot.occupant?.is_host || false}
                isCurrentPlayer={slot.occupant?.name === app.playerName}
                canModify={isHost}
                onAddBot={isHost ? addBot : null}
                onRemove={isHost ? removePlayer : null}
                className="h-32"
              />
            ))}
          </div>

          {/* Game controls */}
          <div className="text-center space-y-4">
            {isHost ? (
              <div className="space-y-2">
                <Button
                  size="lg"
                  onClick={startGame}
                  disabled={!canStartGame() || isStartingGame}
                  loading={isStartingGame}
                  title={getGameStartTooltip()}
                >
                  Start Game
                </Button>
                <p className="text-sm text-gray-500">
                  {getGameStartTooltip()}
                </p>
              </div>
            ) : (
              <div className="text-gray-600">
                <p>Waiting for the host to start the game...</p>
                {(() => {
                  const playersObj = roomData?.players || roomData?.slots || {};
                  const count = Object.values(playersObj).filter(p => p !== null).length;
                  return count < 4 ? (
                    <p className="text-sm mt-1">
                      Need {4 - count} more players
                    </p>
                  ) : null;
                })()}
              </div>
            )}
          </div>

          {/* Connection status */}
          {!socket.isConnected && (
            <div className="mt-8 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-center">
                <span className="text-yellow-600 mr-2">⚠️</span>
                <p className="text-yellow-800">
                  {socket.isConnecting ? 'Connecting to room...' : 'Not connected to room'}
                </p>
              </div>
            </div>
          )}
        </div>
      </Layout>

      {/* Leave room confirmation */}
      <Modal
        isOpen={showLeaveModal}
        onClose={() => setShowLeaveModal(false)}
        title="Leave Room"
        size="sm"
      >
        <div className="space-y-4">
          <p className="text-gray-600">
            Are you sure you want to leave this room?
            {isHost && ' As the host, leaving will close the room for all players.'}
          </p>
          
          <div className="flex space-x-3">
            <Button
              variant="danger"
              fullWidth
              onClick={leaveRoom}
            >
              {isHost ? 'Close Room' : 'Leave Room'}
            </Button>
            <Button
              variant="ghost"
              fullWidth
              onClick={() => setShowLeaveModal(false)}
            >
              Stay
            </Button>
          </div>
        </div>
      </Modal>

      <LoadingOverlay
        isVisible={isStartingGame}
        message="Starting game..."
        subtitle="Preparing the game for all players"
      />
    </>
  );
};

export default RoomPage;