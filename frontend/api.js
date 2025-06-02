// frontend/api.js

console.log("📡 API module loaded");


export async function createRoom(name) {
  const res = await fetch(`/api/create-room?name=${encodeURIComponent(name)}`, {
    method: 'POST',
  });
  const text = await res.text();
  try {
    // ✅ ตรงนี้จะได้รับ { room_id: "...", host_name: "..." }
    return JSON.parse(text);
  } catch (err) {
    console.error("❌ Failed to parse JSON:", text);
    throw err;
  }
}


export async function listRooms() {
  const res = await fetch(`/api/list-rooms`);
  return res.json();
}

export async function joinRoom(roomId, name) {
  const res = await fetch(`/api/join-room?room_id=${roomId}&name=${name}`, {
    method: 'POST',
  });
  return res.json();
}


export async function startGame(roomId) {
  const res = await fetch(`/api/start-game?room_id=${roomId}`, { method: 'POST' });
  return res.json();
}

export async function assignSlot(roomId, name, slot) {
  const res = await fetch(`/api/assign-slot?room_id=${roomId}&name=${name}&slot=${slot}`, {
    method: 'POST',
  });
  return res.json();
}

export async function getRoomStateData(roomId) { // เปลี่ยนชื่อจาก getRoomState เพื่อหลีกเลี่ยงความสับสน
  const res = await fetch(`/api/get-room-state?room_id=${roomId}`);
  const text = await res.text();
  try {
    // จะคืนค่า { room_id: "...", host_name: "...", slots: {...}, started: false }
    return JSON.parse(text);
  } catch (err) {
    console.error("❌ Failed to parse JSON for getRoomStateData:", text);
    throw err;
  }
}