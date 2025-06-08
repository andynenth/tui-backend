// frontend/scenes/GameScene.js - Simplified CLI-style version

import { Container, Text, TextStyle } from "pixi.js";
import { GameButton } from "../components/GameButton.js";
import { GameTextbox } from "../components/GameTextbox.js";
import { GameEvents } from "../SceneFSM.js";
import {
  on as onSocketEvent,
  off as offSocketEvent,
  emit as emitSocketEvent,
} from "../network/index.js";

export class GameScene extends Container {
  constructor(roomId, playerName, gameData, triggerFSMEvent) {
    super();

    this.roomId = roomId;
    this.playerName = playerName;
    this.gameData = gameData;
    this.triggerFSMEvent = triggerFSMEvent;

    // Game state
    this.currentRound = gameData.round || 1;
    this.players = gameData.players || [];
    this.myHand = [];
    this.currentPhase = "ROUND_START";

    // Find my player data
    this.myPlayerData = this.players.find((p) => p.name === this.playerName);
    this.myHand = gameData.hands?.[this.playerName] || [];

    // Track game state
    this.declarations = {};
    this.currentTurnNumber = 0;
    this.waitingForInput = false;
    this.requiredPieceCount = null;
    this.currentTurnPlays = [];

    // Track turn order
    this.currentTurnStarter = this.gameData.starter;
    this.turnOrder = [];

    this.socketManager = new SocketManager({
      enableMessageQueue: true,
      maxQueueSize: 50, // Keep last 50 moves
    });

    // Simple CLI-style UI
    this.layout = {
      width: "100%",
      height: "100%",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      padding: 20,
    };

    // Status text (minimal info)
    this.statusText = new Text({
      text: `Game Room: ${this.roomId}`,
      style: new TextStyle({ fill: "#666666", fontSize: 14 }),
    });

    // Input container (hidden by default)
    this.inputContainer = new Container();
    this.inputContainer.layout = {
      flexDirection: "row",
      gap: 8,
      alignItems: "center",
    };

    // Text input
    this.textInput = new GameTextbox({
      placeholder: "Your input",
      width: 300,
    });

    // Submit button
    this.submitButton = new GameButton({
      label: "Enter",
      width: 80,
      onClick: () => this.handleSubmit(),
    });

    this.inputContainer.addChild(this.textInput.view, this.submitButton.view);
    this.inputContainer.visible = false;

    // Add minimal UI elements
    this.addChild(this.statusText, this.inputContainer);

    // Setup WebSocket listeners
    this.setupWebSocketListeners();

    // Start the game
    this.printRoundStart();
    this.checkForRedeal();
  }

  // ===== CONSOLE OUTPUT METHODS =====

  printRoundStart() {
    console.log("\n" + "=".repeat(50));
    console.log(`ROUND ${this.currentRound}`);
    console.log("=".repeat(50));

    const starter = this.gameData.starter;
    let startReason = "Won previous round";

    if (this.currentRound === 1) {
      const starterHand = this.gameData.hands[starter];
      if (starterHand?.some((card) => card.includes("GENERAL_RED"))) {
        startReason = "Has GENERAL_RED";
      }
    }

    console.log(`${starter} starts the game (${startReason})\n`);
  }

  printHand() {
    console.log("\n🃏 " + this.playerName + " hand:");
    this.myHand.forEach((card, i) => {
      console.log(`${i}: ${card}`);
    });
  }

  // ===== INPUT HANDLING =====

  async showInput(prompt, validator = null) {
    return new Promise((resolve) => {
      console.log(`\n${prompt}`);

      this.waitingForInput = true;
      this.inputContainer.visible = true;
      this.textInput.setText("");
      this.textInput.focus();

      // Store the resolver and validator
      this.currentInputResolver = resolve;
      this.currentInputValidator = validator;
    });
  }

  handleSubmit() {
    if (!this.waitingForInput || !this.currentInputResolver) return;

    const value = this.textInput.getText().trim();
    if (!value) return;

    // Validate input if validator provided
    if (this.currentInputValidator) {
      const validationResult = this.currentInputValidator(value);
      if (!validationResult.valid) {
        console.log(`❌ ${validationResult.message}`);
        return;
      }
    }

    // Hide input and resolve
    this.inputContainer.visible = false;
    this.waitingForInput = false;
    const resolver = this.currentInputResolver;
    this.currentInputResolver = null;
    this.currentInputValidator = null;

    resolver(value);
  }

  // ===== GAME PHASES =====

  async checkForRedeal() {
    const hasStrongPiece = this.myHand.some((card) => {
      const match = card.match(/\((\d+)\)/);
      return match && parseInt(match[1]) > 9;
    });

    if (!hasStrongPiece && !this.myPlayerData.is_bot) {
      const answer = await this.showInput(
        "⚠️ You have no pieces > 9 points. Request redeal? (y/n):",
        (input) => {
          const lower = input.toLowerCase();
          return {
            valid: lower === "y" || lower === "n",
            message: "Please enter 'y' or 'n'",
          };
        }
      );

      if (answer.toLowerCase() === "y") {
        await this.requestRedeal();
      } else {
        this.startDeclarationPhase();
      }
    } else {
      this.startDeclarationPhase();
    }
  }

  async requestRedeal() {
    try {
      const response = await fetch(
        `/api/redeal?room_id=${this.roomId}&player_name=${this.playerName}`,
        { method: "POST" }
      );
      const result = await response.json();

      if (result.redeal_allowed) {
        console.log(`\n🔄 ${this.playerName} has requested a redeal!`);
        console.log(`Score multiplier: x${result.multiplier}`);
      }
    } catch (err) {
      console.error("Failed to request redeal:", err);
    }
  }

  startDeclarationPhase() {
    console.log("\n🔸 --- Declare Phase ---");
    this.currentPhase = "DECLARATION";

    // Initialize all declarations as null
    this.players.forEach((p) => {
      this.declarations[p.name] = null;
    });

    // Check if it's my turn to declare
    this.checkDeclarationTurn();
  }

  checkDeclarationTurn() {
    // Get declaration order starting from starter
    const starter = this.gameData.starter;
    const starterIndex = this.players.findIndex((p) => p.name === starter);
    const orderedPlayers = [
      ...this.players.slice(starterIndex),
      ...this.players.slice(0, starterIndex),
    ];

    // Check if I've already declared
    if (this.declarations[this.playerName] !== null) {
      return;
    }

    // Check if it's my turn (all players before me have declared)
    const myIndex = orderedPlayers.findIndex((p) => p.name === this.playerName);
    let myTurn = true;

    for (let i = 0; i < myIndex; i++) {
      if (this.declarations[orderedPlayers[i].name] === null) {
        myTurn = false;
        break;
      }
    }

    if (myTurn && !this.waitingForInput) {
      this.promptDeclaration();
    }
  }

  async promptDeclaration() {
    this.printHand();

    // Calculate valid options
    const declaredSoFar = Object.values(this.declarations)
      .filter((v) => v !== null)
      .reduce((sum, v) => sum + v, 0);

    const isLast =
      Object.values(this.declarations).filter((v) => v === null).length === 1;

    let options = [0, 1, 2, 3, 4, 5, 6, 7, 8];

    if (isLast) {
      const forbidden = 8 - declaredSoFar;
      options = options.filter((v) => v !== forbidden);
    }

    // Check zero streak
    const myPlayer = this.players.find((p) => p.name === this.playerName);
    if (myPlayer.zero_declares_in_a_row >= 2) {
      options = options.filter((v) => v > 0);
      console.log(
        "\n⚠️ You must declare at least 1 (declared 0 twice in a row)"
      );
    }

    console.log(
      `\n🟨 ${
        this.playerName
      }, declare how many piles you want to capture (options: [${options.join(
        ", "
      )}]):`
    );

    const value = await this.showInput("Your declaration:", (input) => {
      const num = parseInt(input);
      if (isNaN(num)) {
        return { valid: false, message: "Please enter a number" };
      }
      if (!options.includes(num)) {
        return {
          valid: false,
          message: `Invalid declaration. Choose from [${options.join(", ")}]`,
        };
      }
      return { valid: true };
    });

    await this.makeDeclaration(parseInt(value));
  }

  async makeDeclaration(value) {
    try {
      const response = await fetch(
        `/api/declare?room_id=${this.roomId}&player_name=${this.playerName}&value=${value}`,
        { method: "POST" }
      );
      const result = await response.json();

      if (result.status === "ok") {
        this.declarations[this.playerName] = value;
      }
    } catch (err) {
      console.error("Failed to declare:", err);
    }
  }

  startTurnPhase() {
    console.log("\n--- Turn Phase ---");
    this.currentPhase = "TURN_PLAY";
    this.currentTurnNumber = 1;
    this.currentTurnPlays = [];

    // Set initial turn order based on round starter
    this.currentTurnStarter = this.gameData.starter;
    this.updateTurnOrder();

    this.checkTurnPlay();
  }

  updateTurnOrder() {
    // Create turn order starting from current turn starter
    const starterIndex = this.players.findIndex(
      (p) => p.name === this.currentTurnStarter
    );
    this.turnOrder = [
      ...this.players.slice(starterIndex),
      ...this.players.slice(0, starterIndex),
    ];
  }

  checkTurnPlay() {
    // Check if I need to play based on turn order
    const myOrderIndex = this.turnOrder.findIndex(
      (p) => p.name === this.playerName
    );
    const playsCompleted = this.currentTurnPlays.length;

    // Check if it's my position in the turn order
    if (
      myOrderIndex === playsCompleted &&
      !this.waitingForInput &&
      this.myHand.length > 0
    ) {
      const isFirstPlayer = playsCompleted === 0;
      this.promptTurnPlay(isFirstPlayer);
    }
  }

  async promptTurnPlay(isFirstPlayer) {
    console.log(`\n--- Turn ${this.currentTurnNumber} ---`);

    this.printHand();
    console.log(
      `${this.playerName} declares ${this.declarations[this.playerName]} piles.`
    );

    const prompt = isFirstPlayer
      ? "Enter the indices of pieces you want to play (space-separated):"
      : `Enter the indices of pieces you want to play (must be exactly ${this.requiredPieceCount} pieces):`;

    const input = await this.showInput(prompt, (value) => {
      const indices = value
        .trim()
        .split(/\s+/)
        .map((i) => parseInt(i));

      if (indices.some((i) => isNaN(i) || i < 0 || i >= this.myHand.length)) {
        return {
          valid: false,
          message: "Invalid indices. Please check your hand.",
        };
      }

      if (isFirstPlayer) {
        if (indices.length < 1 || indices.length > 6) {
          return { valid: false, message: "Must play 1-6 pieces" };
        }
      } else {
        if (indices.length !== this.requiredPieceCount) {
          return {
            valid: false,
            message: `Must play exactly ${this.requiredPieceCount} pieces`,
          };
        }
      }

      return { valid: true };
    });

    const indices = input
      .trim()
      .split(/\s+/)
      .map((i) => parseInt(i));
    await this.playTurn(indices);
  }

  async playTurn(indices) {
    try {
      const pieces = indices.map((i) => this.myHand[i]);

      const url = `/api/play-turn?room_id=${this.roomId}&player_name=${
        this.playerName
      }&piece_indexes=${indices.join(",")}`;
      const response = await fetch(url, { method: "POST" });

      if (!response.ok) {
        const errorText = await response.text();
        console.error("Server error:", errorText);
        return;
      }

      const result = await response.json();

      if (result.status === "waiting" || result.status === "resolved") {
        // Remove played pieces from hand
        indices
          .sort((a, b) => b - a)
          .forEach((i) => {
            this.myHand.splice(i, 1);
          });
      }
    } catch (err) {
      console.error("Failed to play turn:", err);
    }
  }

  checkRoundComplete() {
    if (this.myHand.length === 0) {
      console.log("\n🏁 Your hand is empty - waiting for round scoring...");
    }
  }

  // ===== WEBSOCKET HANDLERS =====

  setupWebSocketListeners() {
    // Handle declarations
    this.handleDeclare = (data) => {
      if (data.is_bot) {
        console.log(`🤖 ${data.player} declares ${data.value} piles.`);
      }
      this.declarations[data.player] = data.value;

      // Check if all declared
      const allDeclared = this.players.every(
        (p) => this.declarations[p.name] !== null
      );

      if (allDeclared) {
        const total = Object.values(this.declarations).reduce(
          (sum, v) => sum + v,
          0
        );
        console.log(`\n✅ All players declared! Total: ${total}`);

        setTimeout(() => {
          this.startTurnPhase();
        }, 1000);
      } else {
        this.checkDeclarationTurn();
      }
    };
    onSocketEvent("declare", this.handleDeclare);

    // Handle plays
    this.handlePlay = (data) => {
      const validStr = data.valid ? "✅" : "❌";
      console.log(
        `${data.player}'s play: [${data.pieces.join(", ")}] → ${validStr} (${
          data.play_type || "INVALID"
        })`
      );

      // Track plays
      this.currentTurnPlays.push({
        player: data.player,
        pieces: data.pieces,
        valid: data.valid,
      });

      // Set required count from first play
      if (this.currentTurnPlays.length === 1) {
        this.requiredPieceCount = data.pieces.length;
      }

      // Check if I need to play
      this.checkTurnPlay();
    };
    onSocketEvent("play", this.handlePlay);

    // Handle turn resolution
    this.handleTurnResolved = (data) => {
      console.log("\n🎯 Turn Summary:");

      // Show plays
      data.plays.forEach((play) => {
        const declared = this.declarations[play.player];
        console.log(
          `  - ${play.player}: [${play.pieces.join(", ")}] ${
            play.is_valid ? "✅" : "❌"
          } [?/${declared}]`
        );
      });

      if (data.winner) {
        console.log(
          `\n>>> 🏆 ${data.winner} wins the turn with [${data.plays
            .find((p) => p.player === data.winner)
            .pieces.join(", ")}] (+${data.pile_count} pts).`
        );
        this.currentTurnStarter = data.winner;
      } else {
        console.log("\n>>> ⚠️ No one wins the turn.");
      }

      // Reset for next turn
      this.currentTurnPlays = [];
      this.currentTurnNumber++;
      this.requiredPieceCount = null;

      this.checkRoundComplete();

      // Continue if we have pieces
      if (this.myHand.length > 0) {
        this.updateTurnOrder();
        setTimeout(() => {
          this.checkTurnPlay();
        }, 1000);
      }
    };
    onSocketEvent("turn_resolved", this.handleTurnResolved);

    // Handle round scoring
    this.handleScore = (data) => {
      console.log("\n🏁 --- End of Round ---");
      console.log("\n📊 Round Summary:");

      // Show scoring details
      if (data.summary && data.summary.scores) {
        Object.entries(data.summary.scores).forEach(([player, scoreData]) => {
          console.log(
            `${player} → declared ${scoreData.declared}, got ${
              scoreData.actual
            } → ${scoreData.delta >= 0 ? "+" : ""}${scoreData.delta} pts (×${
              scoreData.multiplier || 1
            }), total: ${scoreData.total}`
          );
        });
      }

      if (data.game_over) {
        console.log("\n🎮 GAME OVER!");
        if (data.winners && data.winners.length > 0) {
          console.log(`🏆 Winner: ${data.winners.join(", ")}`);
        }
      } else {
        console.log("\n⏳ Preparing next round...");
      }
    };
    onSocketEvent("score", this.handleScore);

    // Handle redeal
    this.handleRedeal = (data) => {
      console.log(`\n🔄 ${data.player} has requested a redeal!`);
      console.log(`Score multiplier is now x${data.multiplier}`);
    };
    onSocketEvent("redeal", this.handleRedeal);

    // Handle new round
    this.handleStartRound = (data) => {
      console.log("\n🆕 New round started");

      // Update game state
      this.currentRound = data.round;
      this.myHand = data.hands[this.playerName] || [];
      this.gameData = data;

      // Reset declarations
      this.declarations = {};
      this.players.forEach((p) => {
        this.declarations[p.name] = null;
      });

      // Reset turn tracking
      this.currentTurnNumber = 0;
      this.currentTurnPlays = [];
      this.requiredPieceCount = null;
      this.currentTurnStarter = data.starter;

      // Start over
      this.printRoundStart();
      this.checkForRedeal();
    };
    onSocketEvent("start_round", this.handleStartRound);
  }

  teardownWebSocketListeners() {
    offSocketEvent("declare", this.handleDeclare);
    offSocketEvent("play", this.handlePlay);
    offSocketEvent("turn_resolved", this.handleTurnResolved);
    offSocketEvent("score", this.handleScore);
    offSocketEvent("redeal", this.handleRedeal);
    offSocketEvent("start_round", this.handleStartRound);
  }

  destroy(options) {
    this.teardownWebSocketListeners();
    super.destroy(options);
  }
}
