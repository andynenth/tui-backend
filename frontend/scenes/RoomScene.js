// frontend/scenes/RoomScene.js

import { Container, Text, TextStyle } from "pixi.js";
import { GameButton } from "../components/GameButton.js";
import { getRoomState, assignSlot, startGame } from "../api.js";

export class RoomScene extends Container {
  constructor(roomId, playerName, onGameStart, sceneManager) {
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
    this.sceneManager = sceneManager;

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
        //   location.reload(); // หรือ 
          this.sceneManager.gotoScene('LobbyScene');

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

    this.startButton.setEnabled(false);
    footerRow.addChild(this.exitButton.view, this.startButton.view);

    this.addChild(footerRow);
  }

  async refreshRoomState() {
    try {
      const result = await getRoomState(this.roomId, this.playerName);
      const slots = result.slots;
      this.isHost = result.host_name === this.playerName;
      this.updateSlotViews(slots);
    } catch (err) {
      console.error("❌ Failed to fetch room state:", err);
    }
  }

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
        text: `${slot}: ...`,
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
        label: "Action", // will be changed dynamically
        height: 30,
        width: 100,
        onClick: async () => {
          const slotIndex = parseInt(slot[1]) - 1;
          try {
            // toggle slot: if bot → open, if open → add bot
            const info = this.latestSlots[slot]; // use latest fetched data
            if (info?.is_bot) {
              await assignSlot(this.roomId, null, slotIndex); // open
            } else {
              await assignSlot(this.roomId, `Bot ${slotIndex + 1}`, slotIndex); // add bot
            }
            this.refreshRoomState();
          } catch (err) {
            console.error("❌ Failed to toggle slot", err);
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
      //   btnContainer.removeChild(slotBtn.view);

      row.addChild(textContainer, btnContainer);

      this.slotLabels[slot] = { label: slotText, joinBtn: slotBtn };
      this.playerTable.addChild(row);
    }
  }

  updateSlotViews(slots) {
    this.latestSlots = slots; // 💾 save for use in slotBtn toggle

    let mySlot = null;

    for (const slot of this.slots) {
      const info = slots[slot];
      const { label, joinBtn } = this.slotLabels[slot];

      if (!info) {
        // empty
        label.text = `${slot}: (empty)`;
        joinBtn.setText("Add bot");
        joinBtn.view.visible = this.isHost;
      } else if (info.is_bot) {
        // bot
        label.text = `${slot}: 🤖 Bot`;
        joinBtn.setText("Open");
        joinBtn.view.visible = this.isHost;
      } else if (info.name === this.playerName) {
        // myself
        label.text = `${slot}: ${info.name} <<`;
        joinBtn.view.visible = false;
        mySlot = slot;
      } else {
        // other player
        label.text = `${slot}: ${info.name}`;
        joinBtn.setText("Add bot");
        joinBtn.view.visible = this.isHost;
      }
    }

    // ✅ ปุ่ม Start
    const isReady = Object.values(slots).every(
      (info) => info && (info.is_bot || info.name)
    );
    this.startButton.setEnabled(isReady);
    this.startButton.view.visible = this.isHost;
  }
}
