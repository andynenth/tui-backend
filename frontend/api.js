// frontend/api.js
export async function createRoom(name) {
  const res = await fetch(`/api/create-room?name=${encodeURIComponent(name)}`);
  return res.json();
}

export async function listRooms() {
  const res = await fetch(`/api/list-rooms`);
  return res.json();
}

export async function joinRoom(roomId, name) {
  const res = await fetch(`/api/join-room?room_id=${roomId}&name=${name}`);
  return res.json();
}

export async function startGame(roomId) {
  const res = await fetch(`/api/start-game?room_id=${roomId}`, { method: 'POST' });
  return res.json();
}
