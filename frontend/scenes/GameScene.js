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
    console.log("🎮 Entered GameScene");

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
    // Clear UI ของ phase ก่อนหน้า
    this.phaseUIContainer.removeChildren();

    switch (phase) {
      case GamePhases.ROUND_PREPARATION:
        // Check for redeal after preparation
        this.checkForRedeal();
        break;

      case GamePhases.DECLARATION:
        this.showDeclarationUI();
        break;

      case GamePhases.TURN_PLAY:
        this.showTurnPlayUI(data);
        break;

      case GamePhases.TURN_RESOLUTION:
        this.showTurnResultUI(data);
        break;

      case GamePhases.ROUND_SCORING:
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
    const ui = new DeclarationUI(this.playerName, this.declarations, (value) =>
      this.makeDeclaration(value)
    );
    this.phaseUIContainer.addChild(ui.view);
  }

  showTurnPlayUI(data) {
    const isFirstPlayer = this.phaseManager.isFirstPlayerOfTurn(
      this.playerName
    );
    const requiredCount = this.phaseManager.currentTurn.requiredPieceCount;

    const ui = new TurnPlayUI(
      this.myHand,
      isFirstPlayer,
      requiredCount,
      (selectedIndexes) => this.playSelectedCards(selectedIndexes)
    );
    this.phaseUIContainer.addChild(ui.view);
  }

  setupWebSocketListeners() {
    // Listen for game events
    this.handleDeclare = (data) => {
      console.log("WS: Player declared", data);
      // TODO: Update UI
    };
    onSocketEvent("declare", this.handleDeclare);

    this.handlePlay = (data) => {
      console.log("WS: Player played", data);
      // TODO: Update UI
    };
    onSocketEvent("play", this.handlePlay);

    // this.handleScore = (data) => {
    //   console.log("WS: Round scored", data);
    //   // TODO: Update scores and check game over
    // };
    // onSocketEvent("score", this.handleScore);

    this.handleRedeal = (data) => {
      console.log("WS: Redeal requested", data);
      // TODO: Handle redeal
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
    this.handleTurnComplete = (data) => {
      console.log("WS: Turn complete", data);
      this.phaseManager.setPhase(GamePhases.TURN_RESOLUTION, data);
    };
    onSocketEvent("turn_complete", this.handleTurnComplete);

    this.handleScore = (data) => {
      console.log("WS: Round scored", data);
      this.phaseManager.setPhase(GamePhases.ROUND_SCORING, data);
    };
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
        // Disable declaration UI
        this.phaseUIContainer.children[0].visible = false;
      }
    } catch (err) {
      console.error("Failed to declare:", err);
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
