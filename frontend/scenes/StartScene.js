// scenes/StartScene.js
import { Container, Text, TextStyle } from 'pixi.js';
import { GameTextbox } from '../components/GameTextbox.js';
import { GameButton } from '../components/GameButton.js';
import { createRoom } from '../api.js'; // ✅ WORK 100%




export class StartScene extends Container {
    constructor(onNext) {
        super();
        this.layout = { justifyContent: 'center', alignItems: 'center', gap: 16 };

        const textbox = new GameTextbox({ placeholder: 'Your name' });
        const statusText = new Text({ text: '', style: new TextStyle({ fill: '#ffffff' }) });

        const button = new GameButton({
            label: 'Continue',
            onClick: async () => {
                const name = textbox.getText().trim();
                if (!name) return;

                try {
                    const result = await createRoom(name); // ✅ เรียก API
                    statusText.text = `✅ Room ID: ${result.room_id}`;
                    console.log("Created room:", result.room_id);
                } catch (err) {
                    statusText.text = "❌ Failed to create room";
                    console.error(err);
                }

                // 🔹 ถ้าต้องการไปต่อหลังจากสร้างห้อง:
                // onNext(name);
            }
        });

        this.addChild(textbox.view, button.view, statusText);
    }
}
