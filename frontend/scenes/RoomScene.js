// frontend/scenes/RoomScene.js

// Import necessary modules from PixiJS and local components/APIs.
import { Container, Text, TextStyle } from "pixi.js"; // PixiJS Container for scene structure, Text for displaying text, TextStyle for text styling.
import { GameButton } from "../components/GameButton.js"; // Custom Button component.
import { getRoomStateData, assignSlot, startGame } from "../api.js"; // API functions for interacting with the backend.
import { GameEvents } from "../SceneFSM.js"; // GameEvents enum for triggering state transitions in the FSM.
import {
  connect as connectSocket,
  on as onSocketEvent,
  disconnect as disconnectSocket,
  off as offSocketEvent,
} from "../network/index.js"; // WebSocket manager for real-time communication.
import { ConnectionStatus } from "../components/ConnectionStatus.js";
import { SocketManager } from "../network/SocketManager.js";


/**
 * RoomScene class represents the game room screen where players wait for a game to start,
 * join slots, or manage bots (for the host).
 * It extends PixiJS Container to act as a display object.
 */
export class RoomScene extends Container {
  /**
   * Constructor for the RoomScene.
   * @param {string} roomId - The ID of the current room.
   * @param {string} playerName - The name of the current player.
   * @param {function} triggerFSMEvent - A callback function to trigger events in the FSM.
   */
  constructor(roomId, playerName, triggerFSMEvent) {
    super(); // Call the constructor of the parent class (Container).

    console.log("🔵 Entered RoomScene");

    // Define the layout properties for the entire scene container using PixiJS Layout.
    this.layout = {
      width: "100%", // Scene takes full width.
      flexDirection: "column", // Arrange children in a column.
      alignItems: "center", // Horizontally center children.
      padding: 16, // Add padding around the scene content.
      gap: 16, // Add a gap between child elements.
    };

    // Store scene-specific properties.
    this.roomId = roomId;
    this.playerName = playerName;
    this.triggerFSMEvent = triggerFSMEvent; // FSM event trigger callback.

    this.slots = ["P1", "P2", "P3", "P4"]; // Predefined player slots.
    this.slotLabels = {}; // Object to store references to PixiJS Text and Button objects for each slot.
    this.latestSlots = {}; // Stores the most recent slot data received from the server.
    this.openSlots = []; // Not currently used, but could be for tracking available slots.
    this.isHost = false; // Flag to determine if the current player is the host.
    this.isActive = true; // Track if we're in this room

    this.connectionStatus = new ConnectionStatus();

    this.socketManager = new SocketManager({
      enableReconnection: true,
      reconnection: {
        maxAttempts: 10,
        baseDelay: 2000,
      },
    });

    // Create the room ID title.
    const title = new Text({
      text: `📦 Room ID: ${roomId}`,
      style: new TextStyle({ fill: "#ffffff", fontSize: 22 }),
    });
    const titleC = new Container();
    titleC.addChild(title);

    // Create a header row container for the title.
    const headerRow = new Container();
    headerRow.layout = {
      flexDirection: "row",
      justifyContent: "space-between",
      width: "100%",
      height: "auto",
    };

    // Create a container for the player slots table.
    this.playerTable = new Container();
    this.playerTable.layout = {
      flexDirection: "column",
      justifyContent: "center",
      alignItems: "center",
      width: "100%",
    };

    // Add elements to the scene.
    headerRow.addChild(titleC, this.connectionStatus.view);
    this.addChild(headerRow, this.playerTable);

    // Initialize the slot views and fetch the initial room state.
    this.renderSlots(); // Renders the initial structure of slots (labels and buttons).
    this.refreshRoomState(); // Fetches the current state of the room from the backend.
    this.setupWebSocketListeners(); // Sets up real-time updates via WebSocket.

    // Create the "Start Game" button.
    this.startButton = new GameButton({
      label: "Start Game",
      onClick: async () => {
        try {
          // ✅ เรียก API เพื่อเริ่มเกม
          const result = await startGame(this.roomId);
          console.log("🚀 Game started!", result);

          // ✅ ไม่ต้อง trigger event ที่นี่
          // รอให้ WebSocket broadcast มาแทน
        } catch (err) {
          console.error("❌ Failed to start game", err);
          alert(`Failed to start game: ${err.message || "Unknown error"}`);
        }
      },
    });

    // Create the "Exit" button.
    this.exitButton = new GameButton({
      label: "Exit",
      onClick: async () => {
        try {
          // Call API to exit the room.
          await fetch(
            `/api/exit-room?room_id=${this.roomId}&name=${this.playerName}`,
            {
              method: "POST",
            }
          );
          // Trigger FSM event to inform that the player has exited the room, prompting a scene change.
          this.triggerFSMEvent(GameEvents.EXIT_ROOM);
        } catch (err) {
          console.error("❌ Failed to exit", err);
          alert(`Failed to exit room: ${err.message || "Unknown error"}`);
        }
      },
    });

    // Create a footer row for the buttons.
    const footerRow = new Container();
    footerRow.layout = {
      flexDirection: "row",
      justifyContent: "space-between", // Space buttons evenly.
      width: "100%",
      height: "auto",
    };

    this.startButton.setEnabled(false); // Initially disable the "Start Game" button.
    footerRow.addChild(this.exitButton.view, this.startButton.view);
    this.addChild(footerRow);
  }

  /**
   * Fetches the current state of the room from the backend API and updates the UI.
   */
  async refreshRoomState() {
    try {
      const result = await getRoomStateData(this.roomId); // Fetch room state data.
      // Check if the result is valid and contains necessary data.
      if (result && result.slots && result.host_name !== undefined) {
        this.isHost = result.host_name === this.playerName; // Determine if current player is host.
        this.updateSlotViews(result.slots); // Update the UI based on the fetched slot data.
      } else {
        console.error(
          "Received unexpected data from getRoomStateData:",
          result
        );
        alert(
          "Room state invalid or room may have been closed. Returning to Lobby."
        );
        this.triggerFSMEvent(GameEvents.EXIT_ROOM); // Go back to Lobby if data is invalid.
      }
    } catch (err) {
      console.error("❌ Failed to fetch room state:", err);
      alert(
        `Error fetching room state: ${
          err.message || "Unknown error"
        }. Returning to Lobby.`
      );
      this.triggerFSMEvent(GameEvents.EXIT_ROOM); // Go back to Lobby on API error.
    }
  }

  /**
   * Renders the initial structure of player slots (labels and buttons).
   * This method sets up the visual elements but doesn't fill them with dynamic data.
   */
  renderSlots() {
    for (const slot of this.slots) {
      const row = new Container();
      row.layout = {
        flexDirection: "row",
        alignItems: "center",
        justifyContent: "flex-end", // Align content to the right.
        width: "100%",
        padding: 10,
      };

      // Create a text label for the slot (e.g., "P1: ...").
      const slotText = new Text({
        text: `${slot}: ...`, // Initial placeholder text.
        style: new TextStyle({ fill: "#ffffff", fontSize: 18 }),
      });

      const textContainer = new Container();
      textContainer.layout = {
        alignSelf: "center",
        justifyContent: "flex-start", // Align text to the left within its container.
        width: "100%",
        height: "100%",
        marginTop: 10,
      };

      // Create a button for the slot (label will be updated dynamically).
      const slotBtn = new GameButton({
        label: "Add bot", // Initial label, will be updated by updateSlotViews.
        height: 30,
        width: 100,
        onClick: async () => {
          const slotId = slot; // e.g., "P1", "P2"
          const slotIndex = parseInt(slotId[1]) - 1; // Convert "P1" to index 0, "P2" to 1, etc.
          const info = this.latestSlots[slotId]; // Get the current state of the clicked slot from the frontend's latest data.
          console.log(
            `[RoomScene.onClick] Player '${this.playerName}' clicked slot ${slotId} (index ${slotIndex}). Current Frontend Info:`,
            info
          );

          try {
            if (this.isHost) {
              // --- Logic for HOST ---
              if (!info) {
                // Slot is empty (null) --> HOST clicks "Add bot" (to add a bot).
                console.log(
                  `[RoomScene.onClick] Host adding bot to empty slot ${slotId}.`
                );
                await assignSlot(
                  this.roomId,
                  `Bot ${slotIndex + 1}`, // Assign a bot name like "Bot 1", "Bot 2".
                  slotIndex
                );
              } else if (info.is_bot) {
                // Slot has a Bot --> HOST clicks "Open" (to make it empty).
                console.log(
                  `[RoomScene.onClick] Host opening slot ${slotId} from bot.`
                );
                await assignSlot(this.roomId, null, slotIndex); // Assign null to make the slot empty.
              } else if (info.name && info.name !== this.playerName) {
                // Slot has another player --> HOST clicks "Add bot" (to kick that player and replace with a bot).
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
                return; // Do nothing if state is unexpected.
              }
            } else {
              // --- Logic for PLAYER (not Host) ---
              if (!info) {
                // Slot is empty (Player clicks "Join").
                console.log(
                  `[RoomScene.onClick] Player '${this.playerName}' attempting to join empty slot ${slotId}.`
                );
                await assignSlot(this.roomId, this.playerName, slotIndex);
              } else {
                console.warn(
                  `[RoomScene.onClick] Player clicked on non-empty slot:`,
                  info
                );
                return; // Do nothing if the slot is not empty.
              }
            }

            console.log(
              `[RoomScene.onClick] assignSlot API call sent for slot ${slotIndex}.`
            );
            // ✅ Added immediate call to getRoomStateData after assignSlot for debugging.
            const serverStateAfterClick = await getRoomStateData(this.roomId);
            console.log(
              "[RoomScene.onClick] Server State AFTER API Call (for Debug):",
              serverStateAfterClick
            );

            console.log(`[RoomScene.onClick] Awaiting WS update...`); // Expecting a WebSocket update.
          } catch (err) {
            console.error("❌ [RoomScene.onClick] Failed to toggle slot", err);
            alert(`Failed to change slot: ${err.message || err.detail}`);
          }
        },
      });

      textContainer.addChild(slotText); // Add the text label to its container.
      const btnContainer = new Container();
      btnContainer.layout = {
        alignItems: "center",
        justifyContent: "flex-end", // Align button to the right.
        width: "100%",
        height: 40,
      };
      btnContainer.addChild(slotBtn.view); // Add the button view to its container.

      row.addChild(textContainer, btnContainer); // Add text and button containers to the row.

      // Store references to the text label and button for later updates.
      this.slotLabels[slot] = { label: slotText, joinBtn: slotBtn };
      this.playerTable.addChild(row); // Add the slot row to the player table.
    }
  }

  /**
   * Updates the visual representation of player slots based on new data received from the server.
   * This method dynamically changes text labels and button visibility/labels.
   * @param {object} slots - An object containing the current state of all player slots.
   */
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
        // Slot ว่าง
        if (this.isHost) {
          label.text = `${slot}: (Open)`;
          joinBtn.setText("Add bot");
          joinBtn.view.visible = true;

          // ✅ สำคัญ: Re-assign onClick handler ทุกครั้ง
          joinBtn.onClick = async () => {
            try {
              console.log(
                `[RoomScene.onClick] Host adding bot to empty slot ${slot}.`
              );
              await assignSlot(
                this.roomId,
                `Bot ${parseInt(slot[1])}`,
                parseInt(slot[1]) - 1
              );
            } catch (err) {
              console.error("❌ Failed to add bot", err);
              alert(`Failed to add bot: ${err.message || err.detail}`);
            }
          };
        } else {
          // Hide join button from other players
          label.text = `${slot}: Open`;
          joinBtn.view.visible = false;
        }
      } else if (info.is_bot) {
        label.text = `${slot}: 🤖 ${info.name}`;
        if (this.isHost) {
          joinBtn.setText("Open");
          joinBtn.view.visible = true;

          // ✅ Re-assign onClick for Open
          joinBtn.onClick = async () => {
            try {
              console.log(
                `[RoomScene.onClick] Host opening slot ${slot} from Bot.`
              );
              await assignSlot(this.roomId, null, parseInt(slot[1]) - 1);
            } catch (err) {
              console.error("❌ Failed to open slot", err);
              alert(`Failed to open slot: ${err.message || err.detail}`);
            }
          };
        } else {
          joinBtn.view.visible = false;
        }
      } else if (info.name === this.playerName) {
        // Slot self-indicator
        label.text = `${slot}: ${info.name} <<`;
        joinBtn.view.visible = false;
      } else {
        // Slot is occupied
        label.text = `${slot}: ${info.name}`;
        if (this.isHost) {
          joinBtn.setText("Add bot");
          joinBtn.view.visible = true;

          // ✅ Re-assign onClick, kick player
          joinBtn.onClick = async () => {
            try {
              console.log(
                `[RoomScene.onClick] Host kicking player '${info.name}' and replacing with Bot.`
              );
              await assignSlot(
                this.roomId,
                `Bot ${parseInt(slot[1])}`,
                parseInt(slot[1]) - 1
              );
            } catch (err) {
              console.error("❌ Failed to kick player", err);
              alert(`Failed to kick player: ${err.message || err.detail}`);
            }
          };
        } else {
          joinBtn.view.visible = false;
        }
      }
    }

    // Update Start Game button
    const isReady = Object.values(slots).every(
      (info) => info && (info.is_bot || info.name)
    );
    this.startButton.setEnabled(isReady);
    this.startButton.view.visible = this.isHost;
  }

  /**
   * Sets up WebSocket listeners for real-time updates from the server.
   * This includes listening for room state changes, room closure, and player departures.
   */
  setupWebSocketListeners() {
    // Show reconnection status to user
    this.socketManager.on("reconnecting", (status) => {
      this.connectionStatus.text = `🟡 Reconnecting... (${status.attempts}/${status.maxAttempts})`;
    });

    this.socketManager.on("reconnected", () => {
      this.connectionStatus.text = "🟢 Connected";
    });

    disconnectSocket();
    connectSocket(this.roomId);

    // Register listener for 'room_state_update' event
    this.handleRoomStateUpdate = (data) => {
      if (!this.isActive) return;

      console.log("[RoomScene.handleRoomStateUpdate] Received data:", data);

      if (data.host_name !== undefined) {
        this.isHost = data.host_name === this.playerName;
      }

      if (data.slots) {
        this.updateSlotViews(data.slots);
      }
    };
    onSocketEvent("room_state_update", this.handleRoomStateUpdate);

    // Register listener for 'room_closed' event
    this.handleRoomClosed = (data) => {
      if (!this.isActive) return;

      console.log("WS: Received room_closed", data);

      if (this.triggerFSMEvent) {
        alert(data.message);
        this.triggerFSMEvent(GameEvents.EXIT_ROOM);
      }
    };
    onSocketEvent("room_closed", this.handleRoomClosed);

    // ✅ Register listener for 'player_kicked' event
    this.handlePlayerKicked = (data) => {
      if (!this.isActive) return;

      console.log("WS: Received player_kicked", data);

      // If you are kicked
      if (data.player === this.playerName) {
        alert(
          data.reason || "You have been removed from the room by the host."
        );
        this.triggerFSMEvent(GameEvents.EXIT_ROOM);
      }
    };
    onSocketEvent("player_kicked", this.handlePlayerKicked);

    // Register listener for 'player_left' event
    this.handlePlayerLeft = (data) => {
      if (!this.isActive) return;
      console.log("WS: Player left:", data.player);
    };
    onSocketEvent("player_left", this.handlePlayerLeft);

    this.handleGameStarted = (data) => {
      if (!this.isActive) return;

      console.log("WS: Game started!", data);

      // ส่ง event ไปที่ FSM พร้อมข้อมูลเกม
      this.triggerFSMEvent(GameEvents.GAME_STARTED, {
        roomId: this.roomId,
        gameData: data,
      });
    };
    onSocketEvent("start_game", this.handleGameStarted);

    this.handleConnectionFailed = (data) => {
      if (!this.isActive) return;

      alert(`Connection lost: ${data.reason}. Returning to Lobby.`);
      this.triggerFSMEvent(GameEvents.EXIT_ROOM);
    };
    onSocketEvent("connection_failed", this.handleConnectionFailed);
  }

  /**
   * Cleans up WebSocket listeners and disconnects the WebSocket connection.
   * This is crucial for preventing memory leaks and ensuring proper resource management
   * when the scene is no longer active.
   */
  teardownWebSocketListeners() {
    this.isActive = false;

    offSocketEvent("room_state_update", this.handleRoomStateUpdate);
    offSocketEvent("room_closed", this.handleRoomClosed);
    offSocketEvent("player_kicked", this.handlePlayerKicked); // ✅ Clean up new listener
    offSocketEvent("player_left", this.handlePlayerLeft);
    disconnectSocket();
    offSocketEvent("start_game", this.handleGameStarted);
    offSocketEvent("connection_failed", this.handleConnectionFailed);
    if (this.connectionStatus) {
      this.connectionStatus.destroy();
    }
  }

  /**
   * Overrides the PixiJS Container's destroy method to perform custom cleanup.
   * This ensures that WebSocket listeners are removed when the scene is destroyed.
   * @param {object} [options] - Options passed to the super.destroy method.
   */
  destroy(options) {
    this.teardownWebSocketListeners(); // Call custom cleanup method.
    super.destroy(options); // Call the parent class's destroy method.
  }
}
