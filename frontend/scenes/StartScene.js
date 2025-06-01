// scenes/StartScene.js
import { Container, Text, TextStyle } from "pixi.js";
import { GameTextbox } from "../components/GameTextbox.js";
import { GameButton } from "../components/GameButton.js";

export class StartScene extends Container {
  constructor(onNext) {
    super();

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
      flexDirection: "row", // 👈 จัดเรียงแนวนอน
      justifyContent: "center",
      alignItems: "center",
      gap: 12, // ระยะห่างระหว่าง textbox กับ button
    };

    const textbox = new GameTextbox({ placeholder: "Enter yourrrr" });

    const button = new GameButton({
      label: "Continue",
      width: 120,
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

    nameInputGroup.addChild(textbox.view, button.view);
    this.addChild(nameInputGroup);
  }
}
