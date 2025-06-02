// frontend/main.js

import { Application } from "pixi.js";
import "@pixi/layout";
import "@pixi/layout/devtools";
import { SceneManager } from "./SceneManager.js";
import { StartScene } from "./scenes/StartScene.js";
import { LobbyScene } from "./scenes/LobbyScene.js";
import { RoomScene } from "./scenes/RoomScene.js"; // ✅ ต้อง import ด้วย
import { initDevtools } from "@pixi/devtools";

///
import { createRoom } from "./api.js"; // ✅ เพิ่มตรงนี้ให้ถูก

(async () => {
  const app = new Application();

  initDevtools({ app });

  await app.init({
    width: 540,
    height: 960,
    background: "#1e1e2e",
  });

  document.body.appendChild(app.canvas);

  app.stage.layout = {
    width: app.screen.width,
    height: app.screen.height,
  };

  const sceneManager = new SceneManager(app);
  //

  ////

  const startScene = new StartScene((playerName) => {
    localStorage.setItem("playerName", playerName);

    const lobbyScene = new LobbyScene(playerName, (roomId) => {
      const roomScene = new RoomScene(roomId, playerName, () => {
        console.log("🎯 Game started! Go to GameScene next.");
      }, sceneManager);

      sceneManager.changeScene(roomScene); // ✅ เปลี่ยนไป RoomScene
    });

    sceneManager.changeScene(lobbyScene); // เริ่มจาก Lobby
  });

  sceneManager.changeScene(startScene);

  ///
  // 🔧 ข้าม StartScene แล้วเข้าสู่ LobbyScene ตรง ๆ

  // const playerName = "TestPlayer";

  // const lobbyScene = new LobbyScene(playerName, (roomId) => {
  //   const roomScene = new RoomScene(roomId, playerName, () => {
  //     console.log("🎯 Game started! Go to GameScene next.");
  //   });

  //   sceneManager.changeScene(roomScene);
  // });

  // sceneManager.changeScene(lobbyScene);

  ///

  // 🧪 ตั้งค่าทดสอบ
  // const playerName = "TestPlayer";

  // const res = await createRoom(playerName);
  // const roomId = res.room_id;
  // // onEnterRoom(result.room_id);

  // const roomScene = new RoomScene(roomId, playerName, () => {
  //   console.log("🎯 Game started!");
  // });
  // sceneManager.changeScene(roomScene);
})();
