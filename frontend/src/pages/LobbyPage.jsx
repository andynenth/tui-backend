// frontend/src/pages/LobbyPage.jsx

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../contexts/AppContext';
import { Layout, Button, Input, Modal, LoadingOverlay } from '../components';
// Phase 1-4 Enterprise Architecture
import { networkService } from '../services';

const LobbyPage = () => {
  const navigate = useNavigate();
  const app = useApp();
  
  const [rooms, setRooms] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionError, setConnectionError] = useState(null);
  
  const [showJoinModal, setShowJoinModal] = useState(false);
  const [isCreatingRoom, setIsCreatingRoom] = useState(false);
  const [isJoiningRoom, setIsJoiningRoom] = useState(false);
  const [joinRoomId, setJoinRoomId] = useState('');

  // Initialize lobby connection and event listeners
  useEffect(() => {
    const initializeLobby = async () => {
      setIsConnecting(true);
      try {
        // Connect to lobby WebSocket
        await networkService.connectToRoom('lobby');
        setIsConnected(true);
        setConnectionError(null);
      } catch (error) {
        console.error('Failed to connect to lobby:', error);
        setConnectionError(error.message);
        setIsConnected(false);
      } finally {
        setIsConnecting(false);
      }
    };

    initializeLobby();

    const unsubscribers = [];

    // Room list updates
    const handleRoomListUpdate = (event) => {
      const eventData = event.detail;
      const roomListData = eventData.data; // The actual room_list_update data from backend
      console.log('Received room_list_update:', eventData);
      setRooms(roomListData.rooms || []);
    };
    networkService.addEventListener('room_list_update', handleRoomListUpdate);
    unsubscribers.push(() => networkService.removeEventListener('room_list_update', handleRoomListUpdate));

    // Room created successfully
    const handleRoomCreated = (event) => {
      const eventData = event.detail;
      const roomData = eventData.data; // The actual room_created data from backend
      console.log('Received room_created:', eventData);
      console.log('🟢 Navigation: room_id =', roomData.room_id, 'navigating to:', `/room/${roomData.room_id}`);
      
      // Only navigate if this is a real room ID (not 'lobby') and we're currently creating a room
      if (roomData.room_id && roomData.room_id !== 'lobby' && isCreatingRoom) {
        console.log('✅ Navigating to new room:', roomData.room_id);
        setIsCreatingRoom(false);
        app.goToRoom(roomData.room_id);
        // Disconnect from lobby before navigating to room
        networkService.disconnectFromRoom('lobby');
        navigate(`/room/${roomData.room_id}`);
      } else {
        console.log('⏭️ Ignoring room_created event:', { 
          roomId: roomData.room_id, 
          isCreatingRoom, 
          reason: roomData.room_id === 'lobby' ? 'lobby event' : 'not creating room'
        });
      }
    };
    networkService.addEventListener('room_created', handleRoomCreated);
    unsubscribers.push(() => networkService.removeEventListener('room_created', handleRoomCreated));

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
    unsubscribers.push(() => networkService.removeEventListener('room_joined', handleRoomJoined));

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
    unsubscribers.push(() => networkService.removeEventListener('error', handleError));

    // Request initial room list
    if (isConnected) {
      networkService.send('lobby', 'get_rooms', {});
    }

    // Cleanup
    return () => {
      unsubscribers.forEach(unsub => unsub());
    };
  }, [isConnected, isCreatingRoom, app, navigate]);

  // Refresh room list
  const refreshRooms = () => {
    if (isConnected) {
      networkService.send('lobby', 'get_rooms', {});
    }
  };

  // Create new room
  const createRoom = () => {
    setIsCreatingRoom(true);
    
    // Phase 5.2: Remove artificial delay for <50ms state sync optimization
    networkService.send('lobby', 'create_room', {
      player_name: app.playerName
    });
  };

  // Join room by ID
  const joinRoomById = () => {
    if (!joinRoomId.trim()) return;
    
    setIsJoiningRoom(true);
    networkService.send('lobby', 'join_room', {
      room_id: joinRoomId.trim(),
      player_name: app.playerName
    });
  };

  // Join room from list
  const joinRoom = (roomId) => {
    networkService.send('lobby', 'join_room', {
      room_id: roomId,
      player_name: app.playerName
    });
  };

  const getRoomStatusText = (room) => {
    // Use players array if available, fallback to occupied_slots
    const playerCount = room.players 
      ? room.players.filter(player => player !== null).length 
      : (room.occupied_slots || 0);
    const maxPlayers = room.total_slots || 4;
    
    if (room.started || room.status === 'playing') {
      return `🎮 In Game (${playerCount}/${maxPlayers})`;
    }
    
    if (playerCount >= maxPlayers) {
      return `🔒 Full (${playerCount}/${maxPlayers})`;
    }
    
    return `⏳ Waiting (${playerCount}/${maxPlayers})`;
  };

  const canJoinRoom = (room) => {
    // Use players array if available, fallback to occupied_slots
    const playerCount = room.players 
      ? room.players.filter(player => player !== null).length 
      : (room.occupied_slots || 0);
    const maxPlayers = room.total_slots || 4;
    
    return !room.started && playerCount < maxPlayers;
  };

  return (
    <>
      <Layout
        title="Game Lobby"
        showConnection={true}
        connectionProps={{
          isConnected,
          isConnecting,
          isReconnecting: false,
          error: connectionError,
          roomId: 'lobby'
        }}
        headerContent={
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">
              Welcome, {app.playerName}
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/')}
            >
              Change Name
            </Button>
          </div>
        }
      >
        <div className="max-w-6xl mx-auto px-4 py-8">
          {/* Actions */}
          <div className="flex flex-wrap items-center justify-between gap-4 mb-8">
            <div className="flex items-center space-x-4">
              <Button
                variant="primary"
                onClick={createRoom}
                disabled={!isConnected || isCreatingRoom}
              >
                {isCreatingRoom ? 'Creating...' : 'Create Room'}
              </Button>
              
              <Button
                variant="outline"
                onClick={() => setShowJoinModal(true)}
                disabled={!isConnected}
              >
                Join by ID
              </Button>
            </div>

            <Button
              variant="ghost"
              onClick={refreshRooms}
              disabled={!isConnected}
            >
              🔄 Refresh
            </Button>
          </div>

          {/* Room List */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">
                Available Rooms ({rooms.length})
              </h2>
            </div>

            <div className="divide-y divide-gray-200">
              {rooms.length === 0 ? (
                <div className="px-6 py-12 text-center text-gray-500">
                  <p className="text-lg mb-2">No rooms available</p>
                  <p className="text-sm">Create a new room to start playing!</p>
                </div>
              ) : (
                rooms.map((room) => (
                  <div key={room.room_id || room.id} className="px-6 py-4 hover:bg-gray-50">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3">
                          <h3 className="font-medium text-gray-900">
                            Room {room.room_id || room.id}
                          </h3>
                          <span className="text-sm text-gray-500">
                            {getRoomStatusText(room)}
                          </span>
                        </div>
                        
                        {room.players && room.players.length > 0 && (
                          <div className="mt-2 flex flex-wrap gap-2">
                            {room.players.filter(player => player !== null).map((player, index) => (
                              <span
                                key={index}
                                className="inline-flex items-center px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full"
                              >
                                {player.is_bot ? '🤖' : '👤'} {player.name}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>

                      <div className="ml-4">
                        {canJoinRoom(room) ? (
                          <Button
                            size="sm"
                            onClick={() => joinRoom(room.room_id || room.id)}
                            disabled={!isConnected}
                          >
                            Join
                          </Button>
                        ) : (
                          <Button
                            size="sm"
                            variant="ghost"
                            disabled
                          >
                            {room.status === 'playing' ? 'In Game' : 'Full'}
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Connection status */}
          {!isConnected && (
            <div className="mt-8 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-center">
                <span className="text-yellow-600 mr-2">⚠️</span>
                <p className="text-yellow-800">
                  {isConnecting ? 'Connecting to lobby...' : 'Not connected to lobby'}
                </p>
              </div>
            </div>
          )}
        </div>
      </Layout>


      {/* Join Room Modal */}
      <Modal
        isOpen={showJoinModal}
        onClose={() => setShowJoinModal(false)}
        title="Join Room by ID"
        maxWidth="md"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Room ID
            </label>
            <Input
              type="text"
              value={joinRoomId}
              onChange={(e) => setJoinRoomId(e.target.value)}
              placeholder="Enter room ID..."
              onKeyDown={(e) => {
                if (e.key === 'Enter' && joinRoomId.trim()) {
                  joinRoomById();
                }
              }}
            />
          </div>
          
          <div className="flex justify-end space-x-3">
            <Button
              variant="outline"
              onClick={() => {
                setShowJoinModal(false);
                setJoinRoomId('');
              }}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={joinRoomById}
              disabled={!joinRoomId.trim() || isJoiningRoom}
            >
              {isJoiningRoom ? 'Joining...' : 'Join Room'}
            </Button>
          </div>
        </div>
      </Modal>

      <LoadingOverlay
        isVisible={isCreatingRoom || isJoiningRoom}
        message={isCreatingRoom ? 'Creating room...' : 'Joining room...'}
      />
    </>
  );
};

export default LobbyPage;