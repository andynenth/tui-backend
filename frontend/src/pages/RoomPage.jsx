// frontend/src/pages/RoomPage.jsx
// Room management page - configure room before starting game

import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useApp } from '../contexts/AppContext';
import { Layout, Button } from '../components';
import { networkService } from '../services';

const RoomPage = () => {
  const navigate = useNavigate();
  const { roomId } = useParams();
  const app = useApp();
  
  const [roomData, setRoomData] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isStartingGame, setIsStartingGame] = useState(false);
  
  // Calculate room occupancy
  const occupiedSlots = roomData?.players?.filter(player => player !== null).length || 0;
  const isRoomFull = occupiedSlots === 4;

  // Connect to room and get room state
  useEffect(() => {
    const initializeRoom = async () => {
      try {
        await networkService.connectToRoom(roomId);
        setIsConnected(true);
        
        // Request room state
        networkService.send(roomId, 'get_room_state', {});
      } catch (error) {
        console.error('Failed to connect to room:', error);
      }
    };

    if (roomId && app.playerName) {
      initializeRoom();
    }
  }, [roomId, app.playerName]);

  // Event handlers for room updates and game start
  useEffect(() => {
    if (!isConnected) return;

    const handleRoomUpdate = (event) => {
      const eventData = event.detail;
      const roomUpdate = eventData.data;
      console.log('🏠 ROOM_UPDATE: Full data received:', roomUpdate);
      console.log('🏠 ROOM_UPDATE: Players array:', roomUpdate.players);
      console.log('🏠 ROOM_UPDATE: Players array type:', typeof roomUpdate.players);
      console.log('🏠 ROOM_UPDATE: Players array length:', roomUpdate.players?.length);
      console.log('🏠 ROOM_UPDATE: Players array entries:', Object.entries(roomUpdate.players || {}));
      setRoomData(roomUpdate);
    };

    const handleGameStarted = (event) => {
      const eventData = event.detail;
      const gameData = eventData.data;
      console.log('Game started, navigating to game page');
      navigate(`/game/${roomId}`);
    };

    networkService.addEventListener('room_update', handleRoomUpdate);
    networkService.addEventListener('game_started', handleGameStarted);

    return () => {
      networkService.removeEventListener('room_update', handleRoomUpdate);
      networkService.removeEventListener('game_started', handleGameStarted);
    };
  }, [isConnected, roomId, navigate]);

  const startGame = () => {
    console.log('🎮 START_GAME: Button clicked');
    console.log('🎮 START_GAME: Room ID:', roomId);
    setIsStartingGame(true);
    networkService.send(roomId, 'start_game', {});
  };

  const addBot = (slotId) => {
    console.log('🤖 ADD_BOT: Button clicked for slot', slotId);
    console.log('🤖 ADD_BOT: Sending to room', roomId);
    networkService.send(roomId, 'add_bot', { slot_id: slotId });
  };

  const removePlayer = (slotId) => {
    console.log('🗑️ REMOVE_PLAYER: Button clicked for slot', slotId);
    console.log('🗑️ REMOVE_PLAYER: Sending to room', roomId);
    networkService.send(roomId, 'remove_player', { slot_id: slotId });
  };

  const leaveRoom = () => {
    console.log('🚪 LEAVE_ROOM: Button clicked');
    console.log('🚪 LEAVE_ROOM: Player name:', app.playerName);
    console.log('🚪 LEAVE_ROOM: Room ID:', roomId);
    networkService.send(roomId, 'leave_room', {
      player_name: app.playerName
    });
    navigate('/lobby');
  };

  if (!app.playerName) {
    return (
      <Layout title="Room Access">
        <div className="text-center py-12">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Player Name Required
          </h2>
          <p className="text-gray-600 mb-6">
            Please set your player name first.
          </p>
          <Button onClick={() => navigate('/')}>
            Go to Start Page
          </Button>
        </div>
      </Layout>
    );
  }

  return (
    <Layout 
      title={`Room ${roomId}`}
      showConnection={true}
      connectionProps={{
        isConnected,
        isConnecting: false,
        isReconnecting: false,
        error: null,
        roomId
      }}
      headerContent={
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={leaveRoom}
          >
            Leave Room
          </Button>
        </div>
      }
    >
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Room Header */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Room {roomId}</h1>
              <p className="text-gray-600">Host: {app.playerName}</p>
            </div>
            <div className="text-right">
              <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                isConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}>
                {isConnected ? '✅ Connected' : '❌ Disconnected'}
              </div>
            </div>
          </div>
        </div>

        {/* Player Slots */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Players</h2>
          <div className="grid grid-cols-2 gap-4">
            {[1, 2, 3, 4].map((slotId) => {
              const player = roomData?.players?.[slotId - 1];
              const isEmpty = !player;
              console.log(`🎯 SLOT_${slotId}: player=`, player, 'isEmpty=', isEmpty);
              
              return (
                <div key={slotId} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium text-gray-900">P{slotId}</h3>
                      {player ? (
                        <div className="flex items-center space-x-2">
                          <span className="text-sm text-gray-600">
                            {player.is_bot ? '🤖' : '👤'} {player.name}
                          </span>
                          {player.is_host && (
                            <span className="inline-flex items-center px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">
                              Host
                            </span>
                          )}
                        </div>
                      ) : (
                        <p className="text-sm text-gray-500">Empty</p>
                      )}
                    </div>
                    
                    <div className="flex space-x-2">
                      {isEmpty ? (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => addBot(slotId)}
                          disabled={!isConnected}
                        >
                          Add Bot
                        </Button>
                      ) : !player.is_host ? (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => removePlayer(slotId)}
                          disabled={!isConnected}
                        >
                          Remove
                        </Button>
                      ) : null}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Game Controls */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Game Controls</h2>
              <p className="text-gray-600">Ready to start the game?</p>
            </div>
            <Button
              onClick={startGame}
              disabled={!isConnected || isStartingGame || !isRoomFull}
              size="lg"
            >
              {isStartingGame ? 'Starting...' : isRoomFull ? 'Start Game' : `Start Game (${occupiedSlots}/4)`}
            </Button>
          </div>
        </div>

        {/* Connection Status */}
        {!isConnected && (
          <div className="mt-8 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-center">
              <span className="text-yellow-600 mr-2">⚠️</span>
              <p className="text-yellow-800">
                Not connected to room. Trying to reconnect...
              </p>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default RoomPage;