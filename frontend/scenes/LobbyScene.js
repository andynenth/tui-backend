// frontend/scenes/LobbyScene.js

// Import necessary modules from PixiJS and local components/APIs.
import { Container, Text, TextStyle } from "pixi.js"; // PixiJS Container for scene structure, Text for displaying text, TextStyle for text styling.
import { GameButton } from "../components/GameButton.js"; // Custom Button component.
import { GameTextbox } from "../components/GameTextbox.js"; // Custom Textbox component for user input.
import { createRoom, joinRoom, listRooms } from "../api.js"; // API functions for interacting with the backend.
import { GameEvents } from '../SceneFSM.js'; // Import GameEvents enum from the SceneFSM for triggering state transitions.

/**
 * LobbyScene class represents the game lobby screen where players can
 * see available rooms, create a new room, or join an existing room by ID.
 * It extends PixiJS Container to act as a display object.
 */
export class LobbyScene extends Container {
    /**
     * Constructor for the LobbyScene.
     * @param {string} playerName - The name of the current player.
     * @param {function} triggerFSMEvent - A callback function to trigger events in the FSM.
     */
    constructor(playerName, triggerFSMEvent) {
        super(); // Call the constructor of the parent class (Container).

        console.log("🔵 Entered LobbyScene"); // Log a message indicating entry into this scene.

        this.playerName = playerName; // Store the player's name.
        this.triggerFSMEvent = triggerFSMEvent; // Store the FSM event trigger callback.

        // Define the layout properties for the entire scene container using PixiJS Layout.
        this.layout = {
            width: "100%", // Scene takes full width.
            flexDirection: "column", // Arrange children in a column.
            alignItems: "center", // Horizontally center children.
            padding: 16, // Add padding around the scene content.
            gap: 16, // Add a gap between child elements.
        };

        // Create a header row container for the welcome message and "Create Room" button.
        const headerRow = new Container();
        headerRow.layout = {
            flexDirection: "row",
            justifyContent: "flex-end", // Align content to the right.
            alignItems: "center",
            width: "100%",
        };

        // Create the welcome message text.
        const title = new Text({
            text: `👤 Welcome, ${playerName}`,
            style: new TextStyle({ fill: "#ffffff", fontSize: 24 }),
        });

        // Create the "Create Room" button.
        const createBtn = new GameButton({
            label: "Create Room",
            onClick: async () => {
                try {
                    const result = await createRoom(playerName); // Call API to create a room.
                    console.log("✅ Created room:", result.room_id);
                    // Trigger FSM event to inform that a room has been created,
                    // passing the new room's ID.
                    this.triggerFSMEvent(GameEvents.ROOM_CREATED, { roomId: result.room_id });
                } catch (err) {
                    console.error("❌ Failed to create room:", err);
                    alert(`Failed to create room: ${err.message || "Unknown error"}`);
                }
            },
        });

        // Create a container for the room list table.
        const roomTable = new Container();
        roomTable.layout = {
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            width: "100%",
            gap: 16,
        };

        // Create a container for the table header (e.g., "Available Rooms" title).
        this.tableHeader = new Container();
        this.tableHeader.layout = {
            width: "100%",
            marginBottom: 40,
            flexDirection: "column",
            alignSelf: "flex-start", // Align header to the start (left).
            gap: 8,
        };

        // Create a container to hold the dynamically loaded list of rooms.
        this.roomListContainer = new Container();
        this.roomListContainer.layout = {
            width: "100%",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            gap: 8,
        };

        // Create a row for joining a room by ID.
        const joinRow = new Container();
        joinRow.layout = {
            flexDirection: "row",
            justifyContent: "center",
            alignItems: "center",
            gap: 8,
        };

        // Create a textbox for entering a room ID.
        const roomIdInput = new GameTextbox({ placeholder: "Enter Room ID" });

        // Create the "Join Room" button for joining by ID.
        const joinBtn = new GameButton({
            label: "Join Room",
            onClick: async () => {
                const roomId = roomIdInput.getText().trim(); // Get the entered room ID.
                if (!roomId) return; // If empty, do nothing.
                try {
                    const result = await joinRoom(roomId, playerName); // Call API to join the room.
                    console.log("✅ Joined room:", roomId);
                    // Trigger FSM event to inform that a room has been joined,
                    // passing the room's ID.
                    this.triggerFSMEvent(GameEvents.ROOM_JOINED, { roomId: roomId });
                } catch (err) {
                    console.error("❌ Failed to join room:", err);
                    alert(`Failed to join room: ${err.message || "Unknown error"}`);
                }
            },
        });

        // Add elements to their respective containers and then to the main scene.
        headerRow.addChild(title, createBtn.view);
        roomTable.addChild(this.tableHeader, this.roomListContainer);
        joinRow.addChild(roomIdInput.view, joinBtn.view);
        this.addChild(headerRow, roomTable, joinRow);

        // Load the list of available rooms when the scene is initialized.
        this.loadRoomList();
    }

    /**
     * Fetches the list of available rooms from the backend API and updates the UI.
     */
    async loadRoomList() {
        try {
            const result = await listRooms(); // Call API to get the list of rooms.
            const roomList = result.rooms;

            // Clear existing room list and header content before re-rendering.
            this.roomListContainer.removeChildren();
            this.tableHeader.removeChildren();

            if (roomList.length === 0) {
                // If no rooms are available, display a message.
                const emptyText = new Text({
                    text: "No available rooms.",
                    style: new TextStyle({ fill: "#999999", fontSize: 16 }),
                });
                this.tableHeader.addChild(emptyText);
                return;
            }

            // Add a title for the available rooms list.
            const listTitle = new Text({
                text: "🗂 Available Rooms:",
                style: new TextStyle({ fill: "#ffffff", fontSize: 20 }),
            });
            this.tableHeader.addChild(listTitle);

            // Iterate through the room list and create a row for each room.
            for (const room of roomList) {
                const row = new Container();
                row.layout = {
                    flexDirection: "row",
                    justifyContent: "flex-end", // Align content to the right.
                    alignItems: "center",
                    width: "100%",
                };

                // Create a label for the room ID.
                const label = new Text({
                    text: `Room: ${room.room_id}`,
                    style: new TextStyle({ fill: "#ffffff", fontSize: 18 }),
                });

                // Create a "Join" button for each room in the list.
                const joinBtn = new GameButton({
                    width: 90,
                    height: 30,
                    label: "Join",
                    onClick: async () => {
                        try {
                            const result = await joinRoom(room.room_id, this.playerName); // Join the specific room.
                            console.log("✅ Joined room:", room.room_id);
                            // Trigger FSM event to inform that a room has been joined.
                            this.triggerFSMEvent(GameEvents.ROOM_JOINED, { roomId: room.room_id });
                        } catch (err) {
                            console.error("❌ Failed to join room:", err);
                            alert(`Failed to join room: ${err.message || "Unknown error"}`);
                        }
                    },
                });

                // Add the label and button to the room row.
                row.addChild(label, joinBtn.view);
                // Add the room row to the main room list container.
                this.roomListContainer.addChild(row);
            }
        } catch (err) {
            console.error("❌ Failed to load room list:", err);
            alert(`Failed to load room list: ${err.message || "Unknown error"}`);
        }
    }
}
