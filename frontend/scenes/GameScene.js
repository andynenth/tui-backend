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
    console.log("🎮 Entered GameScene with data:", {
      roomId,
      playerName,
      gameData,
      round: gameData.round,
      starter: gameData.starter,
      players: gameData.players,
      myHand: gameData.hands?.[playerName],
    });

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
    console.log(
      `📊 Phase change: ${this.phaseManager.getCurrentPhase()} → ${phase}`,
      data
    );

    // Clear ALL previous phase UI
    this.phaseUIContainer.removeChildren();
    this.currentPhaseUI = null;

    // Hide waiting message if any
    if (this.waitingText) {
      this.waitingText.visible = false;
    }

    switch (phase) {
      case GamePhases.ROUND_PREPARATION:
        console.log("🔄 Round preparation phase - checking for redeal");
        this.checkForRedeal();
        break;

      case GamePhases.DECLARATION:
        console.log("📢 Declaration phase started");
        this.showDeclarationUI();
        break;

      case GamePhases.TURN_PLAY:
        console.log("🎯 Turn play phase started");
        this.showTurnPlayUI(data);
        break;

      case GamePhases.TURN_RESOLUTION:
        console.log("🏆 Turn resolution phase");
        this.showTurnResultUI(data);
        break;

      case GamePhases.ROUND_SCORING:
        console.log("📊 Round scoring phase");
        this.showRoundScoreUI(data);
        break;
    }
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
    // Check if already declared
    if (this.declarations[this.playerName] !== null) {
      console.log("✅ Already declared:", this.declarations[this.playerName]);
      this.showWaitingForDeclarations();
      return;
    }

    console.log("🎯 Showing declaration UI for", this.playerName);

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
    const isFirstPlayer = this.phaseManager.isFirstPlayerOfTurn(
      this.playerName
    );
    const requiredCount = this.phaseManager.currentTurn.requiredPieceCount;

    // Main container
    const container = new Container();
    container.layout = {
      flexDirection: "column",
      alignItems: "center",
      gap: 16,
    };

    // Turn status display
    this.turnStatusContainer = new Container();
    this.turnStatusContainer.layout = {
      flexDirection: "column",
      gap: 8,
      padding: 10,
      backgroundColor: 0x2a2a2a,
    };

    container.addChild(this.turnStatusContainer);

    // Update initial status
    this.updateTurnPlaysDisplay();

    // Play UI
    const ui = new TurnPlayUI(
      this.myHand,
      isFirstPlayer,
      requiredCount,
      (selectedIndexes) => this.playSelectedCards(selectedIndexes)
    );

    container.addChild(ui.view);
    this.phaseUIContainer.addChild(container);
  }

  setupWebSocketListeners() {
    // Listen for game events
    this.handleDeclare = (data) => {
      console.log("📡 WS: Declaration received:", {
        player: data.player,
        value: data.value,
        isBot: data.is_bot,
        currentDeclarations: this.declarations,
      });

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
        console.log("✅ All players declared! Moving to TURN_PLAY");

        // Calculate total
        const total = Object.values(this.declarations).reduce(
          (sum, val) => sum + val,
          0
        );
        console.log(`📊 Total declared: ${total} (must not equal 8)`);

        this.phaseManager.setPhase(GamePhases.TURN_PLAY);
      }
    };
    onSocketEvent("declare", this.handleDeclare);

    this.handlePlay = (data) => {
      console.log("📡 WS: Play received:", {
        player: data.player,
        pieces: data.pieces,
        valid: data.valid,
        play_type: data.play_type,
        currentTurn: this.phaseManager.currentTurn,
      });

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
      console.log("WS: Player declared", data);
      this.declarations[data.player] = data.value;

      // Update UI ถ้าอยู่ใน declaration phase
      if (this.phaseManager.getCurrentPhase() === GamePhases.DECLARATION) {
        this.showDeclarationUI(); // Refresh UI
      }

      // Check ว่าทุกคนประกาศครบหรือยัง
      const allDeclared = Object.values(this.declarations).every(
        (v) => v !== null
      );
      if (allDeclared) {
        this.phaseManager.setPhase(GamePhases.TURN_PLAY);
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

    this.declarationStatusContainer.removeChildren();

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
      this.declarationStatusContainer.addChild(statusText);
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
