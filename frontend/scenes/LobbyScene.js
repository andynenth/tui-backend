// frontend/scenes/LobbyScene.js

import { Container, Text, TextStyle } from "pixi.js";
import { GameButton } from "../components/GameButton.js";
import { GameTextbox } from "../components/GameTextbox.js";
import { createRoom, joinRoom } from "../api.js";
import { GameEvents } from "../SceneFSM.js";
import {
  connect as connectSocket,
  on as onSocketEvent,
  off as offSocketEvent,
  disconnect as disconnectSocket,
  emit as emitSocketEvent,
} from "../socketManager.js";

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

    console.log("🔵 Entered Enhanced LobbyScene with WebSocket");

    this.playerName = playerName; // Store the player's name.
    this.triggerFSMEvent = triggerFSMEvent; // Store the FSM event trigger callback.

    // Track if scene is active
    this.isActive = true;

    // Define the layout properties for the entire scene container using PixiJS Layout.
    this.layout = {
      width: "100%",
      flexDirection: "column",
      alignItems: "center",
      padding: 16,
      gap: 16,
    };

    // Create a header row container for the welcome message and "Create Room" button.
    const headerRow = new Container();
    headerRow.layout = {
      flexDirection: "row",
      justifyContent: "flex-end",
      alignItems: "center",
      width: "100%",
      height: 50,
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
          this.triggerFSMEvent(GameEvents.ROOM_CREATED, {
            roomId: result.room_id,
          });
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


    const createBtnRow = new Container();
    createBtnRow.layout = {
      flexDirection: "row",
      alignSelf: "flex-start",
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

    // Connection status indicator
    this.connectionStatus = new Text({
      text: "🔴 Connecting to lobby...",
      style: new TextStyle({ fill: "#ffaa00", fontSize: 14 }),
    });

    // Add elements to their respective containers and then to the main scene.
    headerRow.addChild(title, this.connectionStatus);
    roomTable.addChild(this.tableHeader, this.roomListContainer);
    createBtnRow.addChild(createBtn.view);
    joinRow.addChild(roomIdInput.view, joinBtn.view);
    this.addChild(headerRow, roomTable, createBtnRow
        , joinRow);

    this.setupLobbyWebSocket();
  }

  /**
   * ✅ Setup WebSocket connection for real-time lobby updates
   */
  setupLobbyWebSocket() {
    // ✅ Connect to special lobby WebSocket
    disconnectSocket(); // Ensure clean state
    connectSocket("lobby");

    console.log("🌐 Setting up lobby WebSocket listeners");

    // ✅ Handle connection events
    this.handleConnected = () => {
      if (!this.isActive) return;
      console.log("✅ Connected to lobby WebSocket");
      this.connectionStatus.text = "🟢 Connected";
      this.connectionStatus.style.fill = "#00ff00";

      // Request initial room list
      emitSocketEvent("request_room_list", { player_name: this.playerName });
    };

    this.handleDisconnected = () => {
      if (!this.isActive) return;
      console.log("⚠️ Disconnected from lobby WebSocket");
      this.connectionStatus.text = "🔴 Disconnected";
      this.connectionStatus.style.fill = "#ff0000";
    };

    this.handleReconnecting = (data) => {
      if (!this.isActive) return;
      this.connectionStatus.text = `🟡 Reconnecting... (${data.attempt}/${data.maxAttempts})`;
      this.connectionStatus.style.fill = "#ffaa00";
    };

    this.handleConnectionFailed = () => {
      if (!this.isActive) return;
      this.connectionStatus.text = "❌ Connection Failed";
      this.connectionStatus.style.fill = "#ff0000";

      // Fallback to showing cached/empty state
      this.showFallbackRoomList();
    };

    // ✅ Handle room list updates
    this.handleRoomListUpdate = (data) => {
      if (!this.isActive) return;
      console.log("📡 Received room list update:", data);

      if (data.rooms) {
        this.updateRoomList(data.rooms);
      }
    };

    // ✅ Handle individual room updates
    this.handleRoomCreated = (data) => {
      if (!this.isActive) return;
      console.log("🆕 Room created:", data);
      // Request fresh room list
      emitSocketEvent("request_room_list", { player_name: this.playerName });
    };

    this.handleRoomClosed = (data) => {
      if (!this.isActive) return;
      console.log("🗑️ Room closed:", data);
      // Request fresh room list
      emitSocketEvent("request_room_list", { player_name: this.playerName });
    };

    this.handleRoomUpdated = (data) => {
      if (!this.isActive) return;
      console.log("🔄 Room updated:", data);
      // Request fresh room list to get latest occupancy
      emitSocketEvent("request_room_list", { player_name: this.playerName });
    };

    // Register all event listeners
    onSocketEvent("connected", this.handleConnected);
    onSocketEvent("disconnected", this.handleDisconnected);
    onSocketEvent("reconnecting", this.handleReconnecting);
    onSocketEvent("connection_failed", this.handleConnectionFailed);
    onSocketEvent("room_list_update", this.handleRoomListUpdate);
    onSocketEvent("room_created", this.handleRoomCreated);
    onSocketEvent("room_closed", this.handleRoomClosed);
    onSocketEvent("room_updated", this.handleRoomUpdated);

    // Request room list if connection is ready
    // In case WebSocket connect faster than setup listeners
    setTimeout(() => {
      if (this.isActive) {
        emitSocketEvent("request_room_list", { player_name: this.playerName });
      }
    }, 100);
  }

  updateRoomList(roomList) {
    console.log("🔄 Updating room list with", roomList.length, "rooms");

    // Clear existing content
    this.roomListContainer.removeChildren();
    this.tableHeader.removeChildren();

    if (roomList.length === 0) {
      const emptyText = new Text({
        text: "No available rooms. Create one to get started!",
        style: new TextStyle({ fill: "#999999", fontSize: 16 }),
      });
      this.tableHeader.addChild(emptyText);
      return;
    }

    const listTitle = new Text({
      text: `🗂 Available Rooms (${roomList.length}):`,
      style: new TextStyle({ fill: "#ffffff", fontSize: 20 }),
    });
    this.tableHeader.addChild(listTitle);

    // ✅ Filter and display rooms
    let displayedRooms = 0;
    for (const room of roomList) {
      const occupiedSlots = room.occupied_slots || 0;
      const totalSlots = room.total_slots || 4;

      // Skip full rooms
      if (occupiedSlots >= totalSlots) {
        continue;
      }

      const row = new Container();
      row.layout = {
        flexDirection: "row",
        justifyContent: "flex-end",
        alignItems: "center",
        width: "100%",
        gap: 16,
      };

      // ✅ Enhanced room label with host info
      const hostInfo = room.host_name ? ` by ${room.host_name}` : "";
      const label = new Text({
        text: `Room: ${room.room_id} (${occupiedSlots}/${totalSlots})${hostInfo}`,
        style: new TextStyle({
          fill: "#ffffff",
          fontSize: 18,
          wordWrap: false,
        }),
      });

      const joinBtn = new GameButton({
        width: 90,
        height: 30,
        label: "Join",
        onClick: async () => {
          try {
            // ✅ Optimistic UI update
            joinBtn.setText("Joining...");
            joinBtn.setEnabled(false);

            const result = await joinRoom(room.room_id, this.playerName);
            console.log("✅ Joined room:", room.room_id);
            this.triggerFSMEvent(GameEvents.ROOM_JOINED, {
              roomId: room.room_id,
            });
          } catch (err) {
            console.error("❌ Failed to join room:", err);

            // ✅ Reset button state
            joinBtn.setText("Join");
            joinBtn.setEnabled(true);

            if (err.message && err.message.includes("409")) {
              alert("Cannot join: Room is already full.");
            } else if (err.message && err.message.includes("404")) {
              alert("Room no longer exists.");
              // Request fresh room list
              emitSocketEvent("request_room_list", { player_name: this.playerName });
            } else {
              alert(`Failed to join room: ${err.message || "Unknown error"}`);
            }
          }
        },
      });

      row.addChild(label, joinBtn.view);
      this.roomListContainer.addChild(row);
      displayedRooms++;
    }

    // ✅ Show message if all rooms are full
    if (displayedRooms === 0 && roomList.length > 0) {
      const fullText = new Text({
        text: "All rooms are currently full. Please create a new room.",
        style: new TextStyle({ fill: "#ffaa00", fontSize: 16 }),
      });
      this.roomListContainer.addChild(fullText);
    }
  }

/**
   * ✅ Fallback room list when connection fails
   */
  showFallbackRoomList() {
    this.roomListContainer.removeChildren();
    this.tableHeader.removeChildren();

    const fallbackText = new Text({
      text: "⚠️ Unable to load room list. Connection issue.",
      style: new TextStyle({ fill: "#ff6666", fontSize: 16 }),
    });

    const retryBtn = new GameButton({
      label: "Retry Connection",
      onClick: () => {
        this.setupLobbyWebSocket();
      },
    });

    this.tableHeader.addChild(fallbackText);
    this.roomListContainer.addChild(retryBtn.view);
  }

  /**
   * ✅ Cleanup WebSocket listeners
   */
  teardownWebSocketListeners() {
    console.log("🧹 Cleaning up lobby WebSocket listeners");

    this.isActive = false;

    // Remove all event listeners
    offSocketEvent("connected", this.handleConnected);
    offSocketEvent("disconnected", this.handleDisconnected);
    offSocketEvent("reconnecting", this.handleReconnecting);
    offSocketEvent("connection_failed", this.handleConnectionFailed);
    offSocketEvent("room_list_update", this.handleRoomListUpdate);
    offSocketEvent("room_created", this.handleRoomCreated);
    offSocketEvent("room_closed", this.handleRoomClosed);
    offSocketEvent("room_updated", this.handleRoomUpdated);

    // Disconnect from lobby WebSocket
    disconnectSocket();
  }

  /**
   * ✅ Start auto-refresh of room list
   */
  startAutoRefresh() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }

    this.refreshInterval = setInterval(() => {
      if (this.isActive) {
        this.loadRoomList();
      }
    }, 2000); // Refresh every 2 seconds
  }

  /**
   * ✅ Stop auto-refresh
   */
  stopAutoRefresh() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
      this.refreshInterval = null;
    }
  }

  /**
   * Fetches the list of available rooms from the backend API and updates the UI.
   */
  async loadRoomList() {
    try {
      const result = await listRooms();
      const roomList = result.rooms;

      // Clear existing content
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
        // Calculate occupied slots and total slots.
        // room.slots is an object like {P1: {name: "Player1"}, P2: null, ...}
        const occupiedSlots = room.occupied_slots || 0;
        const totalSlots = room.total_slots || 4;

        // Do not display rooms that are full.
        if (occupiedSlots >= totalSlots) {
          continue; // Skip this room if it's full.
        }

        const row = new Container();
        row.layout = {
          flexDirection: "row",
          justifyContent: "flex-end",
          alignItems: "center",
          width: "100%",
          gap: 16,
        };

        // Create a label for the room ID. Room: ID (occupied/total)
        const label = new Text({
          text: `Room: ${room.room_id} (${occupiedSlots}/${totalSlots})`,
          style: new TextStyle({
            fill: "#ffffff",
            fontSize: 18,
            wordWrap: false,
          }),
        });

        const joinBtn = new GameButton({
          width: 90,
          height: 30,
          label: "Join",
          onClick: async () => {
            try {
              const result = await joinRoom(room.room_id, this.playerName);
              console.log("✅ Joined room:", room.room_id);
              this.triggerFSMEvent(GameEvents.ROOM_JOINED, {
                roomId: room.room_id,
              });
            } catch (err) {
              console.error("❌ Failed to join room:", err);

              if (err.message && err.message.includes("409")) {
                alert("Cannot join: Room is already full.");
              } else {
                alert(`Failed to join room: ${err.message || "Unknown error"}`);
              }
            }
          },
        });

        row.addChild(label, joinBtn.view);
        this.roomListContainer.addChild(row);
      }

      // ✅ If all rooms were full after filtering, display a specific message.
      if (this.roomListContainer.children.length === 0 && roomList.length > 0) {
        const fullText = new Text({
          text: "All rooms are currently full. Please create a new room.",
          style: new TextStyle({ fill: "#ffaa00", fontSize: 16 }),
        });
        this.roomListContainer.addChild(fullText);
      }
    } catch (err) {
      console.error("❌ Failed to load room list:", err);
    }
  }

  /**
   * ✅ Override destroy to cleanup interval
   */
  destroy(options) {
    this.isActive = false;
    this.stopAutoRefresh();
    super.destroy(options);
  }
}
