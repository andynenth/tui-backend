// scenes/StartScene.js
import { Container, Text, TextStyle } from 'pixi.js';
import { GameTextbox } from '../components/GameTextbox.js';
import { GameButton } from '../components/GameButton.js';
import { createRoom } from '../api.js';




export class StartScene extends Container {
    constructor(onNext) {
        super();
        this.layout = { justifyContent: 'center', alignItems: 'center', gap: 16 };

        const textbox = new GameTextbox({ placeholder: 'Enter yourrrrr' });
        const statusText = new Text({ text: '', style: new TextStyle({ fill: '#ffffff' }) });

        const button = new GameButton({
            label: 'Continue',
            onClick: async () => {
                const name = textbox.getText().trim();
                if (!name) return;

                try {
                    const result = await createRoom(name); 
                    statusText.text = `✅ Room ID: ${result.room_id}`;
                    console.log("Created room:", result.room_id);
                } catch (err) {
                    statusText.text = "❌ Failed to create room";
                    console.error(err);
                }
            }
        });

        this.addChild(textbox.view, button.view, statusText);
    }
}
