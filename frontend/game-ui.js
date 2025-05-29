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
  dropdowns: [], // ✅ ใหม่
};

// --- Utils ---
function cleanup() {
  console.log("🧹 Running cleanup(), removing", state.dropdowns.length, "dropdowns");

  app.stage.removeChildren();
  document.querySelectorAll("input").forEach((el) => el.remove());

  // ✅ ลบ dropdowns ที่เคยสร้างไว้
  if (state.dropdowns) {
    state.dropdowns.forEach((el) => el.remove());
    state.dropdowns = [];
  }

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
  const btn = new PIXI.Text(text, {
    fontSize: 20,
    fill: 0xffffff,
    fontFamily: "Arial",
  });
  btn.position.set(x, y);
  btn.interactive = true;
  btn.buttonMode = true;
  btn.on("pointerdown", onClick);
  return btn;
}

function createInputFromPixiPos(pixiObject, offsetY = 0, placeholder = "") {
  const global = pixiObject.getGlobalPosition();
  const input = document.createElement("input");
  input.placeholder = placeholder;
  input.style.position = "absolute";
  input.style.left = `${app.view.getBoundingClientRect().left + global.x}px`;
  input.style.top = `${app.view.getBoundingClientRect().top + global.y + offsetY}px`;
  document.body.appendChild(input);
  return input;
}

function createSlotDropdown(x, y, slotIndex, currentValue = "Open") {
  console.log("🟡 Creating dropdown at", x, y, "for slot", slotIndex);

  const select = document.createElement("select");
  select.style.position = "absolute";
  select.style.left = `${x}px`;
  select.style.top = `${y}px`;

  ["Open", "Bot"].forEach((optionText) => {
    const option = document.createElement("option");
    option.value = optionText;
    option.textContent = optionText;
    if (optionText === currentValue) option.selected = true;
    select.appendChild(option);
  });

  select.onchange = () => {
    if (select.value === "Bot") {
      // delay เพื่อให้ dropdown ปิดก่อน
      setTimeout(async () => {
        await fetch(`${BACKEND}/set-bot?room_id=${state.roomId}&slot=${slotIndex}`, { method: "POST" });
        showRoomScreen();
      }, 100); // รอให้ dropdown ปิดก่อนล้าง DOM
    }
  };


  document.body.appendChild(select);
  state.dropdowns.push(select); // ✅ เก็บไว้เพื่อให้ cleanup ลบเฉพาะ dropdown ของรอบล่าสุด
  return select;
}


// --- Screens ---
function showStartScreen() {
  cleanup();

  const container = new PIXI.Container();
  container.position.set(100, 100);
  app.stage.addChild(container);

  const title = new PIXI.Text("Enter your name:", { fontSize: 28, fill: 0xffffff });
  container.addChild(title);

  const nameInput = createInputFromPixiPos(title, 40, "Your name");

  const startButton = createButton("Start", 0, 90, async () => {
    if (nameInput.value.trim()) {
      state.playerName = nameInput.value.trim();
      showLobbyScreen();
    }
  });
  container.addChild(startButton);
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
    const label = room.name || room.room_id || `Room ${i}`;
    const joinBtn = createButton(`Join: ${label}`, 100, 100 + i * 40, async () => {
      state.roomId = room.room_id;
      state.isHost = false;
      showRoomScreen();
    });
    app.stage.addChild(joinBtn);
  });

  const y = 100 + rooms.length * 40 + 20;
  const createBtn = createButton("Create Room", 100, y, async () => {
    const res = await fetch(`${BACKEND}/create-room?name=${state.playerName}`, { method: "POST" });
    if (!res.ok) {
      console.error("Failed to create room:", await res.text());
      return;
    }
    const { room_id } = await res.json();
    state.roomId = room_id;
    state.isHost = true;

    // 🧩 Host เข้าสล็อต 0 ทันที
    await fetch(`${BACKEND}/assign-slot?room_id=${room_id}&name=${state.playerName}&slot=0`, {
      method: "POST",
    });
    state.playerSlot = 0;

    showRoomScreen();
  });
  app.stage.addChild(createBtn);
}

async function showRoomScreen() {
  
  cleanup();

  const res = await fetch(`${BACKEND}/join-room?room_id=${state.roomId}&name=${state.playerName}`, { method: "POST" });
  if (!res.ok) {
    console.error("Failed to join room:", await res.text());
    return;
  }
  const { slots } = await res.json();

  console.log("🧩 Slots:", slots);

  const title = new PIXI.Text(`Room: ${state.roomId}`, { fontSize: 24, fill: 0xffffff });
  title.position.set(100, 50);
  app.stage.addChild(title);

  slots.forEach((slot, i) => {
    const label = slot ? `${slot}` : `[Open Slot ${i}]`;
    const slotBtn = createButton(label, 100, 100 + i * 40, async () => {
      if ((slot === "OPEN" || !slot) && !state.isHost) {
        const assignRes = await fetch(`${BACKEND}/assign-slot?room_id=${state.roomId}&name=${state.playerName}&slot=${i}`, {
          method: "POST",
        });
        if (!assignRes.ok) return;
        state.playerSlot = i;
        showRoomScreen();
      }
    });

    app.stage.addChild(slotBtn); // ✅ ต้องอยู่บน stage ก่อน

    if (state.isHost && (slot === "OPEN" || !slot)) {
      const global = slotBtn.getGlobalPosition();
      createSlotDropdown(
        app.view.getBoundingClientRect().left + global.x + 200,
        app.view.getBoundingClientRect().top + global.y,
        i
      );
    }
  });

  if (state.isHost) {
    const startBtn = createButton("Start Game", 100, 300, async () => {
      const startRes = await fetch(`${BACKEND}/start-game?room_id=${state.roomId}`, { method: "POST" });
      if (!startRes.ok) {
        console.error("Failed to start game:", await startRes.text());
        return;
      }
      connectSocket();
    });
    app.stage.addChild(startBtn);
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
