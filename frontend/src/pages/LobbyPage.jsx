// frontend/src/pages/LobbyPage.jsx

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../contexts/AppContext';
import { useSocket } from '../hooks/useSocket';
import { Layout, Button, Input, Modal, LoadingOverlay } from '../components';

const LobbyPage = () => {
  console.log('LobbyPage component re-rendering');
  const navigate = useNavigate();
  const app = useApp();
  const socket = useSocket('lobby'); // Connect to lobby socket
  
  // Debug logging for socket state
  useEffect(() => {
    console.log('Socket state:', {
      isConnected: socket.isConnected,
      isConnecting: socket.isConnecting,
      connectionError: socket.connectionError
    });
  }, [socket.isConnected, socket.isConnecting, socket.connectionError]);
  
  const [rooms, setRooms] = useState([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  
  // Debug logging for modal state
  useEffect(() => {
    console.log('showCreateModal changed to:', showCreateModal);
  }, [showCreateModal]);
  const [showJoinModal, setShowJoinModal] = useState(false);
  const [isCreatingRoom, setIsCreatingRoom] = useState(false);
  const [isJoiningRoom, setIsJoiningRoom] = useState(false);
  const [joinRoomId, setJoinRoomId] = useState('');

  // Set up socket event listeners
  useEffect(() => {
    console.log('Setting up socket event listeners, connected:', socket.isConnected);
    if (!socket.isConnected) return;

    const unsubscribers = [];

    // Room list updates
    const unsubRoomList = socket.on('room_list', (data) => {
      console.log('Received room_list:', data);
      setRooms(data.rooms || []);
    });
    unsubscribers.push(unsubRoomList);

    // Room created successfully
    const unsubRoomCreated = socket.on('room_created', (data) => {
      console.log('Received room_created:', data);
      setIsCreatingRoom(false);
      setShowCreateModal(false);
      app.goToRoom(data.room_id);
      navigate(`/room/${data.room_id}`);
    });
    unsubscribers.push(unsubRoomCreated);

    // Room joined successfully
    const unsubRoomJoined = socket.on('room_joined', (data) => {
      setIsJoiningRoom(false);
      setShowJoinModal(false);
      app.goToRoom(data.room_id);
      navigate(`/room/${data.room_id}`);
    });
    unsubscribers.push(unsubRoomJoined);

    // Error handling
    const unsubError = socket.on('error', (data) => {
      setIsCreatingRoom(false);
      setIsJoiningRoom(false);
      console.error('Lobby error:', data);
      alert(data.message || 'An error occurred');
    });
    unsubscribers.push(unsubError);

    // Request initial room list
    socket.send('get_rooms');

    // Cleanup
    return () => {
      console.log('Cleaning up socket event listeners');
      unsubscribers.forEach(unsub => unsub());
    };
  }, [socket.isConnected]); // Removed app and navigate from dependencies

  // Refresh room list
  const refreshRooms = () => {
    if (socket.isConnected) {
      socket.send('get_rooms');
    }
  };

  // Create new room
  const createRoom = () => {
    setIsCreatingRoom(true);
    socket.send('create_room', {
      player_name: app.playerName
    });
  };

  // Join room by ID
  const joinRoomById = () => {
    if (!joinRoomId.trim()) return;
    
    setIsJoiningRoom(true);
    socket.send('join_room', {
      room_id: joinRoomId.trim(),
      player_name: app.playerName
    });
  };

  // Join room from list
  const joinRoom = (roomId) => {
    socket.send('join_room', {
      room_id: roomId,
      player_name: app.playerName
    });
  };

  const getRoomStatusText = (room) => {
    const playerCount = room.players?.length || 0;
    const maxPlayers = 4;
    
    if (room.status === 'playing') {
      return `🎮 In Game (${playerCount}/${maxPlayers})`;
    }
    
    if (playerCount >= maxPlayers) {
      return `🔒 Full (${playerCount}/${maxPlayers})`;
    }
    
    return `⏳ Waiting (${playerCount}/${maxPlayers})`;
  };

  const canJoinRoom = (room) => {
    return room.status === 'waiting' && (room.players?.length || 0) < 4;
  };

  return (
    <>
      <Layout
        title="Game Lobby"
        showConnection={true}
        connectionProps={{
          isConnected: socket.isConnected,
          isConnecting: socket.isConnecting,
          isReconnecting: socket.isReconnecting,
          error: socket.connectionError,
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
                onClick={() => {
                  console.log('Create Room button clicked');
                  console.log('Socket connected:', socket.isConnected);
                  console.log('Current showCreateModal:', showCreateModal);
                  setShowCreateModal(true);
                  console.log('setShowCreateModal(true) called');
                }}
                disabled={!socket.isConnected}
              >
                Create Room
              </Button>
              
              <Button
                variant="outline"
                onClick={() => setShowJoinModal(true)}
                disabled={!socket.isConnected}
              >
                Join by ID
              </Button>
            </div>

            <Button
              variant="ghost"
              onClick={refreshRooms}
              disabled={!socket.isConnected}
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
                  <div key={room.id} className="px-6 py-4 hover:bg-gray-50">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3">
                          <h3 className="font-medium text-gray-900">
                            Room {room.id}
                          </h3>
                          <span className="text-sm text-gray-500">
                            {getRoomStatusText(room)}
                          </span>
                        </div>
                        
                        {room.players && room.players.length > 0 && (
                          <div className="mt-2 flex flex-wrap gap-2">
                            {room.players.map((player, index) => (
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
                            onClick={() => joinRoom(room.id)}
                            disabled={!socket.isConnected}
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
          {!socket.isConnected && (
            <div className="mt-8 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-center">
                <span className="text-yellow-600 mr-2">⚠️</span>
                <p className="text-yellow-800">
                  {socket.isConnecting ? 'Connecting to lobby...' : 'Not connected to lobby'}
                </p>
              </div>
            </div>
          )}
        </div>
      </Layout>

      {/* SIMPLE MODAL TEST */}
      {showCreateModal && (
        <div 
          className="fixed inset-0 flex items-center justify-center"
          style={{ 
            backgroundColor: 'rgba(255, 0, 0, 0.8)', // Bright red background 
            zIndex: 999999,
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0
          }}
          onClick={() => {
            console.log('🔍 DEBUG: Modal overlay clicked, closing modal');
            setShowCreateModal(false);
          }}
        >
          <div 
            style={{
              backgroundColor: 'white',
              padding: '20px',
              borderRadius: '8px',
              border: '5px solid blue', // Obvious blue border
              maxWidth: '400px',
              width: '90%'
            }}
            onClick={(e) => {
              console.log('🔍 DEBUG: Modal content clicked, preventing close');
              e.stopPropagation();
            }}
          >
            <h2 style={{ fontSize: '24px', marginBottom: '20px', color: 'red' }}>
              🚨 TEST MODAL - Create New Room
            </h2>
            <p style={{ marginBottom: '20px' }}>
              This is a test modal with obvious styling. If you can see this, the modal is working!
            </p>
            <button 
              style={{ 
                background: 'green', 
                color: 'white', 
                padding: '10px 20px', 
                border: 'none', 
                borderRadius: '4px',
                marginRight: '10px'
              }}
              onClick={() => {
                console.log('🔍 DEBUG: Create Room clicked');
                createRoom();
              }}
            >
              CREATE ROOM
            </button>
            <button 
              style={{ 
                background: 'red', 
                color: 'white', 
                padding: '10px 20px', 
                border: 'none', 
                borderRadius: '4px' 
              }}
              onClick={() => {
                console.log('🔍 DEBUG: Cancel clicked');
                setShowCreateModal(false);
              }}
            >
              CANCEL
            </button>
          </div>
        </div>
      )}

      {/* Join Room Modal - Temporarily Removed for Debugging */}

      <LoadingOverlay
        isVisible={isCreatingRoom || isJoiningRoom}
        message={isCreatingRoom ? 'Creating room...' : 'Joining room...'}
      />
    </>
  );
};

export default LobbyPage;