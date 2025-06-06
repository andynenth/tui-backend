// frontend/scenes/GameScene.js - Fixed turn order tracking

import { Container, Text, TextStyle } from "pixi.js";
import { GameButton } from "../components/GameButton.js";
import { GameTextbox } from "../components/GameTextbox.js";
import { GameEvents } from "../SceneFSM.js";
import {
  on as onSocketEvent,
  off as offSocketEvent,
  emit as emitSocketEvent,
} from "../socketManager.js";

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
    this.currentTurnStarter = this.gameData.starter; // Start with round starter
    this.turnOrder = [];
    
    // Simple UI setup
    this.layout = {
      width: "100%",
      height: "100%",
      flexDirection: "column",
      alignItems: "center",
      padding: 16,
      gap: 16,
    };

    // Title
    const title = new Text({
      text: `Game - Round ${this.currentRound}`,
      style: new TextStyle({ fill: "#ffffff", fontSize: 24 }),
    });
    
    // Console output area (just for visual reference)
    this.outputText = new Text({
      text: "Check console for game output",
      style: new TextStyle({ fill: "#aaaaaa", fontSize: 14 }),
    });
    
    // Input area
    this.inputContainer = new Container();
    this.inputContainer.layout = {
      flexDirection: "row",
      gap: 8,
      alignItems: "center",
    };
    
    // Text input
    this.textInput = new GameTextbox({
      placeholder: "Enter value",
      width: 200,
    });
    
    // Submit button
    this.submitButton = new GameButton({
      label: "Submit",
      onClick: () => this.handleSubmit(),
    });
    
    // Initially hide input
    this.inputContainer.visible = false;
    
    this.inputContainer.addChild(this.textInput.view, this.submitButton.view);
    
    // Exit button
    const exitButton = new GameButton({
      label: "Exit Game",
      bgColor: 0xaa0000,
      onClick: () => {
        if (confirm("Are you sure you want to exit?")) {
          this.triggerFSMEvent(GameEvents.EXIT_ROOM);
        }
      },
    });
    
    this.addChild(title, this.outputText, this.inputContainer, exitButton.view);
    
    // Setup WebSocket listeners
    this.setupWebSocketListeners();
    
    // Start the game
    this.printRoundStart();
    this.checkForRedeal();
  }

  printRoundStart() {
    console.log("=".repeat(50));
    console.log(`🎮 ROUND ${this.currentRound}`);
    console.log("=".repeat(50));
    
    // Determine starter
    const starter = this.gameData.starter;
    let startReason = "Won previous round";
    
    if (this.currentRound === 1) {
      const starterHand = this.gameData.hands[starter];
      if (starterHand?.some(card => card.includes("GENERAL_RED"))) {
        startReason = "Has RED GENERAL";
      }
    }
    
    console.log(`${starter} starts the game (${startReason})\n`);
  }

  checkForRedeal() {
    const hasStrongPiece = this.myHand.some(card => {
      const match = card.match(/\((\d+)\)/);
      return match && parseInt(match[1]) > 9;
    });

    if (!hasStrongPiece && !this.myPlayerData.is_bot) {
      console.log("⚠️ You have no pieces > 9 points. You can request a redeal.");
      this.showInput("Request redeal? (y/n)", (answer) => {
        if (answer.toLowerCase() === 'y') {
          this.requestRedeal();
        } else {
          this.startDeclarationPhase();
        }
      });
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
        console.log(`🔄 ${this.playerName} has requested a redeal!`);
        console.log(`Score multiplier: x${result.multiplier}`);
      }
    } catch (err) {
      console.error("Failed to request redeal:", err);
    }
  }

  startDeclarationPhase() {
    console.log("\n🔸 --- Declare Phase ---\n");
    this.currentPhase = "DECLARATION";
    
    // Initialize all declarations as null
    this.players.forEach(p => {
      this.declarations[p.name] = null;
    });
    
    // Check if it's my turn to declare
    this.checkDeclarationTurn();
  }

  checkDeclarationTurn() {
    // Get declaration order starting from starter
    const starter = this.gameData.starter;
    const starterIndex = this.players.findIndex(p => p.name === starter);
    const orderedPlayers = [
      ...this.players.slice(starterIndex),
      ...this.players.slice(0, starterIndex)
    ];
    
    // Check if I've already declared
    if (this.declarations[this.playerName] !== null) {
      return;
    }
    
    // Check if it's my turn (all players before me have declared)
    const myIndex = orderedPlayers.findIndex(p => p.name === this.playerName);
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

  promptDeclaration() {
    console.log("\n🃏 Your hand:");
    this.myHand.forEach((card, i) => {
      console.log(`${i}: ${card}`);
    });
    
    // Calculate valid options
    const declaredSoFar = Object.values(this.declarations)
      .filter(v => v !== null)
      .reduce((sum, v) => sum + v, 0);
    
    const isLast = Object.values(this.declarations)
      .filter(v => v === null).length === 1;
    
    let options = [0, 1, 2, 3, 4, 5, 6, 7, 8];
    
    if (isLast) {
      const forbidden = 8 - declaredSoFar;
      options = options.filter(v => v !== forbidden);
    }
    
    // Check zero streak
    const myPlayer = this.players.find(p => p.name === this.playerName);
    if (myPlayer.zero_declares_in_a_row >= 2) {
      options = options.filter(v => v > 0);
      console.log("⚠️ You must declare at least 1 (declared 0 twice in a row)");
    }
    
    console.log(`\n🟨 ${this.playerName}, declare how many piles (options: ${options}):`);
    
    this.showInput("Your declaration", async (value) => {
      const num = parseInt(value);
      if (options.includes(num)) {
        await this.makeDeclaration(num);
      } else {
        console.log(`❌ Invalid declaration. Choose from ${options}`);
        this.promptDeclaration();
      }
    });
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
        console.log(`✅ You declared ${value}`);
      }
    } catch (err) {
      console.error("Failed to declare:", err);
    }
  }

  startTurnPhase() {
    console.log("\n🎯 --- Turn Phase ---");
    this.currentPhase = "TURN_PLAY";
    this.currentTurnNumber = 0;
    this.currentTurnPlays = [];
    
    // Set initial turn order based on round starter
    this.currentTurnStarter = this.gameData.starter;
    this.updateTurnOrder();
    
    this.checkTurnPlay();
  }

  updateTurnOrder() {
    // Create turn order starting from current turn starter
    const starterIndex = this.players.findIndex(p => p.name === this.currentTurnStarter);
    this.turnOrder = [
      ...this.players.slice(starterIndex),
      ...this.players.slice(0, starterIndex)
    ];
    
    console.log(`📍 Turn order: ${this.turnOrder.map(p => p.name).join(" → ")}`);
  }

  checkTurnPlay() {
    // Check if I need to play based on turn order
    const myOrderIndex = this.turnOrder.findIndex(p => p.name === this.playerName);
    const playsCompleted = this.currentTurnPlays.length;
    
    // Check if it's my position in the turn order
    if (myOrderIndex === playsCompleted && !this.waitingForInput && this.myHand.length > 0) {
      const isFirstPlayer = playsCompleted === 0;
      this.promptTurnPlay(isFirstPlayer);
    }
  }

  promptTurnPlay(isFirstPlayer) {
    console.log(`\n--- Turn ${this.currentTurnNumber + 1} ---`);
    
    if (isFirstPlayer) {
      console.log(`${this.playerName} leads this turn`);
    }
    
    console.log("\n🃏 Your hand:");
    this.myHand.forEach((card, i) => {
      console.log(`${i}: ${card}`);
    });
    console.log(`${this.playerName} declares ${this.declarations[this.playerName]} piles.`);
    
    if (isFirstPlayer) {
      console.log("You are first player - play 1-6 pieces");
    } else {
      console.log(`You must play exactly ${this.requiredPieceCount} pieces`);
    }
    
    this.showInput("Enter piece indices (space-separated)", async (input) => {
      const indices = input.trim().split(/\s+/).map(i => parseInt(i));
      
      // Validate
      if (indices.some(i => isNaN(i) || i < 0 || i >= this.myHand.length)) {
        console.log("❌ Invalid indices");
        this.promptTurnPlay(isFirstPlayer);
        return;
      }
      
      if (isFirstPlayer) {
        if (indices.length < 1 || indices.length > 6) {
          console.log("❌ Must play 1-6 pieces");
          this.promptTurnPlay(isFirstPlayer);
          return;
        }
      } else {
        if (indices.length !== this.requiredPieceCount) {
          console.log(`❌ Must play exactly ${this.requiredPieceCount} pieces`);
          this.promptTurnPlay(isFirstPlayer);
          return;
        }
      }
      
      await this.playTurn(indices);
    });
  }

  async playTurn(indices) {
    try {
      const pieces = indices.map(i => this.myHand[i]);
      console.log(`Playing: ${pieces.join(", ")}`);
      
      // Send indices as comma-separated string in query parameter
      const url = `/api/play-turn?room_id=${this.roomId}&player_name=${this.playerName}&piece_indexes=${indices.join(',')}`;
      const response = await fetch(url, { method: "POST" });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error("Server error:", errorText);
        return;
      }
      
      const result = await response.json();
      
      if (result.status === "waiting" || result.status === "resolved") {
        // Remove played pieces from hand
        indices.sort((a, b) => b - a).forEach(i => {
          this.myHand.splice(i, 1);
        });
      }
    } catch (err) {
      console.error("Failed to play turn:", err);
    }
  }

  showInput(prompt, callback) {
    this.waitingForInput = true;
    this.currentCallback = callback;
    
    // Update UI
    this.outputText.text = prompt;
    this.textInput.setText("");
    this.inputContainer.visible = true;
    this.textInput.focus();
  }

  hideInput() {
    this.waitingForInput = false;
    this.currentCallback = null;
    this.inputContainer.visible = false;
    this.outputText.text = "Check console for game output";
  }

  handleSubmit() {
    if (this.currentCallback) {
      const value = this.textInput.getText().trim();
      if (value) {
        const callback = this.currentCallback;
        this.hideInput();
        callback(value);
      }
    }
  }

  setupWebSocketListeners() {
    // Handle declarations
    this.handleDeclare = (data) => {
      console.log(`📢 ${data.player}${data.is_bot ? " 🤖" : ""} declared ${data.value}`);
      this.declarations[data.player] = data.value;
      
      // Check if all declared
      const allDeclared = this.players.every(p => this.declarations[p.name] !== null);
      
      if (allDeclared) {
        console.log("\n✅ All players declared!");
        const total = Object.values(this.declarations).reduce((sum, v) => sum + v, 0);
        console.log(`Total declarations: ${total}`);
        
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
      console.log(`${data.player}'s play: [${data.pieces.join(", ")}] → ${validStr} (${data.play_type || "INVALID"})`);
      
      // Track plays
      this.currentTurnPlays.push({
        player: data.player,
        pieces: data.pieces,
        valid: data.valid
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
      
      // Show plays in turn order
      this.turnOrder.forEach(player => {
        const play = data.plays.find(p => p.player === player.name);
        if (play) {
          const declared = this.declarations[play.player];
          console.log(`  - ${play.player}: [${play.pieces.join(", ")}] ${play.is_valid ? "✅" : "❌"} [?/${declared}]`);
        }
      });
      
      if (data.winner) {
        console.log(`\n>>> 🏆 ${data.winner} wins the turn with [${data.plays.find(p => p.player === data.winner).pieces.join(", ")}] (+${data.pile_count} pts).`);
        // Update turn starter for next turn
        this.currentTurnStarter = data.winner;
      } else {
        console.log("\n>>> ⚠️ No one wins the turn.");
      }
      
      // Reset for next turn
      this.currentTurnPlays = [];
      this.currentTurnNumber++;
      this.requiredPieceCount = null;
      
      // Continue if we have pieces
      if (this.myHand.length > 0) {
        // Update turn order for next turn
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
          console.log(`${player} → declared ${scoreData.declared}, got ${scoreData.actual} → ${scoreData.delta >= 0 ? "+" : ""}${scoreData.delta} pts (×${scoreData.multiplier || 1}), total: ${scoreData.total}`);
        });
      }
      
      if (data.game_over) {
        console.log("\n🎮 GAME OVER!");
        if (data.winners && data.winners.length > 0) {
          console.log(`🏆 Winner: ${data.winners.join(", ")}`);
        }
      }
    };
    onSocketEvent("score", this.handleScore);

    // Handle redeal
    this.handleRedeal = (data) => {
      console.log(`\n🔄 ${data.player} has requested a redeal!`);
      console.log(`Score multiplier is now x${data.multiplier}`);
    };
    onSocketEvent("redeal", this.handleRedeal);

    // Handle new round after redeal
    this.handleStartRound = (data) => {
      console.log("\n🆕 New round started (after redeal)");
      
      // Update game state
      this.currentRound = data.round;
      this.myHand = data.hands[this.playerName] || [];
      this.gameData = data;
      
      // Reset declarations
      this.declarations = {};
      this.players.forEach(p => {
        this.declarations[p.name] = null;
      });
      
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