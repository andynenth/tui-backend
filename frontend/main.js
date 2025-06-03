// frontend/main.js

// Import necessary modules from PixiJS and local files.
import { Application } from "pixi.js"; // Core PixiJS Application class for creating the canvas and managing the rendering loop.
import "@pixi/layout"; // Import PixiJS Layout plugin for responsive layout management.
import "@pixi/layout/devtools"; // Import PixiJS Layout DevTools for debugging layout.
import { SceneManager } from "./SceneManager.js"; // Custom SceneManager to handle different game scenes.
import { SceneFSM, GameStates, GameEvents } from "./SceneFSM.js"; // Custom Finite State Machine (FSM) for managing game states and transitions.
import { initDevtools } from "@pixi/devtools"; // For initializing PixiJS DevTools in the browser.

// Define an asynchronous IIFE (Immediately Invoked Function Expression) to encapsulate the main application logic.
(async () => {
    // Create a new PixiJS Application instance.
    const app = new Application();

    // Initialize PixiJS DevTools. This allows inspecting the PixiJS scene graph in the browser's developer tools.
    initDevtools({ app });

    // Initialize the PixiJS application with specific dimensions and background color.
    await app.init({
        width: 540, // Set the width of the canvas.
        height: 960, // Set the height of the canvas.
        background: "#1e1e2e", // Set the background color of the canvas (a dark purplish-blue).
    });

    // Append the PixiJS canvas element to the HTML document body.
    document.body.appendChild(app.canvas);

    // Configure the layout for the PixiJS stage.
    // This makes the stage responsive to the application's screen dimensions.
    app.stage.layout = {
        width: app.screen.width, // Set the layout width to match the application screen width.
        height: app.screen.height, // Set the layout height to match the application screen height.
    };

    // Create an instance of the SceneManager, passing the PixiJS application instance.
    // The SceneManager will be responsible for adding, removing, and managing different game scenes.
    const sceneManager = new SceneManager(app);

    // Create an instance of the Finite State Machine (FSM) to control the scene flow.
    // This FSM will dictate which scene is active based on game states and events.
    const gameFSM = new SceneFSM(app, sceneManager);

    // Attempt to retrieve a stored player name from the browser's local storage.
    const storedPlayerName = localStorage.getItem("playerName");

    // Check if a player name was found in local storage.
    if (storedPlayerName) {
        // If a player name exists:
        // Set the retrieved player name in the FSM's context (accessible by states).
        gameFSM.context.playerName = storedPlayerName;
        // Transition the FSM directly to the LOBBY state.
        gameFSM.changeState(GameStates.LOBBY);
        // Log a message to the console indicating the found name and starting state.
        console.log(`Main: Found stored player name: ${storedPlayerName}. Starting at Lobby.`);
    } else {
        // If no player name was found:
        // Transition the FSM to the START_SCREEN state, prompting the player to enter their name.
        gameFSM.changeState(GameStates.START_SCREEN);
        // Log a message to the console indicating no stored name and starting at the Start Screen.
        console.log("Main: No stored player name. Starting at Start Screen.");
    }

    // Comment: Direct scene creation and transitions are no longer handled here in main.js.
    // All scene management and flow control are now delegated to the `gameFSM` (Finite State Machine).
})();
