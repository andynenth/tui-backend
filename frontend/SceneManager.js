// frontend/SceneManager.js
export class SceneManager {
    constructor(app) {
        this.app = app;
        this.currentScene = null;
    }

    changeScene(scene) {
        if (this.currentScene) this.app.stage.removeChild(this.currentScene);
        this.currentScene = scene;
        this.app.stage.addChild(scene);
    }
}
