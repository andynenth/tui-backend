// frontend/game/GameUIComponents.js

import { Container, Text, TextStyle } from "pixi.js";
import { GameButton } from "../components/GameButton.js";

export class RedealUI {
  constructor(onRedeal, onSkip) {
    this.view = new Container();
    this.view.layout = {
      flexDirection: "column",
      alignItems: "center",
      gap: 16,
      padding: 20,
      backgroundColor: 0x333333,
    };

    const title = new Text({
      text: "🔄 Redeal Check",
      style: new TextStyle({ fill: "#ffffff", fontSize: 20 }),
    });

    const info = new Text({
      text: "You have no pieces > 9 points",
      style: new TextStyle({ fill: "#ffaa00", fontSize: 16 }),
    });

    const redealBtn = new GameButton({
      label: "Request Redeal",
      bgColor: 0xff6600,
      onClick: onRedeal,
    });

    const skipBtn = new GameButton({
      label: "Continue",
      onClick: onSkip,
    });

    this.view.addChild(title, info, redealBtn.view, skipBtn.view);
  }
}

export class DeclarationUI {
  constructor(playerName, currentDeclarations, onDeclare) {
    this.view = new Container();
    this.view.layout = {
      flexDirection: "column",
      alignItems: "center",
      gap: 12,
    };

    const title = new Text({
      text: "📢 Declaration Phase",
      style: new TextStyle({ fill: "#ffffff", fontSize: 20 }),
    });

    const instruction = new Text({
      text: "Declare how many piles you aim to capture:",
      style: new TextStyle({ fill: "#aaaaaa", fontSize: 16 }),
    });

    // Show current declarations
    const declareList = new Container();
    declareList.layout = { flexDirection: "column", gap: 4 };

    Object.entries(currentDeclarations).forEach(([player, value]) => {
      const text = new Text({
        text: `${player}: ${value !== null ? value : "..."}`,
        style: new TextStyle({
          fill: player === playerName ? "#00ff00" : "#ffffff",
          fontSize: 14,
        }),
      });
      declareList.addChild(text);
    });

    // Declaration buttons (0-8)
    const buttonGrid = new Container();
    buttonGrid.layout = {
      flexDirection: "row",
      flexWrap: "wrap",
      gap: 8,
      width: 300,
      justifyContent: "center",
    };

    this.buttons = [];
    for (let i = 0; i <= 8; i++) {
      const btn = new GameButton({
        label: String(i),
        width: 60,
        height: 40,
        onClick: () => {
          // Disable all buttons after click
          this.buttons.forEach((b) => b.setEnabled(false));
          onDeclare(i);
        },
      });
      this.buttons.push(btn);
      buttonGrid.addChild(btn.view);
    }

    this.view.addChild(title, instruction, declareList, buttonGrid);
  }
}

export class TurnPlayUI {
  constructor(playerHand, isFirstPlayer, requiredCount, onPlay) {
    this.view = new Container();
    this.view.layout = {
      flexDirection: "column",
      alignItems: "center",
      gap: 16,
    };

    this.selectedPieces = new Set();
    this.cardButtons = [];
    this.playerHand = playerHand;
    this.isFirstPlayer = isFirstPlayer;
    this.requiredCount = requiredCount;

    const title = new Text({
      text: isFirstPlayer
        ? "🎯 Your turn - Play 1-6 pieces"
        : `🎯 Play exactly ${requiredCount} pieces`,
      style: new TextStyle({ fill: "#ffffff", fontSize: 18 }),
    });

    // Show hand info
    const handInfo = new Text({
      text: `Your hand (${playerHand.length} pieces):`,
      style: new TextStyle({ fill: "#aaaaaa", fontSize: 14 }),
    });

    // Hand display
    const handContainer = new Container();
    handContainer.layout = {
      flexDirection: "row",
      flexWrap: "wrap",
      gap: 8,
      maxWidth: 500,
    };

    playerHand.forEach((piece, index) => {
      const btn = new GameButton({
        label: piece,
        width: 90,
        height: 70,
        bgColor: 0x4444ff,
        onClick: () => this.togglePiece(index),
      });

      // Store button reference
      this.cardButtons.push({
        button: btn,
        index: index,
        piece: piece,
        selected: false,
      });

      handContainer.addChild(btn.view);
    });

    // Selection info
    this.selectionInfo = new Text({
      text: "Select pieces to play",
      style: new TextStyle({ fill: "#ffaa00", fontSize: 14 }),
    });

    // Play button
    this.playBtn = new GameButton({
      label: "Play 0 pieces",
      bgColor: 0x00aa00,
      onClick: () => {
        const selected = Array.from(this.selectedPieces);
        if (this.validateSelection()) {
          onPlay(selected);
        } else {
          alert(this.getValidationError());
        }
      },
    });

    this.playBtn.setEnabled(false);
    this.view.addChild(
      title,
      handInfo,
      handContainer,
      this.selectionInfo,
      this.playBtn.view
    );
  }

  togglePiece(index) {
    // Find the card button
    const cardData = this.cardButtons.find((c) => c.index === index);
    if (!cardData) return;

    if (this.selectedPieces.has(index)) {
      // Deselect
      this.selectedPieces.delete(index);
      cardData.selected = false;
      cardData.button.bgColor = 0x4444ff;
      cardData.button._createView();
    } else {
      // Select
      this.selectedPieces.add(index);
      cardData.selected = true;
      cardData.button.bgColor = 0x00ff00;
      cardData.button._createView();
    }

    this.updateUI();
  }

  updateUI() {
    const count = this.selectedPieces.size;

    // Update play button text
    if (count === 0) {
      this.playBtn.setText("Play 0 pieces");
      this.playBtn.setEnabled(false);
    } else {
      this.playBtn.setText(`Play ${count} piece${count !== 1 ? "s" : ""}`);
      this.playBtn.setEnabled(true);
    }

    // Update selection info
    if (count === 0) {
      this.selectionInfo.text = "Select pieces to play";
      this.selectionInfo.style.fill = "#ffaa00";
    } else {
      const selectedPieces = Array.from(this.selectedPieces)
        .map((i) => this.playerHand[i])
        .join(", ");
      this.selectionInfo.text = `Selected: ${selectedPieces}`;

      if (this.validateSelection()) {
        this.selectionInfo.style.fill = "#00ff00";
      } else {
        this.selectionInfo.style.fill = "#ff0000";
      }
    }
  }

  validateSelection() {
    const count = this.selectedPieces.size;

    if (count === 0) return false;

    if (this.isFirstPlayer) {
      return count >= 1 && count <= 6;
    } else {
      return count === this.requiredCount;
    }
  }

  getValidationError() {
    const count = this.selectedPieces.size;

    if (count === 0) {
      return "Please select at least one piece";
    }

    if (this.isFirstPlayer) {
      if (count > 6) {
        return "Cannot play more than 6 pieces";
      }
    } else {
      if (count !== this.requiredCount) {
        return `Must play exactly ${this.requiredCount} pieces`;
      }
    }

    return "";
  }
}

export class TurnResultUI {
  constructor(turnResult, onContinue) {
    this.view = new Container();
    this.view.layout = {
      flexDirection: "column",
      alignItems: "center",
      gap: 12,
      padding: 20,
    };

    const title = new Text({
      text: "🏆 Turn Result",
      style: new TextStyle({ fill: "#ffffff", fontSize: 20 }),
    });

    // Show all plays
    const playsContainer = new Container();
    playsContainer.layout = { flexDirection: "column", gap: 8 };

    turnResult.plays.forEach((play) => {
      const text = new Text({
        text: `${play.player}: ${play.pieces.join(", ")} ${
          play.isValid ? "✅" : "❌"
        }`,
        style: new TextStyle({
          fill: play.player === turnResult.winner ? "#00ff00" : "#ffffff",
          fontSize: 14,
        }),
      });
      playsContainer.addChild(text);
    });

    const winnerText = new Text({
      text: turnResult.winner
        ? `${turnResult.winner} wins ${turnResult.pileCount} pieces!`
        : "No winner this turn",
      style: new TextStyle({ fill: "#ffff00", fontSize: 18 }),
    });

    const continueBtn = new GameButton({
      label: "Continue",
      onClick: onContinue,
    });

    this.view.addChild(title, playsContainer, winnerText, continueBtn.view);
  }
}

export class RoundScoreUI {
  constructor(scoreData, onContinue) {
    this.view = new Container();
    this.view.layout = {
      flexDirection: "column",
      alignItems: "center",
      gap: 12,
    };

    const title = new Text({
      text: "📊 Round Scores",
      style: new TextStyle({ fill: "#ffffff", fontSize: 24 }),
    });

    const scoresContainer = new Container();
    scoresContainer.layout = { flexDirection: "column", gap: 8 };

    scoreData.scores.forEach((playerScore, player) => {
      const text = new Text({
        text: `${player}: Declared ${playerScore.declared}, Got ${
          playerScore.actual
        } → ${playerScore.delta >= 0 ? "+" : ""}${playerScore.delta} pts`,
        style: new TextStyle({
          fill: playerScore.delta >= 0 ? "#00ff00" : "#ff0000",
          fontSize: 16,
        }),
      });
      scoresContainer.addChild(text);
    });

    const continueBtn = new GameButton({
      label: "Next Round",
      onClick: onContinue,
    });

    this.view.addChild(title, scoresContainer, continueBtn.view);
  }
}
