import { Container, Text, TextStyle } from "pixi.js";
import { GameButton } from "../components/GameButton.js";
import { GameTextbox } from "../components/GameTextbox.js";
import { createRoom, joinRoom } from "../api.js";

export class LobbyScene extends Container {
  constructor(playerName, onEnterRoom) {
    super();

    console.log("🔵 Entered LobbyScene");

    this.layout = {
      justifyContent: "center",
      alignItems: "center",
      gap: 16,
    };

    const title = new Text({
      text: `👤 Welcome, ${playerName}`,
      style: new TextStyle({
        fill: "#ffffff",
        fontSize: 24,
      }),
    });

    const createBtn = new GameButton({
      label: "Create Room",
      onClick: async () => {
        try {
          const result = await createRoom(playerName);
          console.log("✅ Created room:", result.room_id);
          onEnterRoom(result.room_id); // เปลี่ยน scene ไป RoomScene
        } catch (err) {
          console.error("❌ Failed to create room:", err);
        }
      },
    });

    const roomIdInput = new GameTextbox({ placeholder: "Enter Room ID" });

    const joinBtn = new GameButton({
      label: "Join Room",
      onClick: async () => {
        const roomId = roomIdInput.getText().trim();
        if (!roomId) return;
        try {
          const result = await joinRoom(roomId, playerName);
          console.log("✅ Joined room:", roomId);
          onEnterRoom(roomId); // เปลี่ยน scene ไป RoomScene
        } catch (err) {
          console.error("❌ Failed to join room:", err);
        }
      },
    });

    this.addChild(title, createBtn.view, roomIdInput.view, joinBtn.view);
  }
}
