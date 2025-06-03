// frontend/scenes/StartScene.js

// Import necessary modules from PixiJS and local components.
import { Container, Text, TextStyle } from "pixi.js"; // PixiJS Container for scene structure, Text for displaying text, TextStyle for text styling.
import { GameTextbox } from "../components/GameTextbox.js"; // Custom Textbox component for user input.
import { GameButton } from "../components/GameButton.js"; // Custom Button component for interactive elements.
import { GameEvents } from '../SceneFSM.js'; // Import GameEvents enum from the SceneFSM for triggering state transitions.

/**
 * StartScene class represents the initial screen of the game where the player
 * is prompted to enter their name.
 * It extends PixiJS Container to act as a display object.
 */
export class StartScene extends Container {
    /**
     * Constructor for the StartScene.
     * @param {function} triggerFSMEvent - A callback function to trigger events in the FSM.
     * This allows the scene to communicate with the FSM
     * without knowing the next state directly.
     */
    constructor(triggerFSMEvent) {
        super(); // Call the constructor of the parent class (Container).
        this.triggerFSMEvent = triggerFSMEvent; // Store the FSM event trigger callback.

        console.log("🔵 Entered StartScene"); // Log a message indicating entry into this scene.

        // Define the layout properties for the entire scene container.
        // These properties are used by the PixiJS Layout plugin for responsive design.
        this.layout = {
            width: "100%", // Scene takes full width of its parent (app.stage).
            height: "100%", // Scene takes full height of its parent.
            justifyContent: "center", // Horizontally center its children.
            alignItems: "center", // Vertically center its children.
        };

        // Create a container for the name input elements (textbox and button).
        const nameInputGroup = new Container();
        // Define layout properties for the input group.
        nameInputGroup.layout = {
            width: "auto", // Width adjusts to content.
            height: "auto", // Height adjusts to content.
            flexDirection: "row", // Arrange children in a row.
            justifyContent: "center", // Horizontally center children within the group.
            alignItems: "center", // Vertically center children within the group.
            gap: 12, // Add a gap of 12 pixels between children.
        };

        // Create a new GameTextbox instance for player name input.
        const textbox = new GameTextbox({ placeholder: "Enter your name" });

        // Create a new GameButton instance for the "Continue" action.
        const button = new GameButton({
            label: "Continue", // Text displayed on the button.
            width: 120, // Fixed width for the button.
            onClick: async () => {
                const name = textbox.getText().trim(); // Get the text from the textbox and trim whitespace.
                if (!name) return; // If the name is empty, do nothing.

                // Instead of directly calling a 'onNext()' method,
                // trigger the FSM event to signal that the player name has been entered.
                // The FSM will then decide the next state (e.g., transition to LobbyScene).
                this.triggerFSMEvent(GameEvents.PLAYER_NAME_ENTERED, { playerName: name });
            },
        });

        // Add the textbox and button views to the name input group.
        nameInputGroup.addChild(textbox.view, button.view);
        // Add the entire name input group to the main scene container.
        this.addChild(nameInputGroup);
    }
}
