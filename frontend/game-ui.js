import { deal } from './api.js';

/**
 * Convert raw piece name (e.g., "CANNON_RED(4)") into readable format.
 */
function formatPiece(raw) {
  const match = raw.match(/([A-Z_]+)\((\d+)\)/) || raw.match(/([A-Z_]+)/);
  if (!match) return raw;

  const [_, name] = match;
  const displayName = name
    .replace(/_/g, ' ')
    .toLowerCase()
    .replace(/\b\w/g, c => c.toUpperCase());

  const colorEmoji = name.includes('RED') ? '🔴' : name.includes('BLACK') ? '⚫️' : '';
  return `${displayName} ${colorEmoji}`;
}

// ✅ Initialize PixiJS app
const app = new PIXI.Application();
await app.init({
  width: 800,
  height: 600,
  backgroundColor: 0xf5f5f5,
});

document.getElementById('game-container').appendChild(app.canvas);

// 🧩 All unique piece names
const allPieceNames = [
  "GENERAL_RED",
  "GENERAL_BLACK",
  "ADVISOR_RED",
  "ADVISOR_BLACK",
  "ELEPHANT_RED",
  "ELEPHANT_BLACK",
  "CHARIOT_RED",
  "CHARIOT_BLACK",
  "HORSE_RED",
  "HORSE_BLACK",
  "CANNON_RED",
  "CANNON_BLACK",
  "SOLDIER_RED",
  "SOLDIER_BLACK"
];

document.getElementById('deal-button').addEventListener('click', async () => {
  console.log("🟡 Deal button clicked");

  try {
    const gameData = await deal();
    const player1Hand = gameData.hands.P1;

    app.stage.removeChildren();

    const columnCount = 2;
    const rowHeight = 32;
    const colWidth = 300;
    const startX = 120;
    const startY = 60;

    player1Hand.forEach((piece, i) => {
      const col = i % columnCount;
      const row = Math.floor(i / columnCount);

      const text = new PIXI.Text(formatPiece(piece), {
        fontFamily: 'Arial',
        fontSize: 20,
        fill: 0x000000,
      });

      text.x = startX + col * colWidth;
      text.y = startY + row * rowHeight;

      app.stage.addChild(text);
    });

  } catch (err) {
    console.error("❌ Deal failed:", err);
  }
});

