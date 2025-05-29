// scenes/StartScene.js
import { Container, Text } from 'pixi.js';
import { GameTextbox } from '../components/GameTextbox.js';
import { GameButton } from '../components/GameButton.js';

export class StartScene extends Container {
    constructor(onNext) {
        super();
        this.layout = { justifyContent: 'center', alignItems: 'center' };

        const textbox = new GameTextbox({ placeholder: 'Your name' });
        const button = new GameButton({
            label: 'Continue',
            onClick: () => {
                const name = textbox.getText();
                onNext(name);
            }
        });

        this.addChild(textbox.view, button.view);
    }
}
