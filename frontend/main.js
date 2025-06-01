// main.js

import { Application } from "pixi.js";
import "@pixi/layout";
import { SceneManager } from "./SceneManager.js";
import { StartScene } from "./scenes/StartScene.js";
import { LobbyScene } from "./scenes/LobbyScene.js";
import { RoomScene } from "./scenes/RoomScene.js"; // ✅ ต้อง import ด้วย
import { initDevtools } from "@pixi/devtools";

(async () => {
  const app = new Application();

  initDevtools({ app });

  await app.init({ width: 540, height: 960, background: "#1e1e2e" });
  document.body.appendChild(app.canvas);

  app.stage.layout = {
    width: app.screen.width,
    height: app.screen.height,
    justifyContent: "center",
    alignItems: "center",
  };

  const sceneManager = new SceneManager(app); // ✅ สร้าง scene manager

  const startScene = new StartScene((playerName) => {
    localStorage.setItem("playerName", playerName);

    const lobbyScene = new LobbyScene(playerName, (roomId) => {
      const roomScene = new RoomScene(roomId, playerName, () => {
        // 👉 ยังไม่สร้าง GameScene ก็ใส่ log ไว้ก่อน
        console.log("🎯 Game started! Go to GameScene next.");
      });

      sceneManager.changeScene(roomScene); // ✅ เปลี่ยนไป RoomScene
    });

    sceneManager.changeScene(lobbyScene); // เริ่มจาก Lobby
  });

  sceneManager.changeScene(startScene);
})();
