// game-ui.js

import * as PIXI from "pixi.js";

const BACKEND = location.hostname === "localhost" ? "http://localhost:5050" : "";

const app = new PIXI.Application({ width: 800, height: 600, backgroundColor: 0x202020 });
document.body.appendChild(app.view);

// Global State
const state = {
  playerName: null,
  roomId: null,
  playerSlot: null,
  isHost: false,
  socket: null,
};

// --- Utils ---
function cleanup() {
  app.stage.removeChildren();
  document.querySelectorAll("input").forEach((el) => el.remove());
  if (state.socket) {
    state.socket.close();
    state.socket = null;
  }
}

function createInput(x, y, placeholder) {
  const input = document.createElement("input");
  input.placeholder = placeholder;
  input.style.position = "absolute";
  input.style.left = `${x}px`;
  input.style.top = `${y}px`;
  document.body.appendChild(input);
  return input;
}

function createButton(text, x, y, onClick) {
  const btn = new PIXI.Text(text, { fontSize: 20, fill: 0xffffff });
  btn.position.set(x, y);
  btn.interactive = true;
  btn.buttonMode = true;
  btn.on("pointerdown", onClick);
  app.stage.addChild(btn);
  return btn;
}

// --- Screens ---
function showStartScreen() {
  cleanup();

  const title = new PIXI.Text("Enter your name:", { fontSize: 28, fill: 0xffffff });
  title.position.set(100, 80);
  app.stage.addChild(title);

  const nameInput = createInput(100, 130, "Your name");
  createButton("Start", 100, 180, async () => {
    if (nameInput.value.trim()) {
      state.playerName = nameInput.value.trim();
      showLobbyScreen();
    }
  });
}

async function showLobbyScreen() {
  cleanup();

  const res = await fetch(`${BACKEND}/list-rooms`);
  if (!res.ok) {
    console.error("Failed to load room list");
    return;
  }
  const { rooms } = await res.json();

  const title = new PIXI.Text("Game Lobby", { fontSize: 28, fill: 0xffffff });
  title.position.set(100, 50);
  app.stage.addChild(title);

  rooms.forEach((room, i) => {
    createButton(`Join: ${room.name}`, 100, 100 + i * 40, async () => {
      state.roomId = room.room_id;
      state.isHost = false;
      showRoomScreen();
    });
  });

  createButton("Create Room", 100, 100 + rooms.length * 40 + 20, async () => {
    const res = await fetch(`${BACKEND}/create-room?name=${state.playerName}`, { method: "POST" });
    if (!res.ok) {
      console.error("Failed to create room:", await res.text());
      return;
    }
    const { room_id } = await res.json();
    state.roomId = room_id;
    state.isHost = true;
    showRoomScreen();
  });
}

async function showRoomScreen() {
  cleanup();

  const res = await fetch(`${BACKEND}/join-room?room_id=${state.roomId}&name=${state.playerName}`, { method: "POST" });
  if (!res.ok) {
    console.error("Failed to join room:", await res.text());
    return;
  }
  const { slots } = await res.json();

  const title = new PIXI.Text(`Room: ${state.roomId}`, { fontSize: 24, fill: 0xffffff });
  title.position.set(100, 50);
  app.stage.addChild(title);

  slots.forEach((slot, i) => {
    const label = slot ? `${slot}` : `[Open Slot ${i}]`;
    createButton(label, 100, 100 + i * 40, async () => {
      if (!slot) {
        const assignRes = await fetch(`${BACKEND}/assign-slot?room_id=${state.roomId}&name=${state.playerName}&slot=${i}`, {
          method: "POST",
        });
        if (!assignRes.ok) {
          console.error("Failed to assign slot:", await assignRes.text());
          return;
        }
        state.playerSlot = i;
        if (state.isHost) {
          createButton("Enable Bot", 300, 100 + i * 40, async () => {
            await fetch(`${BACKEND}/set-bot?room_id=${state.roomId}&slot=${i}`, { method: "POST" });
            showRoomScreen();
          });
        }
      }
    });
  });

  if (state.isHost) {
    createButton("Start Game", 100, 300, async () => {
      const startRes = await fetch(`${BACKEND}/start-game?room_id=${state.roomId}`, { method: "POST" });
      if (!startRes.ok) {
        console.error("Failed to start game:", await startRes.text());
        return;
      }
      connectSocket();
    });
  } else {
    connectSocket();
  }
}

// --- WebSocket Events ---
function connectSocket() {
  const socket = new WebSocket(`ws://${location.host}/ws/${state.roomId}`);
  state.socket = socket;

  socket.onopen = () => console.log("WebSocket connected");
  socket.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    const { event: evt, data } = msg;
    if (evt === "start_game") {
      showGameScreen();
    }
    // TODO: handle declare, play, score
  };

  socket.onclose = () => console.log("WebSocket disconnected");
}

function showGameScreen() {
  cleanup();
  const msg = new PIXI.Text("Game Started!", { fontSize: 30, fill: 0x00ff00 });
  msg.position.set(100, 100);
  app.stage.addChild(msg);
}

// --- Entry ---
showStartScreen();
