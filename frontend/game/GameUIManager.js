export class GameUIManager {
    constructor(container) {
        this.container = container;
        this.current = null;
    }

    showPhase(name) {
        if (this.current) this.container.removeChild(this.current.view);
        // load new UI เช่น DeclareUI, PlayUI, ScoreUI
        this.current = this._createUIFor(name);
        this.container.addChild(this.current.view);
    }

    _createUIFor(name) {
        // return new DeclareUI(), new PlayUI(), etc.
    }
}
