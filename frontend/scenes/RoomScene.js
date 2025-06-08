// frontend/scenes/RoomScene.js

import { Container, Text, TextStyle } from "pixi.js";
import { GameButton } from "../components/GameButton.js";
import { getRoomStateData, assignSlot, startGame } from "../api.js";
import { GameEvents } from "../SceneFSM.js";
import { SocketManager } from "../network/SocketManager.js";
import { ConnectionStatus } from "../components/ConnectionStatus.js";

/**
 * RoomScene class represents the game room screen where players wait for a game to start,
 * join slots, or manage bots (for the host).
 * 
 * REFACTORED: Now uses the new modular SocketManager instead of legacy functions
 */
export class RoomScene extends Container {
  constructor(roomId, playerName, triggerFSMEvent) {
    super();

    console.log("🔵 Entered RoomScene (Refactored Version)");

    // Scene layout configuration
    this.layout = {
      width: "100%",
      flexDirection: "column",
      alignItems: "center",
      padding: 16,
      gap: 16,
    };

    // Core properties
    this.roomId = roomId;
    this.playerName = playerName;
    this.triggerFSMEvent = triggerFSMEvent;

    // Game state
    this.slots = ["P1", "P2", "P3", "P4"];
    this.slotLabels = {};
    this.latestSlots = {};
    this.isHost = false;
    this.isActive = true;

    // ✅ NEW: Create dedicated SocketManager instance
    this.socketManager = new SocketManager({
      enableReconnection: true,
      enableMessageQueue: true,
      reconnection: {
        maxAttempts: 10,
        baseDelay: 2000,
      },
    });

    // ✅ NEW: Connection status component with SocketManager
    this.connectionStatus = new ConnectionStatus(this.socketManager);

    // Initialize UI
    this._createUI();
    this._setupEventListeners();

    // Start connection and fetch initial state
    this._initializeConnection();
  }

  /**
   * Create the UI components
   */
  _createUI() {
    // Header row with title and connection status
    const headerRow = new Container();
    headerRow.layout = {
      flexDirection: "row",
      justifyContent: "space-between",
      width: "100%",
      height: "auto",
    };

    const title = new Text({
      text: `📦 Room ID: ${this.roomId}`,
      style: new TextStyle({ fill: "#ffffff", fontSize: 22 }),
    });

    headerRow.addChild(title, this.connectionStatus.view);

    // Player table container
    this.playerTable = new Container();
    this.playerTable.layout = {
      flexDirection: "column",
      justifyContent: "center",
      alignItems: "center",
      width: "100%",
    };

    // Start button (host only)
    this.startButton = new GameButton({
      label: "Start Game",
      onClick: async () => {
        try {
          const result = await startGame(this.roomId);
          console.log("🚀 Game started!", result);
          // Game start event will come through WebSocket
        } catch (err) {
          console.error("❌ Failed to start game", err);
          alert(`Failed to start game: ${err.message || "Unknown error"}`);
        }
      },
    });

    // Exit button
    this.exitButton = new GameButton({
      label: "Exit",
      onClick: async () => {
        try {
          await fetch(
            `/api/exit-room?room_id=${this.roomId}&name=${this.playerName}`,
            { method: "POST" }
          );
          this.triggerFSMEvent(GameEvents.EXIT_ROOM);
        } catch (err) {
          console.error("❌ Failed to exit", err);
          alert(`Failed to exit room: ${err.message || "Unknown error"}`);
        }
      },
    });

    // Footer row with buttons
    const footerRow = new Container();
    footerRow.layout = {
      flexDirection: "row",
      justifyContent: "space-between",
      width: "100%",
      height: "auto",
    };

    this.startButton.setEnabled(false);
    footerRow.addChild(this.exitButton.view, this.startButton.view);

    // Add all components to scene
    this.addChild(headerRow, this.playerTable, footerRow);

    // Initialize slot views
    this._renderSlots();
  }

  /**
   * Initialize WebSocket connection and fetch initial state
   */
  async _initializeConnection() {
    try {
      // Connect to room WebSocket
      await this.socketManager.connect(this.roomId);
      console.log("✅ Connected to room WebSocket");

      // Fetch initial room state
      await this._refreshRoomState();
    } catch (err) {
      console.error("❌ Failed to initialize connection:", err);
      alert("Failed to connect to room. Returning to lobby.");
      this.triggerFSMEvent(GameEvents.EXIT_ROOM);
    }
  }

  /**
   * Set up WebSocket event listeners using new SocketManager
   */
  _setupEventListeners() {
    // ✅ NEW: Using SocketManager's event system
    
    // Connection events
    this.socketManager.on("connected", () => {
      console.log("✅ WebSocket connected to room");
    });

    this.socketManager.on("disconnected", (data) => {
      console.log("⚠️ WebSocket disconnected:", data);
      if (!data.intentional && this.isActive) {
        // Will auto-reconnect due to enableReconnection: true
      }
    });

    this.socketManager.on("reconnecting", (status) => {
      console.log(`🔄 Reconnecting... (${status.attempts}/${status.maxAttempts})`);
    });

    this.socketManager.on("reconnected", () => {
      console.log("✅ WebSocket reconnected");
      // Refresh room state after reconnection
      this._refreshRoomState();
    });

    this.socketManager.on("connection_failed", (data) => {
      console.error("❌ Connection failed:", data);
      if (this.isActive) {
        alert(`Connection lost: ${data.reason}. Returning to Lobby.`);
        this.triggerFSMEvent(GameEvents.EXIT_ROOM);
      }
    });

    // Room events
    this.socketManager.on("room_state_update", (data) => {
      if (!this.isActive) return;
      console.log("📡 Room state update:", data);

      if (data.host_name !== undefined) {
        this.isHost = data.host_name === this.playerName;
      }

      if (data.slots) {
        this._updateSlotViews(data.slots);
      }
    });

    this.socketManager.on("room_closed", (data) => {
      if (!this.isActive) return;
      console.log("🚪 Room closed:", data);
      alert(data.message || "Room has been closed");
      this.triggerFSMEvent(GameEvents.EXIT_ROOM);
    });

    this.socketManager.on("player_kicked", (data) => {
      if (!this.isActive) return;
      if (data.player === this.playerName) {
        alert(data.reason || "You have been removed from the room by the host.");
        this.triggerFSMEvent(GameEvents.EXIT_ROOM);
      }
    });

    this.socketManager.on("player_left", (data) => {
      if (!this.isActive) return;
      console.log("👋 Player left:", data.player);
    });

    this.socketManager.on("start_game", (data) => {
      if (!this.isActive) return;
      console.log("🎮 Game started!", data);
      this.triggerFSMEvent(GameEvents.GAME_STARTED, {
        roomId: this.roomId,
        gameData: data,
      });
    });
  }

  /**
   * Fetch and update room state
   */
  async _refreshRoomState() {
    try {
      const result = await getRoomStateData(this.roomId);
      if (result && result.slots && result.host_name !== undefined) {
        this.isHost = result.host_name === this.playerName;
        this._updateSlotViews(result.slots);
      } else {
        console.error("Invalid room state data:", result);
        alert("Room state invalid. Returning to Lobby.");
        this.triggerFSMEvent(GameEvents.EXIT_ROOM);
      }
    } catch (err) {
      console.error("❌ Failed to fetch room state:", err);
      alert(`Error fetching room state: ${err.message || "Unknown error"}`);
      this.triggerFSMEvent(GameEvents.EXIT_ROOM);
    }
  }

  /**
   * Render slot UI components
   */
  _renderSlots() {
    for (const slot of this.slots) {
      const row = new Container();
      row.layout = {
        flexDirection: "row",
        alignItems: "center",
        justifyContent: "flex-end",
        width: "100%",
        padding: 10,
      };

      // Slot label
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
      textContainer.addChild(slotText);

      // Slot button
      const slotBtn = new GameButton({
        label: "Add bot",
        height: 30,
        width: 100,
        onClick: () => this._handleSlotClick(slot),
      });

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

  /**
   * Handle slot button clicks
   */
  async _handleSlotClick(slotId) {
    const slotIndex = parseInt(slotId[1]) - 1;
    const info = this.latestSlots[slotId];

    console.log(`Slot ${slotId} clicked. Current state:`, info);

    try {
      if (this.isHost) {
        if (!info) {
          // Empty slot - add bot
          await assignSlot(this.roomId, `Bot ${slotIndex + 1}`, slotIndex);
        } else if (info.is_bot) {
          // Bot slot - make it open
          await assignSlot(this.roomId, null, slotIndex);
        } else if (info.name && info.name !== this.playerName) {
          // Other player - kick and replace with bot
          await assignSlot(this.roomId, `Bot ${slotIndex + 1}`, slotIndex);
        }
      } else {
        // Non-host can only join empty slots
        if (!info) {
          await assignSlot(this.roomId, this.playerName, slotIndex);
        }
      }
    } catch (err) {
      console.error("❌ Failed to update slot:", err);
      alert(`Failed to change slot: ${err.message || err.detail}`);
    }
  }

  /**
   * Update slot views based on new data
   */
  _updateSlotViews(slots) {
    console.log("Updating slot views:", slots);
    this.latestSlots = slots;

    for (const slot of this.slots) {
      const info = slots[slot];
      const { label, joinBtn } = this.slotLabels[slot];

      if (!info) {
        // Empty slot
        label.text = `${slot}: (Open)`;
        if (this.isHost) {
          joinBtn.setText("Add bot");
          joinBtn.view.visible = true;
        } else {
          joinBtn.setText("Join");
          joinBtn.view.visible = true;
        }
      } else if (info.is_bot) {
        // Bot slot
        label.text = `${slot}: 🤖 ${info.name}`;
        if (this.isHost) {
          joinBtn.setText("Open");
          joinBtn.view.visible = true;
        } else {
          joinBtn.view.visible = false;
        }
      } else if (info.name === this.playerName) {
        // Current player's slot
        label.text = `${slot}: ${info.name} <<`;
        joinBtn.view.visible = false;
      } else {
        // Other player's slot
        label.text = `${slot}: ${info.name}`;
        if (this.isHost) {
          joinBtn.setText("Add bot");
          joinBtn.view.visible = true;
        } else {
          joinBtn.view.visible = false;
        }
      }
    }

    // Update start button
    const isReady = Object.values(slots).every(
      (info) => info && (info.is_bot || info.name)
    );
    this.startButton.setEnabled(isReady);
    this.startButton.view.visible = this.isHost;
  }

  /**
   * Clean up when scene is destroyed
   */
  destroy(options) {
    console.log("🧹 Cleaning up RoomScene");
    this.isActive = false;

    // Disconnect WebSocket
    if (this.socketManager) {
      this.socketManager.disconnect();
    }

    // Clean up connection status component
    if (this.connectionStatus) {
      this.connectionStatus.destroy();
    }

    super.destroy(options);
  }
}