// frontend/SceneManager.js

/**
 * SceneManager class is responsible for managing the display of different scenes
 * within the PixiJS application. It handles adding and removing scenes from the stage.
 */
export class SceneManager {
    /**
     * @param {PIXI.Application} app - The PixiJS Application instance.
     */
    constructor(app) {
        this.app = app; // Store a reference to the PixiJS application.
        this.currentScene = null; // Initialize currentScene to null, as no scene is active initially.
    }

    /**
     * Changes the currently displayed scene.
     * If there's an existing scene, it's removed from the PixiJS stage before the new one is added.
     * @param {PIXI.Container} scene - The new scene (a PixiJS Container or a class extending it) to display.
     */
    changeScene(scene) {
        // Check if there is a current scene active on the stage.
        if (this.currentScene) {
            // If yes, remove the current scene from the PixiJS application's stage.
            // This ensures that only one scene is visible at a time.
            this.app.stage.removeChild(this.currentScene);
        }
        // Set the new scene as the current active scene.
        this.currentScene = scene;
        // Add the new scene to the PixiJS application's stage, making it visible.
        this.app.stage.addChild(scene);
    }
}
