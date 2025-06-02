// frontend/SceneFSM.js
import { SceneManager } from './SceneManager.js';
import { StartScene } from './scenes/StartScene.js';
import { LobbyScene } from './scenes/LobbyScene.js';
import { RoomScene } from './scenes/RoomScene.js';
// import { GameScene } from './scenes/GameScene.js'; // จะใช้เมื่อมี GameScene แล้ว

// กำหนดสถานะที่เป็นไปได้ของเกม
const GameStates = {
    INIT: 'INIT', // สถานะเริ่มต้นของ FSM ก่อนที่จะแสดง Scene แรก
    START_SCREEN: 'START_SCREEN',
    LOBBY: 'LOBBY',
    ROOM: 'ROOM',
    GAME: 'GAME',
    // สามารถเพิ่มสถานะอื่นๆ ได้ในอนาคต เช่น GAME_OVER, PAUSE
};

// กำหนดเหตุการณ์ที่สามารถทำให้สถานะเปลี่ยนได้
const GameEvents = {
    PLAYER_NAME_ENTERED: 'PLAYER_NAME_ENTERED',
    ROOM_CREATED: 'ROOM_CREATED',
    ROOM_JOINED: 'ROOM_JOINED',
    EXIT_ROOM: 'EXIT_ROOM',
    GAME_STARTED: 'GAME_STARTED',
    // สามารถเพิ่มเหตุการณ์อื่นๆ ได้ตามการโต้ตอบในเกม
};

export class SceneFSM {
    constructor(app, sceneManager) {
        this.app = app;
        this.sceneManager = sceneManager;
        this.currentState = GameStates.INIT; // สถานะเริ่มต้นของ FSM
        this.context = {}; // Object สำหรับเก็บข้อมูลที่จำเป็นต้องใช้ร่วมกันระหว่าง States (เช่น playerName, roomId)

        // กำหนดกฎการเปลี่ยนผ่าน (transitions) ระหว่าง States
        // แต่ละ State จะมี Object ของ Events ที่สามารถ Trigger การเปลี่ยน State ได้
        this.transitions = {
            [GameStates.INIT]: {
                // หากมี playerName ใน localStorage ให้ไป Lobby เลย
                [GameEvents.PLAYER_NAME_ENTERED]: (data) => {
                    this.context.playerName = data.playerName;
                    return GameStates.LOBBY;
                },
                // เริ่มต้นที่ StartScreen ถ้าไม่มีชื่อผู้เล่น
                start: () => GameStates.START_SCREEN, // เหตุการณ์เริ่มต้น FSM
            },
            [GameStates.START_SCREEN]: {
                [GameEvents.PLAYER_NAME_ENTERED]: (data) => {
                    this.context.playerName = data.playerName;
                    localStorage.setItem("playerName", data.playerName); // บันทึกชื่อผู้เล่น
                    return GameStates.LOBBY;
                },
            },
            [GameStates.LOBBY]: {
                [GameEvents.ROOM_CREATED]: (data) => {
                    this.context.roomId = data.roomId;
                    return GameStates.ROOM;
                },
                [GameEvents.ROOM_JOINED]: (data) => {
                    this.context.roomId = data.roomId;
                    return GameStates.ROOM;
                },
            },
            [GameStates.ROOM]: {
                [GameEvents.GAME_STARTED]: () => GameStates.GAME,
                [GameEvents.EXIT_ROOM]: () => {
                    delete this.context.roomId; // ลบ roomId เมื่อออกจากห้อง กลับไป Lobby
                    return GameStates.LOBBY;
                },
            },
            [GameStates.GAME]: {
                // TODO: กำหนด Transitions สำหรับสถานะ GAME
                // เช่น GAME_ENDED -> LOBBY หรือ GAME_OVER
                [GameEvents.EXIT_ROOM]: () => { // เช่น ออกจากเกมกลางคัน
                    delete this.context.roomId;
                    return GameStates.LOBBY;
                }
            },
        };
    }

    // ฟังก์ชันนี้จะถูกส่งให้ Scene ย่อยเพื่อใช้เรียก Event กลับมายัง FSM
    // ทุก Scene จะมีหน้าที่แค่ "ยิง Event" ไม่ต้องรู้ว่าจะไป Scene ไหนต่อ
    triggerEvent = (event, data = {}) => {
        const nextStateFunction = this.transitions[this.currentState]?.[event];
        if (nextStateFunction) {
            const nextState = nextStateFunction(data);
            if (nextState && nextState !== this.currentState) { // ตรวจสอบว่ามี State ถัดไปและมีการเปลี่ยนแปลง
                console.log(`FSM: Transitioning from ${this.currentState} to ${nextState} via event ${event}`);
                this.changeState(nextState);
            } else if (nextState === this.currentState) {
                console.log(`FSM: Event ${event} in state ${this.currentState} did not cause state change.`);
            } else {
                console.warn(`FSM: No valid next state for event ${event} in state ${this.currentState}`);
            }
        } else {
            console.warn(`FSM: Event ${event} is not defined for state ${this.currentState}`);
        }
    };

    // เปลี่ยนสถานะและแสดง Scene ที่เกี่ยวข้อง
    changeState(newState) {
        this.currentState = newState;
        let sceneInstance;

        switch (newState) {
            case GameStates.START_SCREEN:
                // StartScene รับ callback triggerEvent
                sceneInstance = new StartScene(this.triggerEvent);
                break;
            case GameStates.LOBBY:
                // LobbyScene รับ playerName และ triggerEvent
                if (!this.context.playerName) {
                    console.error("FSM: Missing playerName for LobbyState. Returning to StartScreen.");
                    this.changeState(GameStates.START_SCREEN); // กลับไป StartScreen หากข้อมูลไม่ครบ
                    return;
                }
                sceneInstance = new LobbyScene(this.context.playerName, this.triggerEvent);
                break;
            case GameStates.ROOM:
                // RoomScene รับ roomId, playerName และ triggerEvent
                if (!this.context.roomId || !this.context.playerName) {
                    console.error("FSM: Missing roomId or playerName for RoomState. Returning to Lobby.");
                    this.changeState(GameStates.LOBBY); // กลับไป Lobby หากข้อมูลไม่ครบ
                    return;
                }
                sceneInstance = new RoomScene(this.context.roomId, this.context.playerName, this.triggerEvent);
                break;
            case GameStates.GAME:
                // TODO: สร้าง GameScene instance ที่นี่
                // sceneInstance = new GameScene(this.context.roomId, this.context.playerName, this.triggerEvent);
                console.log("FSM: TODO: Load GameScene here!");
                // หากยังไม่มี GameScene ให้กลับไป Room เพื่อไม่ให้ค้าง
                // this.changeState(GameStates.ROOM);
                // return;
                break;
            default:
                console.error("FSM: Unknown or unhandled game state:", newState);
                return;
        }
        this.sceneManager.changeScene(sceneInstance);
    }
}

// ทำให้ GameStates และ GameEvents สามารถเข้าถึงได้จากภายนอก
export { GameStates, GameEvents };