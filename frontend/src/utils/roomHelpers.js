// Utility functions for consistent room and player display

export const getBotName = (slotNumber) => {
  // Ensure consistent bot naming
  return `Bot ${slotNumber}`;
};

export const getRoomStatusText = (occupancy, maxPlayers = 4) => {
  if (occupancy === maxPlayers) {
    return 'All players ready - Start the game!';
  }
  return 'Waiting for players to join';
};

export const getPlayerDisplayName = (player, slotNumber) => {
  if (!player) return 'Waiting...';
  if (player.is_bot) return getBotName(slotNumber);
  return player.name;
};

export const getRoomOccupancyText = (room) => {
  const playerCount = room.players?.filter(p => p !== null).length || 0;
  const maxPlayers = room.total_slots || 4;
  
  if (room.started || room.status === 'playing') {
    return `🎮 In Game (${playerCount}/${maxPlayers})`;
  }
  
  if (playerCount >= maxPlayers) {
    return `🔒 Full (${playerCount}/${maxPlayers})`;
  }
  
  return `⏳ Waiting (${playerCount}/${maxPlayers})`;
};

export const canJoinRoom = (room) => {
  const playerCount = room.players?.filter(p => p !== null).length || 0;
  const maxPlayers = room.total_slots || 4;
  
  return !room.started && playerCount < maxPlayers;
};