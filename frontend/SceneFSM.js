// frontend/SceneFSM.js

// Import necessary modules.
import { SceneManager } from './SceneManager.js'; // The SceneManager is responsible for displaying and managing PixiJS scenes.
import { StartScene } from './scenes/StartScene.js'; // Scene for the initial screen where players enter their name.
import { LobbyScene } from './scenes/LobbyScene.js'; // Scene for the game lobby, where players can create or join rooms.
import { RoomScene } from './scenes/RoomScene.js'; // Scene for a specific game room.
// import { GameScene } from './scenes/GameScene.js'; // To be imported when the GameScene is implemented.

// Define the possible states of the game.
// These states represent different phases or screens of the application.
const GameStates = {
    INIT: 'INIT', // Initial state of the FSM before any scene is displayed.
    START_SCREEN: 'START_SCREEN', // State for the initial screen where the player enters their name.
    LOBBY: 'LOBBY', // State for the game lobby.
    ROOM: 'ROOM', // State when the player is inside a specific game room.
    GAME: 'GAME', // State when the actual game is being played.
    // Future states can be added here, e.g., GAME_OVER, PAUSE.
};

// Define the events that can trigger state transitions.
// These events are typically triggered by user interactions or game logic.
const GameEvents = {
    PLAYER_NAME_ENTERED: 'PLAYER_NAME_ENTERED', // Event triggered when a player enters their name.
    ROOM_CREATED: 'ROOM_CREATED', // Event triggered when a new game room is created.
    ROOM_JOINED: 'ROOM_JOINED', // Event triggered when a player joins an existing room.
    EXIT_ROOM: 'EXIT_ROOM', // Event triggered when a player leaves a room.
    GAME_STARTED: 'GAME_STARTED', // Event triggered when a game within a room starts.
    // Additional events can be added as per game interactions.
};

/**
 * SceneFSM (Finite State Machine) class manages the overall game flow
 * by controlling which scene is active based on game states and events.
 */
export class SceneFSM {
    /**
     * @param {PIXI.Application} app - The PixiJS Application instance.
     * @param {SceneManager} sceneManager - The SceneManager instance.
     */
    constructor(app, sceneManager) {
        this.app = app; // Reference to the PixiJS application.
        this.sceneManager = sceneManager; // Reference to the SceneManager.
        this.currentState = GameStates.INIT; // The current active state of the FSM, initialized to INIT.
        this.context = {}; // An object to store shared data across different states (e.g., playerName, roomId).

        // Define the transition rules between states.
        // Each state has an object of events that can trigger a state change,
        // and a function that returns the next state.
        this.transitions = {
            [GameStates.INIT]: {
                // If a playerName is found in localStorage, directly transition to Lobby.
                [GameEvents.PLAYER_NAME_ENTERED]: (data) => {
                    this.context.playerName = data.playerName;
                    return GameStates.LOBBY;
                },
                // Initial event to start the FSM, typically leading to the StartScreen if no player name is stored.
                start: () => GameStates.START_SCREEN,
            },
            [GameStates.START_SCREEN]: {
                // When PLAYER_NAME_ENTERED event occurs in START_SCREEN state:
                [GameEvents.PLAYER_NAME_ENTERED]: (data) => {
                    this.context.playerName = data.playerName; // Store the player name in context.
                    localStorage.setItem("playerName", data.playerName); // Save the player name to local storage.
                    return GameStates.LOBBY; // Transition to the LOBBY state.
                },
            },
            [GameStates.LOBBY]: {
                // When ROOM_CREATED event occurs in LOBBY state:
                [GameEvents.ROOM_CREATED]: (data) => {
                    this.context.roomId = data.roomId; // Store the room ID in context.
                    return GameStates.ROOM; // Transition to the ROOM state.
                },
                // When ROOM_JOINED event occurs in LOBBY state:
                [GameEvents.ROOM_JOINED]: (data) => {
                    this.context.roomId = data.roomId; // Store the room ID in context.
                    return GameStates.ROOM; // Transition to the ROOM state.
                },
            },
            [GameStates.ROOM]: {
                // When GAME_STARTED event occurs in ROOM state:
                [GameEvents.GAME_STARTED]: () => GameStates.GAME, // Transition to the GAME state.
                // When EXIT_ROOM event occurs in ROOM state:
                [GameEvents.EXIT_ROOM]: () => {
                    delete this.context.roomId; // Remove roomId from context when exiting the room.
                    return GameStates.LOBBY; // Transition back to the LOBBY state.
                },
            },
            [GameStates.GAME]: {
                // TODO: Define transitions for the GAME state (e.g., GAME_ENDED -> LOBBY or GAME_OVER).
                // Example: Exiting the game mid-play.
                [GameEvents.EXIT_ROOM]: () => {
                    delete this.context.roomId; // Clear room ID if exiting game.
                    return GameStates.LOBBY; // Return to Lobby.
                }
            },
        };
    }

    /**
     * This function is passed to child scenes to allow them to trigger events back to the FSM.
     * Scenes are only responsible for "firing events" and do not need to know which scene comes next.
     * @param {string} event - The name of the event to trigger (from GameEvents).
     * @param {object} [data={}] - Optional data associated with the event.
     */
    triggerEvent = (event, data = {}) => {
        // Find the transition function for the current state and triggered event.
        const nextStateFunction = this.transitions[this.currentState]?.[event];
        if (nextStateFunction) {
            // Execute the transition function to get the next state.
            const nextState = nextStateFunction(data);
            // Check if a valid next state is returned and if it's different from the current state.
            if (nextState && nextState !== this.currentState) {
                console.log(`FSM: Transitioning from ${this.currentState} to ${nextState} via event ${event}`);
                this.changeState(nextState); // Change to the new state.
            } else if (nextState === this.currentState) {
                // Log if the event did not cause a state change (e.g., event handled but no transition).
                console.log(`FSM: Event ${event} in state ${this.currentState} did not cause state change.`);
            } else {
                // Warn if the transition function returned an invalid or null next state.
                console.warn(`FSM: No valid next state for event ${event} in state ${this.currentState}`);
            }
        } else {
            // Warn if the triggered event is not defined for the current state.
            console.warn(`FSM: Event ${event} is not defined for state ${this.currentState}`);
        }
    };

    /**
     * Changes the current state of the FSM and loads the corresponding scene.
     * @param {string} newState - The new state to transition to (from GameStates).
     */
    changeState(newState) {
        this.currentState = newState; // Update the current state.
        let sceneInstance; // Variable to hold the new scene instance.

        // Use a switch statement to create the appropriate scene instance based on the new state.
        switch (newState) {
            case GameStates.START_SCREEN:
                // StartScene receives the triggerEvent callback.
                sceneInstance = new StartScene(this.triggerEvent);
                break;
            case GameStates.LOBBY:
                // LobbyScene requires playerName and the triggerEvent callback.
                if (!this.context.playerName) {
                    console.error("FSM: Missing playerName for LobbyState. Returning to StartScreen.");
                    this.changeState(GameStates.START_SCREEN); // Fallback: go back to StartScreen if data is missing.
                    return;
                }
                sceneInstance = new LobbyScene(this.context.playerName, this.triggerEvent);
                break;
            case GameStates.ROOM:
                // RoomScene requires roomId, playerName, and the triggerEvent callback.
                if (!this.context.roomId || !this.context.playerName) {
                    console.error("FSM: Missing roomId or playerName for RoomState. Returning to Lobby.");
                    this.changeState(GameStates.LOBBY); // Fallback: go back to Lobby if data is missing.
                    return;
                    }
                sceneInstance = new RoomScene(this.context.roomId, this.context.playerName, this.triggerEvent);
                break;
            case GameStates.GAME:
                // TODO: Create and instantiate the GameScene here.
                // sceneInstance = new GameScene(this.context.roomId, this.context.playerName, this.triggerEvent);
                console.log("FSM: TODO: Load GameScene here!");
                // If GameScene is not yet implemented, you might want to prevent staying in this state
                // by transitioning back to a previous state, e.g., this.changeState(GameStates.ROOM);
                // return;
                break;
            default:
                // Log an error for unknown or unhandled states.
                console.error("FSM: Unknown or unhandled game state:", newState);
                return;
        }

        // If a scene instance was successfully created, tell the SceneManager to change the current scene.
        if (sceneInstance) {
            this.sceneManager.changeScene(sceneInstance);
        }
    }
}

// Export GameStates and GameEvents so they can be imported and used by other modules (e.g., main.js).
export { GameStates, GameEvents };
