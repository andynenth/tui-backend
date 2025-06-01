// frontend/components/GameButton.js
import { Container, Graphics, Text, TextStyle } from 'pixi.js';
import { Button as PixiButton } from '@pixi/ui';

export class GameButton {
    constructor({
        label = 'Click me',
        width = 150,
        height = 50,
        radius = 12,
        bgColor = 0x4f46e5,
        textColor = '#ffffff',
        onClick = () => {},
    }) {
        this.label = label;
        this.width = width;
        this.height = height;
        this.radius = radius;
        this.bgColor = bgColor;
        this.textColor = textColor;
        this.onClick = onClick;

        this._createView();
        this._bindEvents();
    }

    _createView() {
        // ✅ Create a container for layout + content
        const wrapper = new Container();
        wrapper.eventMode = 'static'; // Allow interaction
        wrapper.cursor = 'pointer';

        // Background
        const bg = new Graphics()
            .roundRect(0, 0, this.width, this.height, this.radius)
            .fill(this.bgColor);

        // Text
        const textStyle = new TextStyle({
            fontFamily: 'Arial',
            fontSize: 20,
            fill: this.textColor,
        });
        this.text = new Text({ text: this.label, style: textStyle });
        this.text.anchor.set(0.5);
        this.text.x = this.width / 2;
        this.text.y = this.height / 2;

        wrapper.addChild(bg);
        wrapper.addChild(this.text);

        // ✅ Wrap container with PixiButton
        this.button = new PixiButton(wrapper);

        // ✅ Container used for layout on stage
        this.view = new Container({
            layout: {
                width: this.width,
                height: this.height,
                justifyContent: 'center',
                alignItems: 'center',
            },
        });

        this.view.addChild(this.button.view);
    }

    _bindEvents() {
        this.button.onPress.connect(() => {
            this.onClick();
        });
    }

    setText(newText) {
        this.text.text = newText;
    }

    setEnabled(isEnabled) {
        this.button.enabled = isEnabled;
        this.view.alpha = isEnabled ? 1 : 0.5;
    }
}
