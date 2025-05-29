import { Container, Graphics, Text, TextStyle, Ticker } from 'pixi.js';
import { Button } from '@pixi/ui';

export class GameTextbox {
    constructor({
        width = 240,
        height = 50,
        placeholder = 'Your Name',
        maxLength = 12,
        onChange = () => {},
    }) {
        this.width = width;
        this.height = height;
        this.placeholder = placeholder;
        this.maxLength = maxLength;
        this.onChange = onChange;

        this.inputText = '';
        this.isFocused = false;

        this._createView();
        this._bindEvents();
        this._startCursorBlink();
    }

    _createView() {
        const bg = new Graphics()
            .rect(0, 0, this.width, this.height, 8)
            .fill(0x374151);

        this.text = new Text({ text: '', style: new TextStyle({
            fontFamily: 'Arial',
            fontSize: 20,
            fill: '#ffffff',
        })});
        this.text.x = 12;
        this.text.y = 12;

        this.placeholderText = new Text({
            text: this.placeholder,
            style: new TextStyle({
                fontFamily: 'Arial',
                fontSize: 20,
                fill: '#aaaaaa',
            }),
        });
        this.placeholderText.x = 12;
        this.placeholderText.y = 12;

        this.cursor = new Graphics()
            .fill(0xffffff)
            .rect(0, 0, 2, 20);
        this.cursor.y = 15;
        this.cursor.visible = false;

        this.button = new Button(bg);
        this.view = new Container({
            layout: {
                width: this.width,
                height: this.height,
                justifyContent: 'flex-start',
                alignItems: 'center',
                padding: 8,
            },
        });

        this.view.addChild(this.button.view);
        this.view.addChild(this.placeholderText);
        this.view.addChild(this.text);
        this.view.addChild(this.cursor);
    }

    _bindEvents() {
        this.button.onPress.connect(() => this.focus());

        window.addEventListener('pointerdown', (e) => {
            const bounds = document.body.getBoundingClientRect();
            const clickX = e.clientX - bounds.left;
            const clickY = e.clientY - bounds.top;
            const global = this.view.getGlobalPosition();

            if (
                clickX < global.x || clickX > global.x + this.width ||
                clickY < global.y || clickY > global.y + this.height
            ) {
                this.blur();
            }
        });

        window.addEventListener('keydown', (e) => {
            if (!this.isFocused) return;

            if (e.key === 'Backspace') {
                this.inputText = this.inputText.slice(0, -1);
            } else if (e.key.length === 1 && this.inputText.length < this.maxLength) {
                this.inputText += e.key;
            }

            this.text.text = this.inputText;
            this.placeholderText.visible = this.inputText === '';
            this.cursor.x = this.text.x + this.text.width + 4;
            this.onChange(this.inputText);
        });
    }

    _startCursorBlink() {
        Ticker.shared.add(() => {
            if (this.isFocused) {
                const time = Date.now() % 1000;
                this.cursor.visible = time < 500;
            }
        });
    }

    focus() {
        this.isFocused = true;
        this.cursor.visible = true;
        if (this.inputText === '') {
            this.placeholderText.visible = false;
        }
    }

    blur() {
        this.isFocused = false;
        this.cursor.visible = false;
        if (this.inputText === '') {
            this.placeholderText.visible = true;
        }
    }

    getText() {
        return this.inputText;
    }

    setText(text) {
        this.inputText = text.slice(0, this.maxLength);
        this.text.text = this.inputText;
        this.placeholderText.visible = this.inputText === '';
        this.cursor.x = this.text.x + this.text.width + 4;
    }
}
