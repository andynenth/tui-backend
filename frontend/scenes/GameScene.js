// frontend/scenes/GameScene.js

import { Container, Text, TextStyle } from "pixi.js";
import { GameButton } from "../components/GameButton.js";
import { GameEvents } from "../SceneFSM.js";
import {
    on as onSocketEvent,
    off as offSocketEvent,
    emit as emitSocketEvent
} from "../socketManager.js";

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
        this.myPlayerData = this.players.find(p => p.name === this.playerName);
        this.myHand = gameData.hands?.[this.playerName] || [];

        this.layout = {
            width: "100%",
            height: "100%",
            flexDirection: "column",
            alignItems: "center",
            padding: 16,
            gap: 16,
        };

        this.setupUI();
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
        });

        header.addChild(roundText, scoreText);

        // Player area
        const playerArea = new Container();
        playerArea.layout = {
            width: "100%",
            flexDirection: "column",
            gap: 8,
        };

        // Show all players
        this.players.forEach(player => {
            const playerRow = new Container();
            playerRow.layout = {
                flexDirection: "row",
                gap: 8,
            };

            const nameText = new Text({
                text: `${player.name}${player.is_bot ? ' 🤖' : ''}${player.name === this.playerName ? ' (You)' : ''}`,
                style: new TextStyle({ fill: "#ffffff", fontSize: 16 }),
            });

            const scoreText = new Text({
                text: `${player.score} pts`,
                style: new TextStyle({ fill: "#aaaaaa", fontSize: 16 }),
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

        this.handleScore = (data) => {
            console.log("WS: Round scored", data);
            // TODO: Update scores and check game over
        };
        onSocketEvent("score", this.handleScore);

        this.handleRedeal = (data) => {
            console.log("WS: Redeal requested", data);
            // TODO: Handle redeal
        };
        onSocketEvent("redeal", this.handleRedeal);
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