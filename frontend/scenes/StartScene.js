// scenes/StartScene.js
import { Container, Text, TextStyle } from "pixi.js";
import { GameTextbox } from "../components/GameTextbox.js";
import { GameButton } from "../components/GameButton.js";
import { createRoom } from "../api.js";

export class StartScene extends Container {
  constructor(onNext) {
    super();

    console.log("🔵 Entered StartScene");

    this.layout = { justifyContent: "center", alignItems: "center", gap: 16 };

    const textbox = new GameTextbox({ placeholder: "Enter yourrrr" });


    const button = new GameButton({
      label: "Continue",
      onClick: async () => {
        const name = textbox.getText().trim();
        if (!name) return;

        try {
          onNext(name);
        } catch (err) {
          console.error(err);
        }
      },
    });

    this.addChild(textbox.view, button.view);
  }
}
