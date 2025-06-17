// frontend/scenes/GameScene.js
import { Container, Text, TextStyle } from "pixi.js";
import { SocketManager } from "../network/SocketManager.js";
import { GameButton } from "../components/GameButton.js";

export class GameScene extends Container {
  constructor(roomId, playerName, gameData, triggerFSMEvent) {
    super();

    this.roomId = roomId;
    this.playerName = playerName;
    this.gameData = gameData;
    this.triggerFSMEvent = triggerFSMEvent;

    console.log("🎮 Simple GameScene created");
    console.log("📊 Game data:", gameData);

    // Create simple UI
    this.createUI();

    // Connect and listen
    this.connectToGame();
  }

  createUI() {
    // Title
    this.titleText = new Text({
      text: "Game Started - Waiting for events...",
      style: new TextStyle({ fill: "#ffffff", fontSize: 24 }),
    });
    this.titleText.x = 50;
    this.titleText.y = 50;
    this.addChild(this.titleText);

    // Status text
    this.statusText = new Text({
      text: "Connecting...",
      style: new TextStyle({ fill: "#ffffff", fontSize: 18 }),
    });
    this.statusText.x = 50;
    this.statusText.y = 100;
    this.addChild(this.statusText);

    // Hand display
    this.handText = new Text({
      text: "Your hand: (waiting...)",
      style: new TextStyle({ fill: "#ffffff", fontSize: 16 }),
    });
    this.handText.x = 50;
    this.handText.y = 150;
    this.addChild(this.handText);

    // Message area
    this.messageText = new Text({
      text: "",
      style: new TextStyle({ fill: "#ffff00", fontSize: 16 }),
    });
    this.messageText.x = 50;
    this.messageText.y = 200;
    this.addChild(this.messageText);

    // Redeal buttons (hidden initially)
    this.createRedealButtons();
  }

  createRedealButtons() {
    this.redealContainer = new Container();
    this.redealContainer.x = 50;
    this.redealContainer.y = 250;
    this.redealContainer.visible = false;

    const promptText = new Text({
      text: "You have a weak hand. Redeal?",
      style: new TextStyle({ fill: "#ff9999", fontSize: 18 }),
    });
    this.redealContainer.addChild(promptText);

    this.yesButton = new GameButton({
      label: "Yes",
      onClick: () => this.handleRedealDecision("accept"),
    });
    this.yesButton.view.x = 0;
    this.yesButton.view.y = 40;

    this.noButton = new GameButton({
      label: "No",
      onClick: () => this.handleRedealDecision("decline"),
    });
    this.noButton.view.x = 100;
    this.noButton.view.y = 40;

    this.redealContainer.addChild(this.yesButton.view);
    this.redealContainer.addChild(this.noButton.view);
    this.addChild(this.redealContainer);
  }

  async connectToGame() {
    try {
      // Create socket
      this.socket = new SocketManager();

      // Set up listeners BEFORE connecting
      this.setupEventListeners();

      // Connect
      await this.socket.connect(this.roomId);
      console.log("✅ Connected to game socket");

      this.statusText.text = "Connected! Waiting for game events...";

      // Tell backend we're ready
      this.socket.send("player_ready", {
        room_id: this.roomId,
        player: this.playerName,
      });
    } catch (error) {
      console.error("❌ Failed to connect:", error);
      this.statusText.text = "Failed to connect!";
    }
  }

  setupEventListeners() {
    // Preparation events
    this.socket.on("preparation_started", (data) => {
      console.log("📋 Preparation started:", data);
      this.titleText.text = "Preparation Phase";
      this.statusText.text = `${data.weak_hand_count} players have weak hands`;
    });

    this.socket.on("initial_hand_dealt", (data) => {
      console.log("🎴 Hand received:", data);
      if (data.player === this.playerName) {
        this.handText.text = `Your hand: ${data.hand
          .map((p) => p.name)
          .join(", ")}`;
        if (data.is_weak) {
          this.messageText.text = "⚠️ You have a weak hand!";
        }
      }
    });

    this.socket.on("redeal_phase_started", (data) => {
      console.log("🔄 Redeal phase started:", data);
      this.statusText.text = "Checking for redeals...";
    });

    this.socket.on("redeal_prompt", (data) => {
      console.log("❓ Redeal prompt:", data);
      if (data.target_player === this.playerName) {
        this.redealContainer.visible = true;
        this.messageText.text = "Your turn to decide!";
      } else {
        this.messageText.text = `Waiting for ${data.target_player} to decide...`;
      }
    });

    this.socket.on("redeal_decision_made", (data) => {
      console.log("✅ Decision made:", data);
      this.messageText.text = `${data.player} ${data.decision}ed redeal`;
      if (data.player === this.playerName) {
        this.redealContainer.visible = false;
      }
    });

    this.socket.on("redeal_executed", (data) => {
      console.log("🔄 Redeal executed:", data);
      this.messageText.text = `Redeal! New multiplier: ${data.new_multiplier}x`;
      this.handText.text = "Your hand: (getting new cards...)";
    });

    this.socket.on("preparation_complete", (data) => {
      console.log("✅ Preparation complete:", data);
      this.titleText.text = "Preparation Complete!";
      this.statusText.text = `${data.starter} will start the game`;
      this.messageText.text = `Next phase: ${data.next_phase}`;
    });

    // General events
    this.socket.on("game_message", (data) => {
      console.log("💬 Game message:", data);
      this.messageText.text = data.message;
    });

    this.socket.on("error", (data) => {
      console.error("❌ Error:", data);
      this.messageText.text = `Error: ${data.message}`;
    });
  }

  handleRedealDecision(decision) {
    console.log(`📤 Sending redeal decision: ${decision}`);

    this.socket.send("player_action", {
      room_id: this.roomId,
      action: "redeal_decision",
      player: this.playerName,
      data: { decision: decision },
    });

    // Hide buttons
    this.redealContainer.visible = false;
    this.messageText.text = "Decision sent...";
  }

  destroy() {
    if (this.socket) {
      this.socket.disconnect();
    }
    super.destroy();
  }
}
