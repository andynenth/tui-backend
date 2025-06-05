// frontend/scenes/GameScene.js

import { Container, Text, TextStyle } from "pixi.js";
import { GameButton } from "../components/GameButton.js";
import { GameEvents } from "../SceneFSM.js";
import {
  on as onSocketEvent,
  off as offSocketEvent,
  emit as emitSocketEvent,
} from "../socketManager.js";
import { GamePhaseManager, GamePhases } from "../game/GamePhaseManager.js";
import {
  RedealUI,
  DeclarationUI,
  TurnPlayUI,
  TurnResultUI,
  RoundScoreUI,
} from "../game/GameUIComponents.js";

export class GameScene extends Container {
  constructor(roomId, playerName, gameData, triggerFSMEvent) {
    super();
    console.log("=".repeat(50));
    console.log("🎮 GAME STARTED - ROUND " + gameData.round);
    console.log("=".repeat(50));

    // Determine start reason
    let startReason = "Won previous round";
    if (gameData.round === 1) {
      // Check if starter has RED GENERAL
      const starterHand = gameData.hands[gameData.starter];
      if (
        starterHand &&
        starterHand.some((card) => card.includes("GENERAL_RED"))
      ) {
        startReason = "Has RED GENERAL";
      }
    }

    console.log("📍 Game Info:", {
      roomId,
      playerName,
      round: gameData.round,
      starter: gameData.starter,
      startReason,
    });

    console.log("\n👥 Players:");
    gameData.players.forEach((p, i) => {
      console.log(
        `  ${i + 1}. ${p.name}${p.is_bot ? " 🤖" : " 👤"} - Score: ${p.score}`
      );
    });

    console.log("\n🃏 My Hand:", gameData.hands[playerName]);
    console.log("=".repeat(50));

    this.roomId = roomId;
    this.playerName = playerName;
    this.gameData = gameData;
    this.triggerFSMEvent = triggerFSMEvent;

    // Game state
    this.currentRound = gameData.round || 1;
    this.players = gameData.players || [];
    this.myHand = [];
    this.currentPhase = "DEAL"; // DEAL, DECLARE, PLAY, SCORE

    // Find my player data
    this.myPlayerData = this.players.find((p) => p.name === this.playerName);
    this.myHand = gameData.hands?.[this.playerName] || [];

    this.layout = {
      width: "100%",
      height: "100%",
      flexDirection: "column",
      alignItems: "center",
      padding: 16,
      gap: 16,
    };

    this.phaseUIContainer = new Container();
    this.phaseUIContainer.layout = {
      width: "100%",
      flexDirection: "column",
      alignItems: "center",
      marginTop: 20,
    };

    this.setupUI();
    this.phaseManager = new GamePhaseManager(this);
    this.addChild(this.phaseUIContainer);

    // Initialize declarations tracking
    this.declarations = {};
    this.players.forEach((p) => {
      this.declarations[p.name] = null;
    });

    this.phaseManager.setPhase(GamePhases.ROUND_PREPARATION, gameData);

    this.setupWebSocketListeners();

    this.currentPhaseUI = null;
    this.waitingForOthers = false;
    console.log("📊 Initial declarations state:", this.declarations);
  }

  setupUI() {
    // Header
    const header = new Container();
    header.layout = {
      width: "100%",
      flexDirection: "row",
      justifyContent: "space-between",
      alignItems: "center",
    };

    const roundText = new Text({
      text: `Round ${this.currentRound}`,
      style: new TextStyle({ fill: "#ffffff", fontSize: 24 }),
    });

    const scoreText = new Text({
      text: `Score: ${this.myPlayerData?.score || 0}`,
      style: new TextStyle({ fill: "#ffffff", fontSize: 20 }),
      x: 200,
      y: 0,
    });

    header.addChild(roundText, scoreText);

    // Player area
    const playerArea = new Container();
    playerArea.layout = {
      width: "100%",
      flexDirection: "column",
      gap: 8,
      marginTop: 30,
    };

    // Show all players
    this.players.forEach((player) => {
      const playerRow = new Container();
      playerRow.layout = {
        flexDirection: "row",
        gap: 8,
        marginTop: 20,
      };

      const nameText = new Text({
        text: `${player.name}${player.is_bot ? " 🤖" : ""}${
          player.name === this.playerName ? " (You)" : ""
        }`,
        style: new TextStyle({ fill: "#ffffff", fontSize: 16 }),
      });

      const scoreText = new Text({
        text: `${player.score} pts`,
        style: new TextStyle({ fill: "#aaaaaa", fontSize: 16 }),
        x: 200,
        y: 0,
      });

      playerRow.addChild(nameText, scoreText);
      playerArea.addChild(playerRow);
    });

    // Hand area
    const handArea = new Container();
    handArea.layout = {
      width: "100%",
      flexDirection: "column",
      alignItems: "center",
      gap: 8,
      marginTop: 200,
    };

    const handTitle = new Text({
      text: "Your Hand:",
      style: new TextStyle({ fill: "#ffffff", fontSize: 18 }),
    });

    const handContainer = new Container();
    handContainer.layout = {
      flexDirection: "row",
      flexWrap: "wrap",
      gap: 8,
      marginTop: 50,
    };

    // Show cards in hand
    this.myHand.forEach((card, index) => {
      const cardButton = new GameButton({
        label: card,
        width: 80,
        height: 60,
        onClick: () => {
          console.log(`Clicked card: ${card}`);
          // TODO: Implement card selection
        },
      });
      handContainer.addChild(cardButton.view);
    });

    handArea.addChild(handTitle, handContainer);

    // Exit button
    const exitButton = new GameButton({
      label: "Exit Game",
      bgColor: 0xaa0000,
      onClick: () => {
        if (confirm("Are you sure you want to exit the game?")) {
          this.triggerFSMEvent(GameEvents.EXIT_ROOM);
        }
      },
    });

    this.addChild(header, playerArea, handArea, exitButton.view);
  }

  onPhaseChange(phase, data) {
    console.log("\n" + "=".repeat(40));
    console.log(
      `📊 PHASE CHANGE: ${
        this.phaseManager.getCurrentPhase() || "NONE"
      } → ${phase}`
    );
    console.log("=".repeat(40));

    // Clear previous UI
    this.phaseUIContainer.removeChildren();
    this.currentPhaseUI = null;

    switch (phase) {
      case GamePhases.ROUND_PREPARATION:
        console.log("🔄 Checking for redeal conditions...");
        this.checkForRedeal();
        break;

      case GamePhases.DECLARATION:
        console.log("📢 DECLARATION PHASE");
        console.log(
          "📍 Declaration order should follow turn order starting from:",
          this.gameData.starter
        );
        console.log("📍 Expected order:", this.getDeclarationOrder());
        this.showDeclarationUI();
        break;

      case GamePhases.TURN_PLAY:
        console.log("🎯 TURN PLAY PHASE");
        // Initialize first turn with correct starter
        if (this.phaseManager.currentTurn.number === 0) {
          this.phaseManager.startNewTurn(this.gameData.starter);
        }
        this.showTurnPlayUI(data);
        break;

      case GamePhases.TURN_RESOLUTION:
        console.log("🏆 TURN RESOLUTION");
        this.showTurnResultUI(data);
        break;

      case GamePhases.ROUND_SCORING:
        console.log("📊 ROUND SCORING");
        this.showRoundScoreUI(data);
        break;
    }
  }

  getDeclarationOrder() {
    const starter = this.gameData.starter;
    const starterIndex = this.players.findIndex((p) => p.name === starter);

    if (starterIndex === -1) return this.players.map((p) => p.name);

    return [
      ...this.players.slice(starterIndex),
      ...this.players.slice(0, starterIndex),
    ].map((p) => p.name);
  }

  // 4. เพิ่ม methods สำหรับแต่ละ phase
  checkForRedeal() {
    const hasStrongPiece = this.myHand.some((card) => {
      // ตรวจสอบจาก string เช่น "GENERAL_RED(14)"
      const match = card.match(/\((\d+)\)/);
      return match && parseInt(match[1]) > 9;
    });

    if (!hasStrongPiece) {
      this.phaseManager.setPhase(GamePhases.REDEAL_CHECK);
      const ui = new RedealUI(
        () => this.requestRedeal(),
        () => this.skipToDeclaration()
      );
      this.phaseUIContainer.addChild(ui.view);
    } else {
      // ถ้ามีไพ่แรง ข้ามไป declaration
      this.phaseManager.setPhase(GamePhases.DECLARATION);
    }
  }

  showDeclarationUI() {
    // Get expected declaration order
    const expectedOrder = this.getDeclarationOrder();
    const myPosition = expectedOrder.indexOf(this.playerName);

    // Check who should declare now
    let shouldDeclareNow = true;
    for (let i = 0; i < myPosition; i++) {
      const playerName = expectedOrder[i];
      if (this.declarations[playerName] === null) {
        shouldDeclareNow = false;
        console.log(
          `⏳ Waiting for ${playerName} to declare first (position ${i + 1})`
        );
        break;
      }
    }

    // Check if already declared
    if (this.declarations[this.playerName] !== null) {
      console.log("✅ Already declared:", this.declarations[this.playerName]);
      this.showWaitingForDeclarations();
      return;
    }

    if (!shouldDeclareNow) {
      console.log("⏳ Not your turn to declare yet");
      this.showWaitingForDeclarations();
      return;
    }

    console.log(
      "🎯 Your turn to declare (position",
      myPosition + 1,
      "in order)"
    );

    const ui = new DeclarationUI(
      this.playerName,
      this.declarations,
      async (value) => {
        console.log(`📢 Player ${this.playerName} declaring ${value}`);

        // Disable UI immediately
        if (this.currentPhaseUI) {
          this.currentPhaseUI.visible = false;
        }

        // Call API
        await this.makeDeclaration(value);
      }
    );

    this.currentPhaseUI = ui.view;
    this.phaseUIContainer.addChild(ui.view);
  }

  showWaitingForDeclarations() {
    console.log("⏳ Waiting for other players to declare");

    const waitingContainer = new Container();
    waitingContainer.layout = {
      flexDirection: "column",
      alignItems: "center",
      gap: 12,
    };

    const title = new Text({
      text: "⏳ Waiting for other players...",
      style: new TextStyle({ fill: "#ffaa00", fontSize: 20 }),
    });

    // Show current declaration status
    const statusContainer = new Container();
    statusContainer.layout = { flexDirection: "column", gap: 8 };

    this.players.forEach((player) => {
      const declared = this.declarations[player.name];
      const statusText = new Text({
        text: `${player.name}${player.is_bot ? " 🤖" : ""}: ${
          declared !== null ? `Declared ${declared}` : "Thinking..."
        }`,
        style: new TextStyle({
          fill: declared !== null ? "#00ff00" : "#ffffff",
          fontSize: 16,
        }),
      });
      statusContainer.addChild(statusText);
    });

    waitingContainer.addChild(title, statusContainer);
    this.phaseUIContainer.addChild(waitingContainer);

    // Store reference for updates
    this.declarationStatusContainer = statusContainer;
  }

  showTurnPlayUI(data) {
    // ตรวจสอบว่ามี turn data
    if (!this.phaseManager.currentTurn.firstPlayer) {
      console.error("❌ No first player set for turn!");
      // Set first player as starter if not set
      this.phaseManager.startNewTurn(this.gameData.starter);
    }

    const isFirstPlayer = this.phaseManager.isFirstPlayerOfTurn(
      this.playerName
    );
    const requiredCount = this.phaseManager.currentTurn.requiredPieceCount;
    const turnNumber = this.phaseManager.currentTurn.number;

    console.log("\n🎲 TURN", turnNumber);
    console.log(
      "📍 Turn order:",
      this.phaseManager.currentTurn.turnOrder.map((p) => p.name)
    );
    console.log("📍 First player:", this.phaseManager.currentTurn.firstPlayer);

    if (isFirstPlayer) {
      console.log("✅ You are FIRST PLAYER - can play 1-6 pieces");
    } else if (requiredCount) {
      console.log(`⚠️ You must play exactly ${requiredCount} pieces`);
    } else {
      console.log("⏳ Waiting for first player to play...");
    }

    console.log("🃏 Your current hand (" + this.myHand.length + " pieces):");
    this.myHand.forEach((card, i) => {
      console.log(`  [${i}] ${card}`);
    });

    // Main container
    const container = new Container();
    container.layout = {
      flexDirection: "column",
      alignItems: "center",
      gap: 16,
    };

    // Turn info
    const turnInfo = new Text({
      text: `Turn ${turnNumber} - ${this.phaseManager.currentTurn.firstPlayer} leads`,
      style: new TextStyle({ fill: "#ffffff", fontSize: 16 }),
    });
    container.addChild(turnInfo);

    // Turn status display
    this.turnStatusContainer = new Container();
    this.turnStatusContainer.layout = {
      flexDirection: "column",
      gap: 8,
      padding: 10,
      backgroundColor: 0x2a2a2a,
    };

    container.addChild(this.turnStatusContainer);
    this.updateTurnPlaysDisplay();

    // Play UI
    const ui = new TurnPlayUI(
      this.myHand,
      isFirstPlayer,
      requiredCount,
      (selectedIndexes) => {
        console.log("🎯 Playing pieces at indexes:", selectedIndexes);
        console.log(
          "🎯 Pieces:",
          selectedIndexes.map((i) => this.myHand[i])
        );
        this.playSelectedCards(selectedIndexes);
      }
    );

    container.addChild(ui.view);
    this.phaseUIContainer.addChild(container);
  }

  setupWebSocketListeners() {
    // Listen for game events
    this.handleDeclare = (data) => {
      console.log("\n📢 DECLARATION:", data.player, "declared", data.value);

      // Update declarations
      this.declarations[data.player] = data.value;

      // Update waiting UI if visible
      if (this.declarationStatusContainer) {
        this.updateDeclarationStatus();
      }

      // Check if all declared
      const allDeclared = this.players.every(
        (p) => this.declarations[p.name] !== null
      );

      console.log("📊 Declaration status:", {
        declarations: this.declarations,
        allDeclared,
      });

      if (allDeclared) {
        console.log("\n✅ ALL PLAYERS DECLARED!");
        console.log("📊 Final declarations:");
        this.players.forEach((p, i) => {
          const order =
            this.gameData.starter === p.name ? "STARTER" : `Order ${i + 1}`;
          console.log(`  ${p.name}: ${this.declarations[p.name]} (${order})`);
        });

        const total = Object.values(this.declarations).reduce(
          (sum, val) => sum + val,
          0
        );
        console.log(`📊 Total: ${total} ✅ (not 8)`);

        setTimeout(() => {
          console.log("\n➡️ Moving to TURN PLAY phase");
          this.phaseManager.setPhase(GamePhases.TURN_PLAY);
        }, 1000);
      }
    };
    onSocketEvent("declare", this.handleDeclare);

    this.handlePlay = (data) => {
      console.log("\n🎯 PLAY:", data.player, "played", data.pieces);
      console.log("  Valid:", data.valid ? "✅" : "❌");
      console.log("  Type:", data.play_type || "Unknown");

      // Record the play in phase manager
      this.phaseManager.recordPlay(data.player, data.pieces, data.valid);

      // If this is the first play of the turn, set required piece count
      if (this.phaseManager.currentTurn.plays.length === 1) {
        this.phaseManager.setRequiredPieceCount(data.pieces.length);
        console.log(
          `🎯 First play: ${data.pieces.length} pieces required for this turn`
        );
      }

      // Update UI to show current plays
      this.updateTurnPlaysDisplay();

      // Check if all players have played
      if (this.phaseManager.allPlayersPlayed()) {
        console.log("✅ All players have played this turn");
        // Wait for server to send turn result
      }
    };
    onSocketEvent("play", this.handlePlay);

    this.handleRedeal = (data) => {
      console.log("🔄 WS: Redeal occurred", {
        player: data.player,
        multiplier: data.multiplier,
        newStarter: data.player,
      });

      // Update multiplier display
      this.updateMultiplierDisplay(data.multiplier);

      // Show redeal notification
      this.showRedealNotification(data.player, data.multiplier);

      // If redeal was accepted, we'll receive new hands via start_round event
      // The server will reshuffle and send new hands
    };
    onSocketEvent("redeal", this.handleRedeal);

    this.handleDeclare = (data) => {
      console.log("📡 WS: Declaration received:", {
        player: data.player,
        value: data.value,
        isBot: data.is_bot,
        currentDeclarations: { ...this.declarations },
        timestamp: new Date().toISOString(),
      });

      // Prevent duplicate updates
      if (this.declarations[data.player] === data.value) {
        console.log(
          `⚠️ Duplicate declaration ignored for ${data.player}: ${data.value}`
        );
        return;
      }

      // Update declarations
      this.declarations[data.player] = data.value;

      // Log individual declaration
      console.log(
        `✅ ${data.player}${data.is_bot ? " 🤖" : ""} declared: ${data.value}`
      );

      // Update waiting UI if visible
      if (
        this.declarationStatusContainer &&
        this.phaseManager.getCurrentPhase() === GamePhases.DECLARATION
      ) {
        this.updateDeclarationStatus();
      }

      // Check if all declared
      const declaredPlayers = this.players.filter(
        (p) => this.declarations[p.name] !== null
      );
      const allDeclared = declaredPlayers.length === this.players.length;

      console.log("📊 Declaration progress:", {
        declared: declaredPlayers.map((p) => p.name),
        remaining: this.players
          .filter((p) => this.declarations[p.name] === null)
          .map((p) => p.name),
        total: `${declaredPlayers.length}/${this.players.length}`,
        allDeclared,
      });

      if (allDeclared) {
        // Calculate total and check if valid
        const total = Object.values(this.declarations).reduce(
          (sum, val) => sum + val,
          0
        );
        console.log(
          `📊 All players declared! Total: ${total} (must not equal 8)`
        );

        if (total === 8) {
          console.error("❌ Total declarations = 8, which is not allowed!");
          // This should be handled by backend
        }

        // Show declaration summary
        console.log("📋 Final declarations:");
        this.players.forEach((p) => {
          console.log(
            `  ${p.name}${p.is_bot ? " 🤖" : ""}: ${this.declarations[p.name]}`
          );
        });

        // Transition to TURN_PLAY
        setTimeout(() => {
          console.log("➡️ Moving to TURN_PLAY phase");
          this.phaseManager.setPhase(GamePhases.TURN_PLAY);
        }, 1000); // Small delay to see final declarations
      }
    };
    onSocketEvent("declare", this.handleDeclare);

    // แก้ไข handlePlay ที่มีอยู่
    this.handlePlay = (data) => {
      console.log("WS: Player played", data);

      // Record play in phase manager
      this.phaseManager.recordPlay(data.player, data.pieces, data.valid);

      if (this.phaseManager.currentTurn.plays.length === 1) {
        this.phaseManager.setRequiredPieceCount(data.pieces.length);
      }

      // Update UI to show current plays
      this.updateCurrentPlaysDisplay();
    };
    onSocketEvent("play", this.handlePlay);

    // turn resolution
    // this.handleTurnComplete = (data) => {
    //   console.log("WS: Turn complete", data);
    //   this.phaseManager.setPhase(GamePhases.TURN_RESOLUTION, data);
    // };
    // onSocketEvent("turn_complete", this.handleTurnComplete);

    this.handleTurnResolved = (data) => {
      console.log("🏆 WS: Turn resolved", {
        winner: data.winner,
        plays: data.plays,
        pile_count: data.pile_count,
      });

      // Show turn result
      this.phaseManager.setPhase(GamePhases.TURN_RESOLUTION, {
        turnResult: {
          plays: data.plays,
          winner: data.winner,
          pileCount: data.pile_count,
        },
        hasMoreTurns: this.myHand.length > 0,
      });
    };
    onSocketEvent("turn_resolved", this.handleTurnResolved);

    this.handleStartRound = (data) => {
      console.log("🆕 WS: New round started (after redeal)", {
        round: data.round,
        starter: data.starter,
        hands: data.hands,
      });

      // Update game state
      this.currentRound = data.round;
      this.myHand = data.hands[this.playerName] || [];

      // Reset declarations
      this.players.forEach((p) => {
        this.declarations[p.name] = null;
      });

      // Start from redeal check again
      this.phaseManager.setPhase(GamePhases.ROUND_PREPARATION, data);
    };
    onSocketEvent("start_round", this.handleStartRound);

    this.handleScore = (data) => {
      console.log("WS: Round scored", data);
      this.phaseManager.setPhase(GamePhases.ROUND_SCORING, data);
    };
  }

  async makeDeclaration(value) {
    try {
      console.log(`🎲 Making declaration: ${value}`);

      const response = await fetch(
        `/api/declare?room_id=${this.roomId}&player_name=${this.playerName}&value=${value}`,
        { method: "POST" }
      );
      const result = await response.json();

      console.log("📡 Declaration response:", result);

      if (result.status === "ok") {
        this.declarations[this.playerName] = value;
        this.showWaitingForDeclarations();
      } else if (result.status === "error") {
        console.error("❌ Declaration error:", result.message);
        alert(result.message);
        // Re-enable UI
        if (this.currentPhaseUI) {
          this.currentPhaseUI.visible = true;
        }
      }
    } catch (err) {
      console.error("❌ Failed to declare:", err);
      alert(`Failed to declare: ${err.message || "Unknown error"}`);
    }
  }

  async playSelectedCards(selectedIndexes) {
    try {
      // Remove cards from hand display immediately
      const playedCards = selectedIndexes.map((i) => this.myHand[i]);

      const response = await fetch(
        `/api/play-turn?room_id=${this.roomId}&player_name=${
          this.playerName
        }&piece_indexes=${selectedIndexes.join(",")}`,
        { method: "POST" }
      );
      const result = await response.json();

      if (result.status === "waiting") {
        // Show waiting for other players
        this.showWaitingForPlayers();
      }

      // Remove played cards from hand
      selectedIndexes
        .sort((a, b) => b - a)
        .forEach((i) => {
          this.myHand.splice(i, 1);
        });
    } catch (err) {
      console.error("Failed to play turn:", err);
    }
  }

  updateDeclarationStatus() {
    if (!this.declarationStatusContainer) return;

    console.log("🔄 Updating declaration status display");

    this.declarationStatusContainer.removeChildren();

    // Sort players to show declared ones first
    const sortedPlayers = [...this.players].sort((a, b) => {
      const aDeclared = this.declarations[a.name] !== null;
      const bDeclared = this.declarations[b.name] !== null;
      if (aDeclared && !bDeclared) return -1;
      if (!aDeclared && bDeclared) return 1;
      return 0;
    });

    sortedPlayers.forEach((player) => {
      const declared = this.declarations[player.name];
      const statusText = new Text({
        text: `${player.name}${player.is_bot ? " 🤖" : ""}: ${
          declared !== null ? `Declared ${declared} ✓` : "Thinking..."
        }`,
        style: new TextStyle({
          fill: declared !== null ? "#00ff00" : "#ffaa00",
          fontSize: 16,
        }),
      });
      this.declarationStatusContainer.addChild(statusText);
    });

    // Add total if at least 2 players declared
    const declaredValues = Object.values(this.declarations).filter(
      (v) => v !== null
    );
    if (declaredValues.length >= 2) {
      const currentTotal = declaredValues.reduce((sum, val) => sum + val, 0);
      const totalText = new Text({
        text: `Current Total: ${currentTotal}`,
        style: new TextStyle({
          fill: currentTotal === 8 ? "#ff0000" : "#ffffff",
          fontSize: 14,
          fontStyle: "italic",
        }),
      });
      this.declarationStatusContainer.addChild(totalText);
    }
  }

  resetDeclarations() {
    console.log("🔄 Resetting all declarations");
    this.players.forEach((p) => {
      this.declarations[p.name] = null;
    });
  }

  updateTurnPlaysDisplay() {
    // If we have a turn status container, update it
    if (this.turnStatusContainer) {
      this.turnStatusContainer.removeChildren();

      const playsText = new Text({
        text: "Current plays:",
        style: new TextStyle({
          fill: "#ffffff",
          fontSize: 16,
          fontWeight: "bold",
        }),
      });
      this.turnStatusContainer.addChild(playsText);

      // Show each play
      this.phaseManager.currentTurn.plays.forEach((play) => {
        const playText = new Text({
          text: `${play.player}: ${play.pieces.join(", ")} ${
            play.isValid ? "✅" : "❌"
          }`,
          style: new TextStyle({
            fill: play.isValid ? "#00ff00" : "#ff0000",
            fontSize: 14,
          }),
        });
        this.turnStatusContainer.addChild(playText);
      });

      // Show waiting count
      const remaining =
        this.players.length - this.phaseManager.currentTurn.plays.length;
      if (remaining > 0) {
        const waitingText = new Text({
          text: `⏳ Waiting for ${remaining} player${
            remaining > 1 ? "s" : ""
          }...`,
          style: new TextStyle({ fill: "#ffaa00", fontSize: 14 }),
        });
        this.turnStatusContainer.addChild(waitingText);
      }
    }
  }

  updateMultiplierDisplay(multiplier) {
    if (!this.multiplierText) {
      this.multiplierText = new Text({
        text: "",
        style: new TextStyle({
          fill: "#ff6600",
          fontSize: 18,
          fontWeight: "bold",
        }),
      });
      // Add to header area
      this.headerContainer.addChild(this.multiplierText);
    }

    if (multiplier > 1) {
      this.multiplierText.text = `🔥 x${multiplier} Multiplier!`;
      this.multiplierText.visible = true;
    } else {
      this.multiplierText.visible = false;
    }
  }

  showRedealNotification(playerName, multiplier) {
    // Clear previous UI
    this.phaseUIContainer.removeChildren();

    const notificationContainer = new Container();
    notificationContainer.layout = {
      flexDirection: "column",
      alignItems: "center",
      gap: 16,
      padding: 20,
      backgroundColor: 0x333333,
    };

    const icon = new Text({
      text: "🔄",
      style: new TextStyle({ fontSize: 48 }),
    });

    const title = new Text({
      text: "Redeal Triggered!",
      style: new TextStyle({
        fill: "#ff6600",
        fontSize: 24,
        fontWeight: "bold",
      }),
    });

    const info = new Text({
      text: `${playerName} requested a redeal`,
      style: new TextStyle({ fill: "#ffffff", fontSize: 18 }),
    });

    const multiplierInfo = new Text({
      text: `Score multiplier is now x${multiplier}`,
      style: new TextStyle({
        fill: "#ffaa00",
        fontSize: 20,
        fontWeight: "bold",
      }),
    });

    const subtext = new Text({
      text: "All hands will be reshuffled...",
      style: new TextStyle({ fill: "#aaaaaa", fontSize: 14 }),
    });

    notificationContainer.addChild(icon, title, info, multiplierInfo, subtext);
    this.phaseUIContainer.addChild(notificationContainer);

    // Auto-remove after 3 seconds
    setTimeout(() => {
      if (this.phaseUIContainer.children.includes(notificationContainer)) {
        this.phaseUIContainer.removeChild(notificationContainer);
      }
    }, 3000);
  }

  teardownWebSocketListeners() {
    offSocketEvent("declare", this.handleDeclare);
    offSocketEvent("play", this.handlePlay);
    offSocketEvent("score", this.handleScore);
    offSocketEvent("redeal", this.handleRedeal);
  }

  destroy(options) {
    this.teardownWebSocketListeners();
    super.destroy(options);
  }
}
