// frontend/scenes/RoomScene.js
import { Container, Text, TextStyle } from "pixi.js";
import { GameButton } from "../components/GameButton.js";
import { getRoomStateData, assignSlot, startGame } from "../api.js"; // <<< ใช้ new API function >>>
import { GameEvents } from "../SceneFSM.js";
import {
  connect as connectSocket,
  on as onSocketEvent,
  disconnect as disconnectSocket,
  off as offSocketEvent,
  getSocketReadyState,
} from "../socketManager.js";

export class RoomScene extends Container {
  // constructor รับ roomId, playerName และ callback สำหรับการ trigger FSM event
  constructor(roomId, playerName, triggerFSMEvent) {
    super();

    console.log("🔵 Entered RoomScene");

    this.layout = {
      width: "100%",
      flexDirection: "column",
      alignItems: "center",
      padding: 16,
      gap: 16,
    };

    this.roomId = roomId;
    this.playerName = playerName;
    this.triggerFSMEvent = triggerFSMEvent;

    this.slots = ["P1", "P2", "P3", "P4"];
    this.slotLabels = {};
    this.latestSlots = {};
    this.openSlots = [];

    const title = new Text({
      text: `📦 Room ID: ${roomId}`,
      style: new TextStyle({ fill: "#ffffff", fontSize: 22 }),
    });

    const headerRow = new Container();
    headerRow.layout = {
      flexDirection: "row",
      justifyContent: "flex-end",
      alignItems: "center",
      width: "100%",
      height: 30,
    };

    this.playerTable = new Container();
    this.playerTable.layout = {
      flexDirection: "column",
      justifyContent: "center",
      alignItems: "center",
      width: "100%",
    };

    headerRow.addChild(title);
    this.addChild(headerRow, this.playerTable);

    this.renderSlots();
    this.refreshRoomState();
    this.setupWebSocketListeners();

    this.startButton = new GameButton({
      label: "Start Game",
      onClick: async () => {
        try {
          await startGame(this.roomId);
          console.log("🚀 Game started!");
          // เรียก triggerFSMEvent เพื่อแจ้ง FSM ว่าเกมเริ่มแล้ว
          this.triggerFSMEvent(GameEvents.GAME_STARTED);
        } catch (err) {
          console.error("❌ Failed to start game", err);
        }
      },
    });

    this.exitButton = new GameButton({
      label: "Exit",
      onClick: async () => {
        try {
          await fetch(
            `/api/exit-room?room_id=${this.roomId}&name=${this.playerName}`,
            {
              method: "POST",
            }
          );
          // เรียก triggerFSMEvent เพื่อแจ้ง FSM ว่าผู้เล่นออกจากห้องแล้ว
          this.triggerFSMEvent(GameEvents.EXIT_ROOM);
        } catch (err) {
          console.error("❌ Failed to exit", err);
        }
      },
    });

    const footerRow = new Container();
    footerRow.layout = {
      flexDirection: "row",
      justifyContent: "space-between",
      width: "100%",
      height: "auto",
    };

    this.startButton.setEnabled(false); // เริ่มต้นด้วยปุ่ม Start ที่ถูกปิดใช้งาน
    footerRow.addChild(this.exitButton.view, this.startButton.view);
    this.addChild(footerRow);
  }

  async refreshRoomState() {
    try {
      const result = await getRoomStateData(this.roomId);
      if (result && result.slots && result.host_name !== undefined) {
        this.isHost = result.host_name === this.playerName;
        this.updateSlotViews(result.slots);
      } else {
        console.error("ได้รับข้อมูลที่ไม่คาดคิดจาก getRoomStateData:", result);
        alert(
          "Room state invalid or room may have been closed. Returning to Lobby."
        );
        this.triggerFSMEvent(GameEvents.EXIT_ROOM);
      }
    } catch (err) {
      console.error("❌ ล้มเหลวในการดึงสถานะห้อง:", err);
      alert(
        `Error fetching room state: ${
          err.message || "Unknown error"
        }. Returning to Lobby.`
      );
      this.triggerFSMEvent(GameEvents.EXIT_ROOM);
    }
  }

  // renderSlots() - โค้ดเดิม: สร้าง Container และ Text/Button elements
  // ไม่มีการเปลี่ยนแปลงใน logic การสร้าง แต่สำคัญที่ต้องเรียกก่อน updateSlotViews
  renderSlots() {
    for (const slot of this.slots) {
      const row = new Container();
      row.layout = {
        flexDirection: "row",
        alignItems: "center",
        justifyContent: "flex-end",
        width: "100%",
        padding: 10,
      };

      const slotText = new Text({
        text: `${slot}: ...`, // ข้อความเริ่มต้น
        style: new TextStyle({ fill: "#ffffff", fontSize: 18 }),
      });

      const textContainer = new Container();
      textContainer.layout = {
        alignSelf: "center",
        justifyContent: "flex-start",
        width: "100%",
        height: "100%",
        marginTop: 10,
      };

      const slotBtn = new GameButton({
        label: "Add bot", // Initial label, will be updated by updateSlotViews
        height: 30,
        width: 100,
        onClick: async () => {
          const slotId = slot; // "P1", "P2"
          const slotIndex = parseInt(slotId[1]) - 1; // 0, 1, 2, 3
          const info = this.latestSlots[slotId]; // สถานะปัจจุบันของ slot ที่คลิกจาก Frontend (ก่อนส่ง API)
          console.log(
            `[RoomScene.onClick] Player '${this.playerName}' clicked slot ${slotId} (index ${slotIndex}). Current Frontend Info:`,
            info
          );

          try {
            if (this.isHost) {
              // --- Logic สำหรับ HOST ---
              if (!info) {
                // Slot ว่าง (null) --> HOST กด "Add bot" (เพื่อเพิ่มบอท)
                console.log(
                  `[RoomScene.onClick] Host adding bot to empty slot ${slotId}.`
                );
                await assignSlot(
                  this.roomId,
                  `Bot ${slotIndex + 1}`,
                  slotIndex
                );
              } else if (info.is_bot) {
                // Slot เป็น Bot --> HOST กด "Open" (เพื่อทำให้ว่าง)
                console.log(
                  `[RoomScene.onClick] Host opening slot ${slotId} from bot.`
                );
                await assignSlot(this.roomId, null, slotIndex); // ทำให้ slot ว่าง
              } else if (info.name && info.name !== this.playerName) {
                // Slot มีผู้เล่นอื่น --> HOST กด "Add bot" (เพื่อเตะผู้เล่นคนนั้น)
                console.log(
                  `[RoomScene.onClick] Host kicking player '${info.name}' from slot ${slotId} and replacing with Bot.`
                );
                await assignSlot(
                  this.roomId,
                  `Bot ${slotIndex + 1}`,
                  slotIndex
                );
              } else {
                console.warn(
                  `[RoomScene.onClick] Host clicked on unexpected slot state for action. Info:`,
                  info
                );
                return;
              }
            } else {
              // --- Logic สำหรับ PLAYER (ไม่ใช่ Host) ---
              if (!info) {
                // Slot ว่าง (Player กด "Join")
                console.log(
                  `[RoomScene.onClick] Player '${this.playerName}' attempting to join empty slot ${slotId}.`
                );
                await assignSlot(this.roomId, this.playerName, slotIndex);
              } else {
                console.warn(
                  `[RoomScene.onClick] Player clicked on non-empty slot:`,
                  info
                );
                return;
              }
            }

            console.log(
              `[RoomScene.onClick] assignSlot API call sent for slot ${slotIndex}.`
            );
            // ✅ เพิ่มการเรียก getRoomStateData ทันทีหลัง assignSlot เพื่อ Debug
            const serverStateAfterClick = await getRoomStateData(this.roomId);
            console.log(
              "[RoomScene.onClick] Server State AFTER API Call (for Debug):",
              serverStateAfterClick
            );

            console.log(`[RoomScene.onClick] Awaiting WS update...`);
          } catch (err) {
            console.error("❌ [RoomScene.onClick] Failed to toggle slot", err);
            alert(`Failed to change slot: ${err.message || err.detail}`);
          }
        },
      });

      textContainer.addChild(slotText);
      const btnContainer = new Container();
      btnContainer.layout = {
        alignItems: "center",
        justifyContent: "flex-end",
        width: "100%",
        height: 40,
      };
      btnContainer.addChild(slotBtn.view);

      row.addChild(textContainer, btnContainer);

      this.slotLabels[slot] = { label: slotText, joinBtn: slotBtn };
      this.playerTable.addChild(row);
    }
  }

  updateSlotViews(slots) {
    console.log(
      "[RoomScene.updateSlotViews] Called with new slots data:",
      slots
    );
    console.log("[RoomScene.updateSlotViews] Current isHost:", this.isHost);
    this.latestSlots = slots;

    for (const slot of this.slots) {
      const info = slots[slot];
      const { label, joinBtn } = this.slotLabels[slot];
      console.log(
        `[RoomScene.updateSlotViews] Processing slot ${slot}. Info:`,
        info
      );

      if (!info) {
        // Slot ว่าง (null)
        if (this.isHost) {
          label.text = `${slot}: (Open)`; // Host เห็นว่าเปิด (ว่าง)
          joinBtn.setText("Add bot"); // Host สามารถ "Add bot"
          joinBtn.view.visible = true;
          console.log(
            `  - Slot ${slot} (empty), Host view: label='(Open)', btn='Add bot', visible=true`
          );
        } else {
          label.text = `${slot}: Open`; // Player เห็นว่าเปิด (ว่าง)
          joinBtn.setText("Join"); // Player สามารถ "Join"
          joinBtn.view.visible = true;
          // ✅ กำหนด onClick ใหม่สำหรับปุ่ม "Join" ของ Player
          joinBtn.onClick = async () => {
            try {
              console.log(
                `[RoomScene.onClick] Player '${this.playerName}' attempting to join open slot ${slot}.`
              );
              await assignSlot(
                this.roomId,
                this.playerName,
                parseInt(slot[1]) - 1
              );
            } catch (err) {
              console.error("❌ [RoomScene.onClick] Failed to join slot", err);
              alert(`Failed to join slot: ${err.message || err.detail}`);
            }
          };
          console.log(
            `  - Slot ${slot} (empty), Player view: label='Open', btn='Join', visible=true`
          );
        }
      } else if (info.is_bot) {
        // Slot มี Bot
        label.text = `${slot}: 🤖 ${info.name}`; // แสดงชื่อบอทจริงๆ (Bot 2, Bot 3)
        if (this.isHost) {
          joinBtn.setText("Open"); // Host กดแล้ว Slot นี้จะว่าง (Open)
          joinBtn.view.visible = true;
          // ✅ กำหนด onClick ใหม่สำหรับปุ่ม "Open" ของ Host ที่ Bot
          joinBtn.onClick = async () => {
            try {
              console.log(
                `[RoomScene.onClick] Host attempting to open slot ${slot} from Bot ${info.name}.`
              );
              await assignSlot(this.roomId, null, parseInt(slot[1]) - 1); // ทำให้ slot ว่าง
            } catch (err) {
              console.error(
                "❌ [RoomScene.onClick] Failed to open slot from bot",
                err
              );
              alert(`Failed to open slot: ${err.message || err.detail}`);
            }
          };
        } else {
          joinBtn.view.visible = false; // Player ไม่เห็นปุ่ม
        }
        console.log(
          `  - Slot ${slot} (bot), Host view (${this.isHost}): label='🤖 ${
            info.name
          }', btn='Open' (if Host), visible=${this.isHost ? "true" : "false"}`
        );
      } else if (info.name === this.playerName) {
        // Slot คือเราเอง
        label.text = `${slot}: ${info.name} <<`;
        joinBtn.view.visible = false; // ไม่มีปุ่มสำหรับตัวเอง
        console.log(
          `  - Slot ${slot} (self), Host view (${this.isHost}): label='<<', btn visible=false`
        );
      } else {
        // Slot มีผู้เล่นอื่น
        label.text = `${slot}: ${info.name}`;
        if (this.isHost) {
          joinBtn.setText("Add bot"); // Host สามารถ "Add bot" (เพื่อเตะผู้เล่นคนนั้น)
          joinBtn.view.visible = true;
          // ✅ กำหนด onClick ใหม่สำหรับปุ่ม "Add bot" ของ Host ที่ผู้เล่นอื่น
          joinBtn.onClick = async () => {
            try {
              console.log(
                `[RoomScene.onClick] Host attempting to kick player '${info.name}' from slot ${slot} and replace with Bot.`
              );
              await assignSlot(
                this.roomId,
                `Bot ${parseInt(slot[1])}`,
                parseInt(slot[1]) - 1
              ); // ใช้ Slot Index เดิมสำหรับชื่อบอท
            } catch (err) {
              console.error(
                "❌ [RoomScene.onClick] Failed to kick player",
                err
              );
              alert(`Failed to kick player: ${err.message || err.detail}`);
            }
          };
        } else {
          joinBtn.view.visible = false; // Player ไม่เห็นปุ่ม
        }
        console.log(
          `  - Slot ${slot} (other player), Host view (${
            this.isHost
          }): label='${info.name}', btn='Add bot' (if Host), visible=${
            this.isHost ? "true" : "false"
          }`
        );
      }
    }

    // ปุ่ม Start Game: แสดงและเปิดใช้งานเฉพาะ Host และเมื่อทุกช่องถูกเติมเต็ม
    const isReady = Object.values(slots).every(
      (info) => info && (info.is_bot || info.name)
    );
    this.startButton.setEnabled(isReady);
    this.startButton.view.visible = this.isHost;
  }

  // เมธอดสำหรับตั้งค่า WebSocket Listeners
  setupWebSocketListeners() {
    // เชื่อมต่อ WebSocket เมื่อเข้า RoomScene
    connectSocket(this.roomId);

    // ลงทะเบียน Listener สำหรับเหตุการณ์ 'room_state_update'
    this.handleRoomStateUpdate = (data) => {
      console.log("[RoomScene.handleRoomStateUpdate] Received data:", data); // ต้องเห็น
      this.isHost = data.host_name === this.playerName;
      console.log(
        `[RoomScene.handleRoomStateUpdate] isHost: ${this.isHost}, playerName: ${this.playerName}, host_name from data: ${data.host_name}`
      ); // ต้องเห็น
      this.updateSlotViews(data.slots);
      console.log("[RoomScene.handleRoomStateUpdate] updateSlotViews called.");
    };

    onSocketEvent("room_state_update", this.handleRoomStateUpdate);

    // ลงทะเบียน Listener สำหรับเหตุการณ์ 'room_closed' (ถ้า host ออกจากห้อง)
    this.handleRoomClosed = (data) => {
      console.log("WS: Received room_closed", data);
      alert(data.message); // แจ้งผู้เล่นว่าห้องปิด
      this.triggerFSMEvent(GameEvents.EXIT_ROOM); // กลับไป LobbyScene
    };
    onSocketEvent("room_closed", this.handleRoomClosed);

    // ลงทะเบียน Listener สำหรับ 'player_left' (ถ้ามีใครออกจากห้อง)
    this.handlePlayerLeft = (data) => {
      console.log("WS: Player left:", data.player);
      // เนื่องจาก room_state_update ก็จะถูกส่งพร้อมกันอยู่แล้ว, event นี้อาจจะแค่ logging
      // หรือใช้แสดง notification ในเกม
    };
    onSocketEvent("player_left", this.handlePlayerLeft);
  }

  // เมธอดสำหรับลบ WebSocket Listeners (สำคัญมากสำหรับการ Clean-up)
  // ควรเรียกเมธอดนี้เมื่อ Scene ถูกทำลาย หรือเมื่อออกจาก Scene
  teardownWebSocketListeners() {
    offSocketEvent("room_state_update", this.handleRoomStateUpdate);
    offSocketEvent("room_closed", this.handleRoomClosed);
    offSocketEvent("player_left", this.handlePlayerLeft);
    disconnectSocket(); // ปิดการเชื่อมต่อ WebSocket
  }

  // Override destroy method ของ PixiJS Container เพื่อ Clean-up
  destroy(options) {
    this.teardownWebSocketListeners();
    super.destroy(options);
  }
}
