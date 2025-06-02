// frontend/main.js
import { Application } from "pixi.js";
import "@pixi/layout";
import "@pixi/layout/devtools";
import { SceneManager } from "./SceneManager.js";
import { SceneFSM, GameStates, GameEvents } from "./SceneFSM.js"; // นำเข้า SceneFSM และ States/Events
import { initDevtools } from "@pixi/devtools";

(async () => {
    const app = new Application();

    initDevtools({ app }); // สำหรับ PixiJS DevTools

    await app.init({
        width: 540,
        height: 960,
        background: "#1e1e2e",
    });

    document.body.appendChild(app.canvas);

    // กำหนด layout ให้ stage ของ PixiJS
    app.stage.layout = {
        width: app.screen.width,
        height: app.screen.height,
    };

    const sceneManager = new SceneManager(app); // สร้าง SceneManager

    // สร้าง Finite State Machine (FSM) ที่จะควบคุม Scene Flow
    const gameFSM = new SceneFSM(app, sceneManager);

    // ตรวจสอบว่ามีชื่อผู้เล่นที่บันทึกไว้หรือไม่
    const storedPlayerName = localStorage.getItem("playerName");

    if (storedPlayerName) {
        // ถ้ามีชื่อผู้เล่นอยู่แล้ว ให้ตั้งค่าใน FSM context และไปที่ LobbyScene โดยตรง
        gameFSM.context.playerName = storedPlayerName;
        gameFSM.changeState(GameStates.LOBBY);
        console.log(`Main: Found stored player name: ${storedPlayerName}. Starting at Lobby.`);
    } else {
        // ถ้าไม่มีชื่อ ให้ไปที่ StartScreen เพื่อให้ผู้เล่นป้อนชื่อ
        gameFSM.changeState(GameStates.START_SCREEN);
        console.log("Main: No stored player name. Starting at Start Screen.");
    }

    // ไม่ต้องมี Logic การสร้างและเปลี่ยน Scene ตรงๆ ใน main.js อีกต่อไป
    // ทุกอย่างจะถูกจัดการโดย gameFSM
})();