// frontend/scenes/StartScene.js
import { Container, Text, TextStyle } from "pixi.js";
import { GameTextbox } from "../components/GameTextbox.js";
import { GameButton } from "../components/GameButton.js";
import { GameEvents } from '../SceneFSM.js'; // นำเข้า GameEvents

export class StartScene extends Container {
    // constructor รับ callback สำหรับการ trigger FSM event
    constructor(triggerFSMEvent) {
        super();
        this.triggerFSMEvent = triggerFSMEvent; // เก็บ reference

        console.log("🔵 Entered StartScene");

        this.layout = {
            width: "100%",
            height: "100%",
            justifyContent: "center",
            alignItems: "center",
        };

        const nameInputGroup = new Container();
        nameInputGroup.layout = {
            width: "auto",
            height: "auto",
            flexDirection: "row",
            justifyContent: "center",
            alignItems: "center",
            gap: 12,
        };

        const textbox = new GameTextbox({ placeholder: "Enter your name" });

        const button = new GameButton({
            label: "Continue",
            width: 120,
            onClick: async () => {
                const name = textbox.getText().trim();
                if (!name) return;

                // แทนที่จะเรียก onNext() ตรงๆ, ให้เรียก triggerFSMEvent
                this.triggerFSMEvent(GameEvents.PLAYER_NAME_ENTERED, { playerName: name });
            },
        });

        nameInputGroup.addChild(textbox.view, button.view);
        this.addChild(nameInputGroup);
    }
}