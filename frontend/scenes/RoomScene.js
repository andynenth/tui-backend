// frontend/scenes/RoomScene.js

// Import necessary modules from PixiJS and local components/APIs.
import { Container, Text, TextStyle } from "pixi.js"; // PixiJS Container for scene structure, Text for displaying text, TextStyle for text styling.
import { GameButton } from "../components/GameButton.js"; // Custom Button component.
import { getRoomStateData, assignSlot, startGame } from "../api.js"; // API functions for interacting with the backend.
import { GameEvents } from "../SceneFSM.js"; // GameEvents enum for triggering state transitions in the FSM.
import {
  connect as connectSocket, // Function to establish WebSocket connection.
  on as onSocketEvent, // Function to register WebSocket event listeners.
  disconnect as disconnectSocket, // Function to close WebSocket connection.
  off as offSocketEvent, // Function to unregister WebSocket event listeners.
  getSocketReadyState, // Function to get the WebSocket connection state.
} from "../socketManager.js"; // WebSocket manager for real-time communication.

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

    console.log("🔵 Entered RoomScene"); // Log a message indicating entry into this scene.

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

    // Create the room ID title.
    const title = new Text({
      text: `📦 Room ID: ${roomId}`,
      style: new TextStyle({ fill: "#ffffff", fontSize: 22 }),
    });

    // Create a header row container for the title.
    const headerRow = new Container();
    headerRow.layout = {
      flexDirection: "row",
      justifyContent: "flex-end", // Align title to the right.
      alignItems: "center",
      width: "100%",
      height: 30,
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
    headerRow.addChild(title);
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
          await startGame(this.roomId); // Call API to start the game.
          console.log("🚀 Game started!");
          // Trigger FSM event to inform that the game has started, prompting a scene change.
          this.triggerFSMEvent(GameEvents.GAME_STARTED);
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
        console.error("Received unexpected data from getRoomStateData:", result);
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
    this.latestSlots = slots; // Store the latest slot data.

    for (const slot of this.slots) {
      const info = slots[slot]; // Get information for the current slot.
      const { label, joinBtn } = this.slotLabels[slot]; // Get references to the PixiJS objects for this slot.
      console.log(
        `[RoomScene.updateSlotViews] Processing slot ${slot}. Info:`,
        info
      );

      if (!info) {
        // Slot is empty (null).
        if (this.isHost) {
          label.text = `${slot}: (Open)`; // Host sees "Open" (empty).
          joinBtn.setText("Add bot"); // Host can "Add bot".
          joinBtn.view.visible = true;
          console.log(
            `  - Slot ${slot} (empty), Host view: label='(Open)', btn='Add bot', visible=true`
          );
        } else {
          label.text = `${slot}: Open`; // Player sees "Open" (empty).
          joinBtn.setText("Join"); // Player can "Join".
          joinBtn.view.visible = true;
          // ✅ Re-assign onClick for the "Join" button for players.
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
        // Slot has a Bot.
        label.text = `${slot}: 🤖 ${info.name}`; // Display bot's actual name (e.g., "Bot 2").
        if (this.isHost) {
          joinBtn.setText("Open"); // Host can "Open" (make empty).
          joinBtn.view.visible = true;
          // ✅ Re-assign onClick for the "Open" button for Host on a Bot slot.
          joinBtn.onClick = async () => {
            try {
              console.log(
                `[RoomScene.onClick] Host attempting to open slot ${slot} from Bot ${info.name}.`
              );
              await assignSlot(this.roomId, null, parseInt(slot[1]) - 1); // Make slot empty.
            } catch (err) {
              console.error(
                "❌ [RoomScene.onClick] Failed to open slot from bot",
                err
              );
              alert(`Failed to open slot: ${err.message || err.detail}`);
            }
          };
        } else {
          joinBtn.view.visible = false; // Player does not see the button.
        }
        console.log(
          `  - Slot ${slot} (bot), Host view (${this.isHost}): label='🤖 ${
            info.name
          }', btn='Open' (if Host), visible=${this.isHost ? "true" : "false"}`
        );
      } else if (info.name === this.playerName) {
        // Slot is occupied by the current player.
        label.text = `${slot}: ${info.name} <<`; // Indicate it's "us".
        joinBtn.view.visible = false; // No button for self-occupied slot.
        console.log(
          `  - Slot ${slot} (self), Host view (${this.isHost}): label='<<', btn visible=false`
        );
      } else {
        // Slot has another player.
        label.text = `${slot}: ${info.name}`;
        if (this.isHost) {
          joinBtn.setText("Add bot"); // Host can "Add bot" (to kick the player).
          joinBtn.view.visible = true;
          // ✅ Re-assign onClick for the "Add bot" button for Host on another player's slot.
          joinBtn.onClick = async () => {
            try {
              console.log(
                `[RoomScene.onClick] Host attempting to kick player '${info.name}' from slot ${slot} and replace with Bot.`
              );
              await assignSlot(
                this.roomId,
                `Bot ${parseInt(slot[1])}`, // Use the slot index for bot naming.
                parseInt(slot[1]) - 1
              );
            } catch (err) {
              console.error(
                "❌ [RoomScene.onClick] Failed to kick player",
                err
              );
              alert(`Failed to kick player: ${err.message || err.detail}`);
            }
          };
        } else {
          joinBtn.view.visible = false; // Player does not see the button.
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

    // "Start Game" button logic:
    // It's enabled only for the host and when all slots are filled (by players or bots).
    const isReady = Object.values(slots).every(
      (info) => info && (info.is_bot || info.name)
    );
    this.startButton.setEnabled(isReady); // Enable/disable based on readiness.
    this.startButton.view.visible = this.isHost; // Only visible to the host.
  }

  /**
   * Sets up WebSocket listeners for real-time updates from the server.
   * This includes listening for room state changes, room closure, and player departures.
   */
  setupWebSocketListeners() {
    // Connect to the WebSocket when entering RoomScene.
    connectSocket(this.roomId);

    // Register listener for 'room_state_update' event.
    this.handleRoomStateUpdate = (data) => {
      console.log("[RoomScene.handleRoomStateUpdate] Received data:", data); // Log received data.
      this.isHost = data.host_name === this.playerName; // Re-evaluate host status.
      console.log(
        `[RoomScene.handleRoomStateUpdate] isHost: ${this.isHost}, playerName: ${this.playerName}, host_name from data: ${data.host_name}`
      );
      this.updateSlotViews(data.slots); // Update UI with new slot data.
      console.log("[RoomScene.handleRoomStateUpdate] updateSlotViews called.");
    };
    onSocketEvent("room_state_update", this.handleRoomStateUpdate);

    // Register listener for 'room_closed' event (e.g., if the host leaves the room).
    this.handleRoomClosed = (data) => {
      console.log("WS: Received room_closed", data);
      alert(data.message); // Notify the player that the room is closed.
      this.triggerFSMEvent(GameEvents.EXIT_ROOM); // Trigger FSM to return to LobbyScene.
    };
    onSocketEvent("room_closed", this.handleRoomClosed);

    // Register listener for 'player_left' event (when any player leaves the room).
    this.handlePlayerLeft = (data) => {
      console.log("WS: Player left:", data.player);
      // This event might be primarily for logging or displaying in-game notifications,
      // as `room_state_update` will also be sent concurrently.
    };
    onSocketEvent("player_left", this.handlePlayerLeft);
  }

  /**
   * Cleans up WebSocket listeners and disconnects the WebSocket connection.
   * This is crucial for preventing memory leaks and ensuring proper resource management
   * when the scene is no longer active.
   */
  teardownWebSocketListeners() {
    offSocketEvent("room_state_update", this.handleRoomStateUpdate);
    offSocketEvent("room_closed", this.handleRoomClosed);
    offSocketEvent("player_left", this.handlePlayerLeft);
    disconnectSocket(); // Close the WebSocket connection.
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
