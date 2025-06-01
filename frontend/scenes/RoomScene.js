import { Container, Text, TextStyle } from "pixi.js";
import { GameButton } from "../components/GameButton.js";
import { getRoomState, assignSlot, startGame } from "../api.js";

export class RoomScene extends Container {
  constructor(roomId, playerName, onGameStart) {
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
    this.onGameStart = onGameStart;

    this.slots = ["P1", "P2", "P3", "P4"];
    this.slotLabels = {};

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

    this.startButton = new GameButton({
      label: "Start Game",
      onClick: async () => {
        try {
          await startGame(this.roomId);
          console.log("🚀 Game started!");
          this.onGameStart(); // เรียกเมื่อเริ่มเกมแล้ว
        } catch (err) {
          console.error("❌ Failed to start game", err);
        }
      },
    });

    this.startButton.visible = false;
    this.addChild(this.startButton.view);
  }

  async refreshRoomState() {
    try {
      const result = await getRoomState(this.roomId, this.playerName);
      const slots = result.slots;
      this.updateSlotViews(slots);
    } catch (err) {
      console.error("❌ Failed to fetch room state:", err);
    }
  }

  renderSlots() {
    for (const slot of this.slots) {
      // 🧱 สร้าง container สำหรับแถวนี้
      const row = new Container();
      row.layout = {
        flexDirection: "row",
        alignItems: "center",
        justifyContent: "flex-end", // หรือ center, flex-start แล้วแต่ต้องการ
        width: "100%",
        margin: 10,
      };

      const label = new Text({
        text: `${slot}: ...`,
        style: new TextStyle({ fill: "#ffffff", fontSize: 18 }),
      });

      const joinBtn = new GameButton({
        label: "Join",
        height:30,
        width:90,
        onClick: async () => {
          try {
            await assignSlot(
              this.roomId,
              this.playerName,
              parseInt(slot[1]) - 1
            );
            this.refreshRoomState();
          } catch (err) {
            console.error("❌ Failed to join slot", slot, err);
          }
        },
      });

      // 🧩 ใส่ label กับปุ่มเข้า container แถวนี้
      row.addChild(label, joinBtn.view);

      // 🧷 เก็บ reference เพื่อ update ทีหลัง
      this.slotLabels[slot] = { label, joinBtn };

      // 📌 ใส่เข้า scene หลัก
      this.playerTable.addChild(row);
    }
  }

  updateSlotViews(slots) {
    let mySlot = null;

    for (const slot of this.slots) {
      const info = slots[slot];
      const { label, joinBtn } = this.slotLabels[slot];

      if (info) {
        label.text = `${slot}: ${info.name}${info.is_bot ? " 🤖" : ""}`;
        joinBtn.view.visible = false;

        if (info.name === this.playerName) {
          mySlot = slot;
        }
      } else {
        label.text = `${slot}: (empty)`;
        joinBtn.view.visible = true;
      }
    }

    this.startButton.visible = mySlot === "P1";
  }
}
