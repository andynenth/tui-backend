// frontend/scenes/GameScene.js - New Architecture Only

import { Container } from "pixi.js";
import { GameEvents } from "../SceneFSM.js";
import { SocketManager } from "../network/SocketManager.js";

// New architecture imports
import { GameStateManager } from "../game/GameStateManager.js";
import { GamePhaseManager } from "../game/GamePhaseManager.js";
import { GameEventHandler } from "../game/handlers/GameEventHandler.js";
import { UserInputHandler } from "../game/handlers/UserInputHandler.js";
import { GameUIRenderer } from "./game/GameUIRenderer.js";

/**
 * GameScene - Clean implementation using only new architecture
 *
 * Responsibilities:
 * - Initialize game components
 * - Coordinate between managers
 * - Handle scene lifecycle
 */
export class GameScene extends Container {
  constructor(roomId, playerName, gameData, triggerFSMEvent) {
    super();

    this.roomId = roomId;
    this.playerName = playerName;
    this.gameData = gameData;
    this.triggerFSMEvent = triggerFSMEvent;

    console.log("🔵 Entered GameScene (New Architecture)");
    console.log("📊 Game data:", gameData);

    this._initialize();
  }

  /**
   * Initialize all game components
   */
  async _initialize() {
    try {
      console.log("🚀 Initializing game components...");

      // 1. Create state manager
      this.stateManager = new GameStateManager(
        this.roomId,
        this.playerName,
        this.gameData
      );
      console.log("✅ GameStateManager initialized");

      // 2. Create socket manager
      this.socketManager = new SocketManager();
      console.log("✅ SocketManager initialized");

      // 3. Create UI renderer
      this.uiRenderer = new GameUIRenderer(this);
      console.log("✅ GameUIRenderer initialized");

      // 4. Create phase manager
      this.phaseManager = new GamePhaseManager(
        this.stateManager,
        this.socketManager,
        this.uiRenderer
      );
      console.log("✅ GamePhaseManager initialized");

      // 5. Create event handler
      this.eventHandler = new GameEventHandler(
        this.stateManager,
        this.phaseManager,
        this.socketManager
      );
      console.log("✅ GameEventHandler initialized");

      // 6. Create input handler
      // NOT USING RN
      this.inputHandler = new UserInputHandler(
        this.stateManager,
        this.phaseManager,
        this.socketManager,
        this.uiRenderer
      );
      console.log("✅ UserInputHandler initialized");

      // 7. Connect to game socket
      await this.eventHandler.connect();
      console.log("✅ Connected to game socket");

      // 8. Initialize UI
      await this.uiRenderer.initialize(this.gameData);
      console.log("✅ UI initialized");

      // 9. Set up event listeners
      this._setupEventListeners();
      console.log("✅ Event listeners set up");

      // 10. Start game based on initial state
      this._startInitialPhase();

      console.log("🎮 Game initialization complete!");
    } catch (error) {
      console.error("❌ Failed to initialize game:", error);
      this.handleInitializationError(error);
    }
  }

  /**
   * Set up event listeners
   */
  _setupEventListeners() {
    // Debug: See if events are being received at all
    this.socketManager.on("redeal_phase_started", (data) => {
      console.log("🔴 redeal_phase_started received in GameScene!", data);
      console.log(
        "Current phase:",
        this.phaseManager.getCurrentPhase()?.constructor.name
      );
    });
    // Listen for game ending events
    this.stateManager.on("gameEnded", (data) => {
      this.handleGameEnd(data);
    });

    // Listen for room closed events
    this.stateManager.on("roomClosed", (data) => {
      this.handleRoomClosed(data);
    });

    // Listen for player quit
    this.stateManager.on("playerQuit", () => {
      this.handlePlayerQuit();
    });

    // Listen for phase transitions
    this.phaseManager.on("phaseChanged", (data) => {
      console.log(`🔄 Phase changed: ${data.from} → ${data.to}`);
    });

    // DEBUG: Monitor all redeal-related events
    const redealEvents = [
      "new_hand",
      "redeal_new_hand",
      "player_redealt",
      "hand_updated",
    ];

    redealEvents.forEach((eventName) => {
      this.socketManager.on(eventName, (data) => {
        console.log(`🃏 [DEBUG] ${eventName} event received:`, data);
      });
    });

    // Monitor game state updates too
    this.socketManager.on("game_state_updated", (data) => {
      console.log("📊 [DEBUG] Game state updated:", data);
      if (data.hands) {
        console.log("🃏 New hands in state update:", data.hands);
      }
    });
  }

  /**
   * Start the appropriate initial phase
   */
  _startInitialPhase() {
    // Debug: Check what data we have
    console.log("🔍 DEBUG: Full gameData:", this.gameData);

    const { need_redeal, starter, round, weak_players, players, hands } =
      this.gameData;

    console.log("🔍 DEBUG: Extracted values:");
    console.log("  need_redeal:", need_redeal);
    console.log("  starter:", starter);
    console.log("  round:", round);
    console.log("  weak_players:", weak_players);
    console.log("  hands available:", hands ? Object.keys(hands) : "none");

    // Manual redeal check if backend didn't provide it
    let shouldCheckRedeal = need_redeal;

    if (need_redeal === undefined && round === 1) {
      console.log("🔍 DEBUG: need_redeal not provided, checking manually...");
      console.log("🔍 DEBUG: players array:", players);
      console.log("🔍 DEBUG: hands object keys:", Object.keys(hands || {}));

      // Check if any player (including ourselves) has weak hand
      if (hands && players) {
        shouldCheckRedeal = false; // Initialize to false

        for (const player of players) {
          console.log(`🔍 DEBUG: Checking player:`, player);
          const playerName = player.name || player;
          const playerHand = hands[playerName] || [];

          console.log(`🔍 DEBUG: ${playerName} hand:`, playerHand);

          const hasStrongPiece = playerHand.some((card) => {
            const match = card.match(/\((\d+)\)/);
            const points = match ? parseInt(match[1]) : 0;
            console.log(`🔍 DEBUG: Card "${card}" has ${points} points`);
            return points > 9;
          });

          console.log(
            `🔍 DEBUG: ${playerName} hasStrongPiece:`,
            hasStrongPiece
          );

          if (!hasStrongPiece) {
            console.log(`🔍 DEBUG: ${playerName} has weak hand - NEED REDEAL!`);
            shouldCheckRedeal = true;
            break;
          }
        }
      } else {
        console.log("🔍 DEBUG: Missing hands or players data");
      }
    }

    console.log("🔍 DEBUG: Final shouldCheckRedeal:", shouldCheckRedeal);

    if (shouldCheckRedeal) {
      console.log("🔄 Some players have weak hands, checking redeal...");
      this.phaseManager.transitionTo("redeal");
    } else if (starter) {
      console.log("📣 No redeal needed, starting with declaration phase");
      this.phaseManager.transitionTo("declaration");
    } else {
      console.log("⚠️ Unknown initial state, starting with waiting phase");
      this.phaseManager.transitionTo("waiting");
    }
  }

  /**
   * Handle initialization errors
   */
  handleInitializationError(error) {
    console.error("Failed to initialize game:", error);

    // Show error message to user
    if (this.uiRenderer) {
      this.uiRenderer.showError(
        "Failed to initialize game. Returning to lobby..."
      );
    }

    // Return to lobby after delay
    setTimeout(() => {
      this.triggerFSMEvent(GameEvents.EXIT_ROOM);
    }, 3000);
  }

  /**
   * Handle game ending
   */
  handleGameEnd(data) {
    console.log("🏁 Game ended, showing results");

    // Show game results
    if (this.uiRenderer) {
      this.uiRenderer.showGameResults(data);
    }

    // Return to lobby after delay
    setTimeout(() => {
      this.cleanup();
      this.triggerFSMEvent(GameEvents.EXIT_ROOM);
    }, 5000);
  }

  /**
   * Handle room closed
   */
  handleRoomClosed(data) {
    console.log("🚪 Room closed:", data.message);

    // Show message to user
    if (this.uiRenderer) {
      this.uiRenderer.showError(data.message || "Room closed");
    }

    // Clean up and return to lobby
    setTimeout(() => {
      this.cleanup();
      this.triggerFSMEvent(GameEvents.EXIT_ROOM);
    }, 2000);
  }

  /**
   * Handle player quitting
   */
  handlePlayerQuit() {
    console.log("👋 Player quit");

    // Notify server
    fetch(`/api/exit-room?room_id=${this.roomId}&name=${this.playerName}`, {
      method: "POST",
    }).catch((err) => console.error("Failed to notify exit:", err));

    // Clean up and return
    this.cleanup();
    this.triggerFSMEvent(GameEvents.EXIT_ROOM);
  }

  /**
   * Clean up resources
   */
  cleanup() {
    console.log("🧹 Cleaning up GameScene");

    // Clean up in reverse order of creation
    if (this.inputHandler) {
      this.inputHandler.destroy();
      this.inputHandler = null;
    }

    if (this.eventHandler) {
      this.eventHandler.disconnect();
      this.eventHandler = null;
    }

    if (this.phaseManager) {
      this.phaseManager.destroy();
      this.phaseManager = null;
    }

    if (this.uiRenderer) {
      this.uiRenderer.destroy();
      this.uiRenderer = null;
    }

    if (this.socketManager) {
      this.socketManager.disconnect();
      this.socketManager = null;
    }

    if (this.stateManager) {
      // Use clear() instead of removeAllListeners()
      // based on your EventEmitter implementation
      this.stateManager.clear();
      this.stateManager = null;
    }
  }

  /**
   * Destroy scene
   */
  destroy(options) {
    console.log("💥 Destroying GameScene");

    this.cleanup();
    super.destroy(options);
  }
}

/**
 * ARCHITECTURE SUMMARY
 *
 * This GameScene acts as a thin orchestrator that:
 * 1. Initializes all game components in the correct order
 * 2. Sets up communication between components
 * 3. Handles scene lifecycle (cleanup, transitions)
 * 4. Delegates all game logic to specialized components
 *
 * Component Responsibilities:
 * - GameStateManager: Maintains game state
 * - GamePhaseManager: Manages phase transitions
 * - GameEventHandler: Handles socket events
 * - UserInputHandler: Processes user input
 * - GameUIRenderer: Renders the game UI
 *
 * Benefits:
 * - Clear separation of concerns
 * - Easy to test each component
 * - No more 700+ line monolithic file
 * - Each component can be modified independently
 */
