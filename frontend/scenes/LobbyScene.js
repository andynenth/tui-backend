// frontend/scenes/LobbyScene.js
import { Container, Text, TextStyle } from "pixi.js";
import { GameButton } from "../components/GameButton.js";
import { GameTextbox } from "../components/GameTextbox.js";
import { createRoom, joinRoom, listRooms } from "../api.js";
import { GameEvents } from '../SceneFSM.js'; // นำเข้า GameEvents

export class LobbyScene extends Container {
    // constructor รับ playerName และ callback สำหรับการ trigger FSM event
    constructor(playerName, triggerFSMEvent) {
        super();

        console.log("🔵 Entered LobbyScene");

        this.playerName = playerName;
        this.triggerFSMEvent = triggerFSMEvent; // เก็บ reference

        this.layout = {
            width: "100%",
            flexDirection: "column",
            alignItems: "center",
            padding: 16,
            gap: 16,
        };

        const headerRow = new Container();
        headerRow.layout = {
            flexDirection: "row",
            justifyContent: "flex-end",
            alignItems: "center",
            width: "100%",
        };

        const title = new Text({
            text: `👤 Welcome, ${playerName}`,
            style: new TextStyle({ fill: "#ffffff", fontSize: 24 }),
        });

        const createBtn = new GameButton({
            label: "Create Room",
            onClick: async () => {
                try {
                    const result = await createRoom(playerName);
                    console.log("✅ Created room:", result.room_id);
                    // เรียก triggerFSMEvent เพื่อแจ้ง FSM ว่าห้องถูกสร้างแล้ว
                    this.triggerFSMEvent(GameEvents.ROOM_CREATED, { roomId: result.room_id });
                } catch (err) {
                    console.error("❌ Failed to create room:", err);
                }
            },
        });

        const roomTable = new Container();
        roomTable.layout = {
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            width: "100%",
            gap: 16,
        };

        this.tableHeader = new Container();
        this.tableHeader.layout = {
            width: "100%",
            marginBottom: 40,
            flexDirection: "column",
            alignSelf: "flex-start",
            gap: 8,
        };

        this.roomListContainer = new Container();
        this.roomListContainer.layout = {
            width: "100%",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            gap: 8,
        };

        const joinRow = new Container();
        joinRow.layout = {
            flexDirection: "row",
            justifyContent: "center",
            alignItems: "center",
            gap: 8,
        };

        const roomIdInput = new GameTextbox({ placeholder: "Enter Room ID" });

        const joinBtn = new GameButton({
            label: "Join Room",
            onClick: async () => {
                const roomId = roomIdInput.getText().trim();
                if (!roomId) return;
                try {
                    const result = await joinRoom(roomId, playerName);
                    console.log("✅ Joined room:", roomId);
                    // เรียก triggerFSMEvent เพื่อแจ้ง FSM ว่าห้องถูกเข้าร่วมแล้ว
                    this.triggerFSMEvent(GameEvents.ROOM_JOINED, { roomId: roomId });
                } catch (err) {
                    console.error("❌ Failed to join room:", err);
                }
            },
        });

        headerRow.addChild(title, createBtn.view);
        roomTable.addChild(this.tableHeader, this.roomListContainer);
        joinRow.addChild(roomIdInput.view, joinBtn.view);
        this.addChild(headerRow, roomTable, joinRow);

        this.loadRoomList();
    }

    async loadRoomList() {
        try {
            const result = await listRooms();
            const roomList = result.rooms;

            this.roomListContainer.removeChildren();
            this.tableHeader.removeChildren();

            if (roomList.length === 0) {
                const emptyText = new Text({
                    text: "No available rooms.",
                    style: new TextStyle({ fill: "#999999", fontSize: 16 }),
                });
                this.tableHeader.addChild(emptyText);
                return;
            }

            const listTitle = new Text({
                text: "🗂 Available Rooms:",
                style: new TextStyle({ fill: "#ffffff", fontSize: 20 }),
            });
            this.tableHeader.addChild(listTitle);

            for (const room of roomList) {
                const row = new Container();
                row.layout = {
                    flexDirection: "row",
                    justifyContent: "flex-end",
                    alignItems: "center",
                    width: "100%",
                };

                const label = new Text({
                    text: `Room: ${room.room_id}`,
                    style: new TextStyle({ fill: "#ffffff", fontSize: 18 }),
                });

                const joinBtn = new GameButton({
                    width: 90,
                    height: 30,
                    label: "Join",
                    onClick: async () => {
                        try {
                            const result = await joinRoom(room.room_id, this.playerName);
                            console.log("✅ Joined room:", room.room_id);
                            // เรียก triggerFSMEvent เพื่อแจ้ง FSM ว่าห้องถูกเข้าร่วมแล้ว
                            this.triggerFSMEvent(GameEvents.ROOM_JOINED, { roomId: room.room_id });
                        } catch (err) {
                            console.error("❌ Failed to join room:", err);
                        }
                    },
                });

                row.addChild(label, joinBtn.view);
                this.roomListContainer.addChild(row);
            }
        } catch (err) {
            console.error("❌ Failed to load room list:", err);
        }
    }
}