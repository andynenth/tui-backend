// frontend/src/pages/RoomPage.jsx
// Room management page - configure room before starting game

import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useApp } from '../contexts/AppContext';
import { Layout, Button } from '../components';
import { PlayerAvatar } from '../components/game/shared';
import TruncatedName from '../components/shared/TruncatedName';
import { networkService, gameService } from '../services';
// CSS classes are imported globally

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
        // Connect both NetworkService and GameService to the room
        await networkService.connectToRoom(roomId, {
          playerName: app.playerName,
        });
        
        // Also connect GameService so it's ready to receive game_started events
        await gameService.joinRoom(roomId, app.playerName);
        
        if (mounted) {
          setIsConnected(true);
          // Request room state
          networkService.send(roomId, 'get_room_state', { room_id: roomId });
        }
      } catch (error) {
        console.error('Failed to connect to room:', error);
      }
    };

    if (roomId && app.playerName) {
      initializeRoom();
    }

    // Cleanup on unmount
    return () => {
      mounted = false;
      // 🎯 FIX: Don't disconnect when navigating to game page
      // Check if we're navigating to the game page for this room
      const currentPath = window.location.pathname;
      const isNavigatingToGame = currentPath.includes(`/game/${roomId}`);
      
      if (roomId && !isNavigatingToGame) {
        console.log('🏠 RoomPage cleanup: Disconnecting from room (not going to game)');
        networkService.disconnectFromRoom(roomId);
        gameService.leaveRoom();
      } else if (isNavigatingToGame) {
        console.log('🏠 RoomPage cleanup: Keeping connection (navigating to game)');
      }
    };
  }, [roomId, app.playerName]);

  // Event handlers for room updates and game start
  useEffect(() => {
    if (!isConnected) return;

    const handleRoomUpdate = (event) => {
      const eventData = event.detail;
      const roomUpdate = eventData.data;
      console.log('🏠 ROOM_UPDATE: Full data received:', roomUpdate);
      console.log('🏠 ROOM_UPDATE: Players array:', roomUpdate.players);
      console.log(
        '🏠 ROOM_UPDATE: Players array type:',
        typeof roomUpdate.players
      );
      console.log(
        '🏠 ROOM_UPDATE: Players array length:',
        roomUpdate.players?.length
      );
      console.log(
        '🏠 ROOM_UPDATE: Players array entries:',
        Object.entries(roomUpdate.players || {})
      );
      setRoomData(roomUpdate);
    };

    const handleGameStarted = (event) => {
      const eventData = event.detail;
      const gameData = eventData.data;
      console.log('🎮 ROOM: Game started event received, preparing navigation');
      console.log('🎮 ROOM: Game data:', gameData);
      
      // 🎯 FIX: Remove artificial delay and improve synchronization
      // Instead of arbitrary timeout, check if GameService has updated state
      console.log('🎮 ROOM: Game started, checking GameService state before navigation');
      
      // Check if GameService has processed the game_started event
      const currentGameState = gameService.getState();
      console.log('🎮 ROOM: Current GameService state:', currentGameState);
      console.log('🎮 ROOM: GameService phase:', currentGameState.phase);
      
      // Navigate immediately - GamePage will handle state synchronization
      console.log('🎮 ROOM: Navigating to game page');
      navigate(`/game/${roomId}`);
    };

    const handleRoomClosed = (event) => {
      const eventData = event.detail;
      const closeData = eventData.data;
      console.log('🏠 ROOM_CLOSED: Room was closed, navigating to lobby');
      console.log('🏠 ROOM_CLOSED: Reason:', closeData.reason);
      console.log('🏠 ROOM_CLOSED: Message:', closeData.message);

      // Navigate back to lobby when room is closed
      navigate('/lobby');
    };

    const handlePlayerKicked = (event) => {
      const eventData = event.detail;
      const kickData = eventData.data;
      console.log('🚨 PLAYER_KICKED: Received kick message');
      console.log('🚨 PLAYER_KICKED: Reason:', kickData.reason);
      console.log('🚨 PLAYER_KICKED: Removed by:', kickData.removed_by);
      console.log('🚨 PLAYER_KICKED: Removed player name:', kickData.removed_player_name);
      console.log('🚨 PLAYER_KICKED: Current player name:', app.playerName);
      
      // Check if this kick message is for the current player
      if (kickData.removed_player_name === app.playerName) {
        console.log('🚨 PLAYER_KICKED: This player was kicked, navigating to lobby');
        navigate('/lobby');
      } else {
        console.log('🚨 PLAYER_KICKED: Kick message not for this player, ignoring');
      }
    };

    networkService.addEventListener('room_update', handleRoomUpdate);
    networkService.addEventListener('game_started', handleGameStarted);
    networkService.addEventListener('room_closed', handleRoomClosed);
    networkService.addEventListener('player_kicked', handlePlayerKicked);

    return () => {
      networkService.removeEventListener('room_update', handleRoomUpdate);
      networkService.removeEventListener('game_started', handleGameStarted);
      networkService.removeEventListener('room_closed', handleRoomClosed);
      networkService.removeEventListener('player_kicked', handlePlayerKicked);
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

  const removePlayer = (playerId) => {
    console.log('🗑️ REMOVE_PLAYER: Button clicked for player', playerId);
    console.log('🗑️ REMOVE_PLAYER: Sending to room', roomId);
    networkService.send(roomId, 'remove_player', { player_id: playerId });
  };

  const leaveRoom = () => {
    console.log('🚪 LEAVE_ROOM: Button clicked');
    console.log('🚪 LEAVE_ROOM: Player name:', app.playerName);
    console.log('🚪 LEAVE_ROOM: Room ID:', roomId);
    networkService.send(roomId, 'leave_room', {
      player_name: app.playerName,
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
          <Button onClick={() => navigate('/')}>Go to Start Page</Button>
        </div>
      </Layout>
    );
  }

  return (
    <Layout title="" showConnection={false} showHeader={false}>
      <div
        className="min-h-screen flex items-center justify-center"
        style={{ background: 'var(--gradient-gray)' }}
      >
        <div className="rp-gameContainer">
          {/* Connection Status */}
          <div
            className={`connection-status ${!isConnected ? 'disconnected' : ''}`}
          >
            <span className="status-dot"></span>
            {isConnected ? 'Connected' : 'Disconnected'}
          </div>

          {/* Room Header */}
          <div className="rp-roomHeader">
            <h1 className="rp-roomTitle">Game Room</h1>
            <div className="rp-roomIdBadge">
              <span className="rp-roomIdLabel">Room ID:</span>
              <span className="rp-roomIdValue">{roomId}</span>
            </div>
          </div>

          {/* Players Section with Table Visualization */}
          <div className="rp-playersSection">
            <div className="rp-sectionHeader">
              <div className={`rp-playerCount ${isRoomFull ? 'full' : ''}`}>
                {occupiedSlots} / 4
              </div>
            </div>

            {/* Game Table Visualization */}
            <div className="rp-gameTable">
              <div className="rp-tableSurface">
                {/* Wood grain texture layer */}
                <div className="rp-table-wood-grain"></div>

                {/* Player positions around the table */}
                {[1, 2, 3, 4].map((position) => {
                  const player = roomData?.players?.[position - 1];
                  const isEmpty = !player;
                  const isHost = player?.is_host;
                  const isBot = player?.is_bot;
                  const playerName = player
                    ? isBot
                      ? `Bot ${position}`
                      : player.name
                    : 'Waiting...';

                  return (
                    <div
                      key={position}
                      className={`rp-playerSeat rp-position-${position}`}
                    >
                      <div
                        className={`rp-playerCard ${!isEmpty ? 'rp-filled' : 'rp-empty'} ${isHost ? 'rp-host' : ''}`}
                      >
                        <div className="rp-playerInfo">
                          {!isEmpty && (
                            <PlayerAvatar
                              name={playerName}
                              isBot={isBot}
                              size="medium"
                              avatarColor={player?.avatar_color}
                            />
                          )}
                          <TruncatedName
                            name={playerName}
                            className="rp-playerName"
                          />
                        </div>
                        {isHost && <span className="rp-hostBadge">Host</span>}
                        {isEmpty && isCurrentPlayerHost ? (
                          <div className="rp-playerAction">
                            <button
                              className="rp-actionBtn rp-addBotBtn"
                              onClick={() => addBot(position)}
                              disabled={!isConnected}
                            >
                              Add Bot
                            </button>
                          </div>
                        ) : (
                          !isHost &&
                          isCurrentPlayerHost && (
                            <div className="rp-playerAction">
                              <button
                                className="rp-actionBtn rp-removeBtn"
                                onClick={() => removePlayer(player?.player_id)}
                                disabled={!isConnected}
                              >
                                Remove
                              </button>
                            </div>
                          )
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Game Controls */}
          <div className="rp-gameControls">
            <div className={`rp-roomStatus ${isRoomFull ? 'rp-ready' : ''}`}>
              {isRoomFull
                ? 'All players ready!'
                : `Need ${4 - occupiedSlots} more player${4 - occupiedSlots > 1 ? 's' : ''} to start`}
            </div>
            <div className="rp-controlButtons">
              {isCurrentPlayerHost && (
                <button
                  className="rp-controlButton rp-startButton"
                  onClick={startGame}
                  disabled={!isConnected || isStartingGame || !isRoomFull}
                >
                  {isStartingGame ? 'Starting...' : 'Start Game'}
                </button>
              )}
              <button
                className="rp-controlButton rp-leaveButton"
                onClick={leaveRoom}
              >
                Leave Room
              </button>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default RoomPage;
