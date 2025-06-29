# Backend Documentation

This document provides a detailed overview of the backend system for the Liap Tui project.

## Table of Contents

*   [Application Entry Point](#application-entry-point)
*   [Game Engine](#game-engine)
*   [Enterprise State Machine](#enterprise-state-machine)
*   [WebSocket API](#websocket-api)
*   [Bot Manager](#bot-manager)

## Application Entry Point

The main entry point for the backend application is `backend/api/main.py`. This file is responsible for:

*   Initializing the FastAPI application.
*   Configuring CORS middleware to allow the frontend to connect.
*   Including the REST and WebSocket routers.
*   Serving the static frontend files.

### Key Functions in `main.py`

*   **`FastAPI()`**: Creates the main application instance.
*   **`app.add_middleware(CORSMiddleware, ...)`**: Configures the application to accept requests from different origins.
*   **`app.include_router(...)`**: Mounts the API and WebSocket endpoints.
*   **`app.mount(...)`**: Serves the compiled frontend application.

## Game Engine

The core game logic is contained within `backend/engine/game.py`. This module defines the `Game` class, which manages the state of a single game instance.

### The `Game` Class

The `Game` class is responsible for:

*   Managing the players in the game.
*   Dealing pieces to players.
*   Tracking the game state, including the current round, turn, and scores.
*   Enforcing the game rules.
*   Calculating scores at the end of each round.

### Key Functions in `game.py`

*   **`deal_pieces()`**: Shuffles the deck and deals pieces to each player.
*   **`request_redeal(...)`**: Allows a player to request a redeal if they have a weak hand.
*   **`declare(...)`**: Records a player's declaration of how many piles they will win.
*   **`play_turn(...)`**: Processes a player's move, validates it, and resolves the turn.
*   **`score_round()`**: Calculates the scores for each player at the end of a round.

## Enterprise State Machine

The backend uses a sophisticated state machine to manage the flow of the game. The state machine is defined in `backend/engine/state_machine/game_state_machine.py`.

### The `GameStateMachine` Class

The `GameStateMachine` class is the central coordinator for the game's state. It is responsible for:

*   Managing the transitions between different game phases (`PREPARATION`, `DECLARATION`, `TURN`, `SCORING`).
*   Processing player actions through an action queue.
*   Delegating action handling to the appropriate state object.
*   Broadcasting state changes to all connected clients.

### Key Functions in `game_state_machine.py`

*   **`start()`**: Initializes and starts the state machine.
*   **`handle_action(...)`**: Adds a player's action to the processing queue.
*   **`_process_loop()`**: The main loop that processes actions and manages phase transitions.
*   **`_transition_to(...)`**: Handles the logic for transitioning from one phase to another.
*   **`broadcast_event(...)`**: Sends WebSocket messages to all clients in the game room.

## WebSocket API

The real-time communication between the frontend and backend is handled by the WebSocket API, defined in `backend/api/routes/ws.py`.

### The `websocket_endpoint` Function

This function is the main entry point for all WebSocket connections. It is responsible for:

*   Registering new client connections.
*   Receiving and processing messages from clients.
*   Broadcasting messages to all clients in a room.
*   Handling client disconnections.

### Key Events Handled by the WebSocket API

*   **`client_ready`**: Sent by the client when it has connected and is ready to receive data.
*   **`create_room`**: Sent by a client to create a new game room.
*   **`join_room`**: Sent by a client to join an existing game room.
*   **`start_game`**: Sent by the host to start the game.
*   **`declare`**: Sent by a player to make their declaration.
*   **`play`**: Sent by a player to play their pieces.

## Bot Manager

The `BotManager` class, located in `backend/engine/bot_manager.py`, is responsible for managing the AI players in the game.

### The `BotManager` Class

The `BotManager` is a singleton class that:

*   Registers and unregisters games that have bot players.
*   Receives game events from the state machine.
*   Uses the `engine.ai` module to make decisions for the bots.
*   Sends bot actions to the state machine for processing.

### Key Functions in `bot_manager.py`

*   **`register_game(...)`**: Adds a new game to the bot manager.
*   **`handle_game_event(...)`**: The main entry point for processing game events.
*   **`_handle_declaration_phase(...)`**: Manages the bot's declaration.
*   **`_handle_play_phase(...)`**: Manages the bot's turn.
*   **`_bot_play(...)`**: Determines the best play for the bot and sends it to the state machine.