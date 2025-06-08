// frontend/scenes/LobbyScene.js

import { Container, Text, TextStyle } from "pixi.js";
import { GameButton } from "../components/GameButton.js";
import { GameTextbox } from "../components/GameTextbox.js";
import { createRoom, joinRoom, listRooms } from "../api.js";
import { GameEvents } from "../SceneFSM.js";
import { SocketManager } from "../network/SocketManager.js";

/**
 * LobbyScene class represents the game lobby screen where players can
 * see available rooms, create a new room, or join an existing room by ID.
 * 
 * REFACTORED: Now uses the new modular SocketManager for real-time updates
 */
export class LobbyScene extends Container {
  constructor(playerName, triggerFSMEvent) {
    super();

    console.log("🔵 Entered LobbyScene (Refactored Version)");

    // Core properties
    this.playerName = playerName;
    this.triggerFSMEvent = triggerFSMEvent;
    this.isActive = true;

    // Scene layout configuration
    this.layout = {
      width: "100%",
      flexDirection: "column",
      alignItems: "center",
      padding: 16,
      gap: 16,
    };

    // ✅ NEW: Create dedicated SocketManager for lobby
    this.socketManager = new SocketManager({
      enableReconnection: true,
      enableMessageQueue: false, // Lobby doesn't need message queuing
      reconnection: {
        maxAttempts: 5,
        baseDelay: 1000,
      },
    });

    // UI References
    this.roomListContainer = null;
    this.tableHeader = null;
    this.connectionStatus = null;

    // Initialize UI and connections
    this._createUI();
    this._setupEventListeners();
    this._initializeLobbyConnection();
  }

  /**
   * Create the UI components
   */
  _createUI() {
    // Header row with welcome message and connection status
    const headerRow = new Container();
    headerRow.layout = {
      flexDirection: "row",
      justifyContent: "space-between",
      alignItems: "center",
      width: "100%",
      height: 50,
    };

    const title = new Text({
      text: `👤 Welcome, ${this.playerName}`,
      style: new TextStyle({ fill: "#ffffff", fontSize: 24 }),
    });

    // Connection status indicator
    this.connectionStatus = new Text({
      text: "🔴 Connecting to lobby...",
      style: new TextStyle({ fill: "#ffaa00", fontSize: 14 }),
    });

    headerRow.addChild(title, this.connectionStatus);

    // Room table container
    const roomTable = new Container();
    roomTable.layout = {
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      width: "100%",
      gap: 16,
    };

    // Table header
    this.tableHeader = new Container();
    this.tableHeader.layout = {
      width: "100%",
      marginBottom: 40,
      flexDirection: "column",
      alignSelf: "flex-start",
      gap: 8,
    };

    // Room list container
    this.roomListContainer = new Container();
    this.roomListContainer.layout = {
      width: "100%",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      gap: 8,
    };

    roomTable.addChild(this.tableHeader, this.roomListContainer);

    // Create room button row
    const createBtnRow = new Container();
    createBtnRow.layout = {
      flexDirection: "row",
      alignSelf: "flex-start",
      gap: 8,
    };

    const createBtn = new GameButton({
      label: "Create Room",
      onClick: () => this._handleCreateRoom(),
    });

    createBtnRow.addChild(createBtn.view);

    // Join room by ID row
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
      onClick: () => this._handleJoinRoomById(roomIdInput.getText()),
    });

    joinRow.addChild(roomIdInput.view, joinBtn.view);

    // Add all components to scene
    this.addChild(headerRow, roomTable, createBtnRow, joinRow);
  }

  /**
   * Initialize WebSocket connection to lobby
   */
  async _initializeLobbyConnection() {
    try {
      // Connect to special "lobby" room for real-time updates
      await this.socketManager.connect("lobby");
      console.log("✅ Connected to lobby WebSocket");

      // Request initial room list
      this.socketManager.send("request_room_list", { 
        player_name: this.playerName 
      });
    } catch (err) {
      console.error("❌ Failed to connect to lobby:", err);
      // Show fallback UI
      this._showFallbackRoomList();
    }
  }

  /**
   * Set up WebSocket event listeners
   */
  _setupEventListeners() {
    // ✅ NEW: Using SocketManager's event system

    // Connection events
    this.socketManager.on("connected", () => {
      console.log("✅ Connected to lobby WebSocket");
      this._updateConnectionStatus("🟢 Connected", "#00ff00");
      
      // Request room list on connection
      this.socketManager.send("request_room_list", { 
        player_name: this.playerName 
      });
    });

    this.socketManager.on("disconnected", () => {
      console.log("⚠️ Disconnected from lobby WebSocket");
      this._updateConnectionStatus("🔴 Disconnected", "#ff0000");
    });

    this.socketManager.on("reconnecting", (status) => {
      this._updateConnectionStatus(
        `🟡 Reconnecting... (${status.attempts}/${status.maxAttempts})`,
        "#ffaa00"
      );
    });

    this.socketManager.on("reconnected", () => {
      console.log("✅ Reconnected to lobby");
      this._updateConnectionStatus("🟢 Connected", "#00ff00");
      
      // Request fresh room list
      this.socketManager.send("request_room_list", { 
        player_name: this.playerName 
      });
    });

    this.socketManager.on("connection_failed", () => {
      this._updateConnectionStatus("❌ Connection Failed", "#ff0000");
      this._showFallbackRoomList();
    });

    // Lobby events
    this.socketManager.on("room_list_update", (data) => {
      if (!this.isActive) return;
      console.log("📡 Room list update:", data);
      if (data.rooms) {
        this._updateRoomList(data.rooms);
      }
    });

    this.socketManager.on("room_created", (data) => {
      if (!this.isActive) return;
      console.log("🆕 Room created:", data);
      // Request fresh room list
      this.socketManager.send("request_room_list", { 
        player_name: this.playerName 
      });
    });

    this.socketManager.on("room_closed", (data) => {
      if (!this.isActive) return;
      console.log("🗑️ Room closed:", data);
      // Request fresh room list
      this.socketManager.send("request_room_list", { 
        player_name: this.playerName 
      });
    });

    this.socketManager.on("room_updated", (data) => {
      if (!this.isActive) return;
      console.log("🔄 Room updated:", data);
      // Request fresh room list
      this.socketManager.send("request_room_list", { 
        player_name: this.playerName 
      });
    });
  }

  /**
   * Update connection status display
   */
  _updateConnectionStatus(text, color) {
    if (this.connectionStatus) {
      this.connectionStatus.text = text;
      this.connectionStatus.style.fill = color;
    }
  }

  /**
   * Handle create room button click
   */
  async _handleCreateRoom() {
    try {
      const result = await createRoom(this.playerName);
      console.log("✅ Created room:", result.room_id);
      this.triggerFSMEvent(GameEvents.ROOM_CREATED, {
        roomId: result.room_id,
      });
    } catch (err) {
      console.error("❌ Failed to create room:", err);
      alert(`Failed to create room: ${err.message || "Unknown error"}`);
    }
  }

  /**
   * Handle join room by ID
   */
  async _handleJoinRoomById(roomId) {
    const trimmedId = roomId.trim();
    if (!trimmedId) return;

    try {
      await joinRoom(trimmedId, this.playerName);
      console.log("✅ Joined room:", trimmedId);
      this.triggerFSMEvent(GameEvents.ROOM_JOINED, { roomId: trimmedId });
    } catch (err) {
      console.error("❌ Failed to join room:", err);
      alert(`Failed to join room: ${err.message || "Unknown error"}`);
    }
  }

  /**
   * Handle join room button click from list
   */
  async _handleJoinRoom(room) {
    const joinBtn = this._activeJoinButtons?.get(room.room_id);
    
    try {
      // Optimistic UI update
      if (joinBtn) {
        joinBtn.setText("Joining...");
        joinBtn.setEnabled(false);
      }

      await joinRoom(room.room_id, this.playerName);
      console.log("✅ Joined room:", room.room_id);
      this.triggerFSMEvent(GameEvents.ROOM_JOINED, {
        roomId: room.room_id,
      });
    } catch (err) {
      console.error("❌ Failed to join room:", err);

      // Reset button state
      if (joinBtn) {
        joinBtn.setText("Join");
        joinBtn.setEnabled(true);
      }

      if (err.message?.includes("409")) {
        alert("Cannot join: Room is already full.");
      } else if (err.message?.includes("404")) {
        alert("Room no longer exists.");
        // Request fresh room list
        this.socketManager.send("request_room_list", { 
          player_name: this.playerName 
        });
      } else {
        alert(`Failed to join room: ${err.message || "Unknown error"}`);
      }
    }
  }

  /**
   * Update room list display
   */
  _updateRoomList(roomList) {
    console.log("🔄 Updating room list with", roomList.length, "rooms");

    // Clear existing content
    this.roomListContainer.removeChildren();
    this.tableHeader.removeChildren();

    // Clear button references
    this._activeJoinButtons = new Map();

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

    // Display rooms
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

      // Room label with host info
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
        onClick: () => this._handleJoinRoom(room),
      });

      // Store button reference for updates
      this._activeJoinButtons.set(room.room_id, joinBtn);

      row.addChild(label, joinBtn.view);
      this.roomListContainer.addChild(row);
      displayedRooms++;
    }

    // Show message if all rooms are full
    if (displayedRooms === 0 && roomList.length > 0) {
      const fullText = new Text({
        text: "All rooms are currently full. Please create a new room.",
        style: new TextStyle({ fill: "#ffaa00", fontSize: 16 }),
      });
      this.roomListContainer.addChild(fullText);
    }
  }

  /**
   * Show fallback UI when connection fails
   */
  _showFallbackRoomList() {
    this.roomListContainer.removeChildren();
    this.tableHeader.removeChildren();

    const fallbackText = new Text({
      text: "⚠️ Unable to load room list. Connection issue.",
      style: new TextStyle({ fill: "#ff6666", fontSize: 16 }),
    });

    const retryBtn = new GameButton({
      label: "Retry Connection",
      onClick: () => this._initializeLobbyConnection(),
    });

    const loadManualBtn = new GameButton({
      label: "Load Room List",
      onClick: () => this._loadRoomListManually(),
    });

    this.tableHeader.addChild(fallbackText);
    this.roomListContainer.addChild(retryBtn.view, loadManualBtn.view);
  }

  /**
   * Fallback: Load room list via API
   */
  async _loadRoomListManually() {
    try {
      const result = await listRooms();
      this._updateRoomList(result.rooms || []);
    } catch (err) {
      console.error("❌ Failed to load rooms manually:", err);
      alert("Failed to load room list");
    }
  }

  /**
   * Clean up when scene is destroyed
   */
  destroy(options) {
    console.log("🧹 Cleaning up LobbyScene");
    this.isActive = false;

    // Disconnect WebSocket
    if (this.socketManager) {
      this.socketManager.disconnect();
    }

    // Clear references
    this._activeJoinButtons = null;

    super.destroy(options);
  }
}