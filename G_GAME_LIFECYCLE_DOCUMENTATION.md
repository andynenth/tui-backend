# Game UI Redesign: Technical Documentation

This document provides a detailed technical breakdown of the game's lifecycle, API, and data structures to support the UI redesign.

## Phase 1: WAITING

### Description

The WAITING phase covers the period from when a player is in the lobby to when the game starts. This includes creating, listing, and joining rooms.

### Game Lifecycle Flow

1.  **Lobby:** The user starts in the lobby, where they can see a list of available rooms.
2.  **Create Room:** A user can create a new room, becoming the host.
3.  **Join Room:** A user can join an existing room.
4.  **Room View:** Once in a room, users can see the other players who have joined. The host can start the game.
5.  **Game Start:** The host starts the game, transitioning all players in the room to the PREPARATION phase.

### API Endpoints & Payloads

#### REST Endpoints

*   **`POST /api/create-room`**: Creates a new game room.
    *   **Request Query Params:** `name` (string) - The name of the host.
    *   **Response Payload:** `{"room_id": "...", "host_name": "..."}`
*   **`POST /api/join-room`**: Joins an existing game room.
    *   **Request Query Params:** `room_id` (string), `name` (string)
    *   **Response Payload:** `{"slots": [...], "host_name": "...", "assigned_slot": "..."}`
*   **`GET /api/list-rooms`**: Retrieves a list of available rooms.
    *   **Response Payload:** `{"rooms": [{"room_id": "...", "host_name": "...", "occupied_slots": "...", "total_slots": "..."}]}`
*   **`POST /api/start-game`**: Starts the game.
    *   **Request Query Params:** `room_id` (string)
    *   **Response Payload:** `{"ok": true}`

#### WebSocket Events

*   **Client to Server:**
    *   `{"event": "get_rooms", "data": {}}`: Requests the list of rooms.
*   **Server to Client:**
    *   `{"event": "room_list_update", "data": {"rooms": [...]}}`: Sent when the list of rooms changes.
    *   `{"event": "room_created", "data": {"room_id": "...", "host_name": "..."}}`: Sent when a new room is created.
    *   `{"event": "room_state_update", "data": {"slots": [...], "host_name": "..."}}`: Sent when a player joins or leaves a room.
    *   `{"event": "room_closed", "data": {"message": "..."}}`: Sent when a room is closed.

### State Management

*   **Global State (React Context - `AppContext`):**
    *   `playerName`: The name of the current player.
    *   `currentRoomId`: The ID of the room the player is currently in.
*   **Local State (`LobbyPage.jsx`):**
    *   `rooms`: A list of available rooms.
    *   `isConnected`: A boolean indicating if the WebSocket is connected.

### Event Handling

The WAITING phase uses a combination of REST API calls and WebSockets.

*   **REST API:** Used for initial actions like creating and joining rooms.
*   **WebSockets:** Used for real-time updates, such as when the list of rooms changes or when players join or leave a room. The client subscribes to the `lobby` room to receive lobby-wide updates.

### Scene/Component Architecture

*   **`LobbyPage.jsx`:** The main component for the lobby. It displays the list of rooms and handles creating and joining rooms.
*   **`RoomPage.jsx`:** The main component for the room view. It displays the players in the room and allows the host to start the game.

### Data Structures

*   **Room:**
    ```json
    {
      "room_id": "string",
      "host_name": "string",
      "occupied_slots": "number",
      "total_slots": "number",
      "players": ["string"],
      "started": "boolean"
    }
    ```
*   **Player:**
    ```json
    {
      "name": "string"
    }
    ```

## Phase 2: PREPARATION

### Description

The PREPARATION phase begins when the host starts the game. In this phase, the server deals cards to each player and checks for weak hands. If a player has a weak hand, they can choose to redeal.

### Game Lifecycle Flow

1.  **Game Start:** The host clicks the "Start Game" button.
2.  **Server Deals Cards:** The server deals 8 cards to each player.
3.  **Weak Hand Check:** The server checks if any player has a "weak hand" (a hand with a total value below a certain threshold).
4.  **Redeal Offer:** If a player has a weak hand, the server offers them the option to redeal.
5.  **Player Decision:** The player with the weak hand can either accept or decline the redeal.
6.  **Redeal:** If the player accepts, the cards are redealt, and the process repeats. If they decline, the game proceeds to the DECLARATION phase.

### API Endpoints & Payloads

#### REST Endpoints

*   **`POST /api/redeal-decision`**: Submits a player's decision to redeal.
    *   **Request Query Params:** `room_id` (string), `player_name` (string), `choice` (string: "accept" or "decline")
    *   **Response Payload:** `{"status": "ok", "choice": "..."}`

#### WebSocket Events

*   **Server to Client:**
    *   `{"event": "phase_change", "data": {"phase": "PREPARATION", ...}}`: Notifies the client that the game has entered the PREPARATION phase.
    *   `{"event": "weak_hand_offer", "data": {"player_name": "..."}}`: Offers a player the option to redeal.
    *   `{"event": "redeal_decision", "data": {"player_name": "...", "choice": "..."}}`: Informs all players of a player's redeal decision.
    *   `{"event": "deal", "data": {"hands": {...}}}`: Sends the new hands to all players after a redeal.

### State Management

*   **Global State (React Context - `GameContext`):**
    *   `gameState`: An object containing the entire game state, including the current phase, players, hands, and redeal information.
*   **Local State (`PreparationUI.jsx`):**
    *   The component receives its state from the `GameContainer` via props.

### Event Handling

The PREPARATION phase is driven entirely by WebSockets. The server pushes state changes to the clients, and the clients send their redeal decisions to the server via WebSocket messages.

### Scene/Component Architecture

*   **`GamePage.jsx`:** The main container for the game.
*   **`GameContainer.jsx`:** A smart container that connects the UI components to the game state.
*   **`PreparationUI.jsx`:** The UI component for the PREPARATION phase. It displays the player's hand and the redeal offer, if applicable.

### Data Structures

*   **GameState:**
    ```json
    {
      "phase": "PREPARATION",
      "players": [...],
      "hands": {
        "player1": [...],
        "player2": [...]
      },
      "weak_hand_player": "string",
      "redeal_offered": "boolean"
    }
    ```

## Phase 3: DECLARATION

### Description

In the DECLARATION phase, each player declares how many piles of cards they believe they will win in the round.

### Game Lifecycle Flow

1.  **Phase Transition:** The game transitions from the PREPARATION phase to the DECLARATION phase.
2.  **Player Declaration:** Each player, in turn, declares the number of piles they expect to win.
3.  **Last Player Rule:** The last player to declare cannot choose a number that would make the total number of declared piles equal to 8.
4.  **Phase Transition:** Once all players have made their declarations, the game transitions to the TURN phase.

### API Endpoints & Payloads

#### REST Endpoints

*   **`POST /api/declare`**: Submits a player's declaration.
    *   **Request Query Params:** `room_id` (string), `player_name` (string), `value` (number)
    *   **Response Payload:** `{"status": "ok"}`

#### WebSocket Events

*   **Server to Client:**
    *   `{"event": "phase_change", "data": {"phase": "DECLARATION", ...}}`: Notifies the client that the game has entered the DECLARATION phase.
    *   `{"event": "next_declarer", "data": {"player_name": "..."}}`: Informs the clients whose turn it is to declare.
    *   `{"event": "declaration", "data": {"player_name": "...", "value": "..."}}`: Informs all players of a player's declaration.

### State Management

*   **Global State (React Context - `GameContext`):**
    *   `gameState`: An object containing the entire game state, including the current phase, players, and declarations.
*   **Local State (`DeclarationUI.jsx`):**
    *   The component receives its state from the `GameContainer` via props.

### Event Handling

The DECLARATION phase is driven by a combination of REST API calls and WebSockets. Players submit their declarations via a REST API call, and the server broadcasts the updated game state to all clients via WebSockets.

### Scene/Component Architecture

*   **`GamePage.jsx`:** The main container for the game.
*   **`GameContainer.jsx`:** A smart container that connects the UI components to the game state.
*   **`DeclarationUI.jsx`:** The UI component for the DECLARATION phase. It displays the declaration interface for the current player.

### Data Structures

*   **GameState:**
    ```json
    {
      "phase": "DECLARATION",
      "players": [...],
      "declarations": {
        "player1": "number",
        "player2": "number"
      },
      "next_declarer": "string"
    }
    ```

## Phase 4: TURN

### Description

In the TURN phase, players take turns playing pieces from their hands.

### Game Lifecycle Flow

1.  **Phase Transition:** The game transitions from the DECLARATION phase to the TURN phase.
2.  **Player Turn:** The current player plays one or more pieces from their hand.
3.  **Play Validation:** The server validates the play to ensure it is legal.
4.  **Turn Winner:** The server determines the winner of the turn.
5.  **Next Turn:** The winner of the turn starts the next turn.
6.  **Phase Transition:** Once all cards have been played, the game transitions to the SCORING phase.

### API Endpoints & Payloads

#### REST Endpoints

*   **`POST /api/play-turn`**: Submits a player's play.
    *   **Request Query Params:** `room_id` (string), `player_name` (string), `piece_indexes` (string: comma-separated list of numbers)
    *   **Response Payload:** `{"status": "ok"}`

#### WebSocket Events

*   **Server to Client:**
    *   `{"event": "phase_change", "data": {"phase": "TURN", ...}}`: Notifies the client that the game has entered the TURN phase.
    *   `{"event": "next_player", "data": {"player_name": "..."}}`: Informs the clients whose turn it is to play.
    *   `{"event": "play", "data": {"player_name": "...", "pieces": [...]}}`: Informs all players of a player's play.

### State Management

*   **Global State (React Context - `GameContext`):**
    *   `gameState`: An object containing the entire game state, including the current phase, players, hands, and the current turn.
*   **Local State (`TurnUI.jsx`):**
    *   The component receives its state from the `GameContainer` via props.

### Event Handling

The TURN phase is driven by a combination of REST API calls and WebSockets. Players submit their plays via a REST API call, and the server broadcasts the updated game state to all clients via WebSockets.

### Scene/Component Architecture

*   **`GamePage.jsx`:** The main container for the game.
*   **`GameContainer.jsx`:** A smart container that connects the UI components to the game state.
*   **`TurnUI.jsx`:** The UI component for the TURN phase. It displays the player's hand and the playing area.

### Data Structures

*   **GameState:**
    ```json
    {
      "phase": "TURN",
      "players": [...],
      "hands": {
        "player1": [...],
        "player2": [...]
      },
      "current_player": "string",
      "current_turn": {
        "plays": [...]
      }
    }
    ```

## Phase 5: TURN_RESULTS

### Description

This phase is not explicitly defined in the backend code, but it is represented in the frontend. It is the period between turns where the results of the previous turn are displayed.

### Game Lifecycle Flow

1.  **Turn End:** A turn ends when all players have played their cards.
2.  **Display Results:** The UI displays the winner of the turn and the cards that were played.
3.  **Next Turn:** After a short delay, the UI transitions to the next turn.

### API Endpoints & Payloads

This phase does not have any specific API endpoints. The data for this phase is derived from the `play` event in the TURN phase.

### State Management

*   **Global State (React Context - `GameContext`):**
    *   `gameState`: The `GameContainer` uses the `gameState` to determine the winner of the turn and pass the relevant data to the `TurnResultsUI` component.
*   **Local State (`TurnResultsUI.jsx`):**
    *   The component receives its state from the `GameContainer` via props.

### Event Handling

This phase is triggered by the frontend after a `play` event is received from the server. The `GameContainer` component is responsible for managing the transition to and from this phase.

### Scene/Component Architecture

*   **`GamePage.jsx`:** The main container for the game.
*   **`GameContainer.jsx`:** A smart container that connects the UI components to the game state.
*   **`TurnResultsUI.jsx`:** The UI component for the TURN_RESULTS phase. It displays the results of the previous turn.

### Data Structures

There are no new data structures for this phase. The data is derived from the `GameState` object.

## Phase 6: SCORING

### Description

In the SCORING phase, the server calculates the scores for the round and checks if there is a winner.

### Game Lifecycle Flow

1.  **Round End:** The round ends when all cards have been played.
2.  **Score Calculation:** The server calculates the scores for each player based on the number of piles they won versus the number they declared.
3.  **Game Over Check:** The server checks if any player has reached the winning score.
4.  **Phase Transition:** If there is a winner, the game transitions to the GAME_OVER phase. Otherwise, it transitions back to the PREPARATION phase for the next round.

### API Endpoints & Payloads

#### REST Endpoints

*   **`POST /api/score-round`**: Triggers the scoring for the current round.
    *   **Request Query Params:** `room_id` (string)
    *   **Response Payload:** `{"status": "ok"}`

#### WebSocket Events

*   **Server to Client:**
    *   `{"event": "phase_change", "data": {"phase": "SCORING", ...}}`: Notifies the client that the game has entered the SCORING phase.
    *   `{"event": "round_over", "data": {"scores": {...}, "game_over": "...", "winners": [...]}}`: Sent at the end of a round, containing the scores and game over status.

### State Management

*   **Global State (React Context - `GameContext`):**
    *   `gameState`: An object containing the entire game state, including the current phase, players, and scores.
*   **Local State (`ScoringUI.jsx`):**
    *   The component receives its state from the `GameContainer` via props.

### Event Handling

The SCORING phase is triggered by a REST API call from the client. The server then calculates the scores and broadcasts the results to all clients via WebSockets.

### Scene/Component Architecture

*   **`GamePage.jsx`:** The main container for the game.
*   **`GameContainer.jsx`:** A smart container that connects the UI components to the game state.
*   **`ScoringUI.jsx`:** The UI component for the SCORING phase. It displays the scores for the round.

### Data Structures

*   **GameState:**
    ```json
    {
      "phase": "SCORING",
      "players": [...],
      "scores": {
        "player1": "number",
        "player2": "number"
      },
      "game_over": "boolean",
      "winners": ["string"]
    }
    ```

## Phase 7: GAME_OVER

### Description

The GAME_OVER phase is the final phase of the game. It displays the final scores and the winner(s) of the game.

### Game Lifecycle Flow

1.  **Game End:** The game ends when one or more players reach the winning score.
2.  **Display Results:** The UI displays the final scores and the winner(s).
3.  **Return to Lobby:** The user can choose to return to the lobby.

### API Endpoints & Payloads

This phase does not have any specific API endpoints. The data for this phase is derived from the `round_over` event in the SCORING phase.

### State Management

*   **Global State (React Context - `GameContext`):**
    *   `gameState`: The `GameContainer` uses the `gameState` to determine the winner of the game and pass the relevant data to the `GameOverUI` component.
*   **Local State (`GameOverUI.jsx`):**
    *   The component receives its state from the `GameContainer` via props.

### Event Handling

This phase is triggered by the `round_over` event from the server when the `game_over` flag is true. The `GameContainer` component is responsible for managing the transition to this phase.

### Scene/Component Architecture

*   **`GamePage.jsx`:** The main container for the game.
*   **`GameContainer.jsx`:** A smart container that connects the UI components to the game state.
*   **`GameOverUI.jsx`:** The UI component for the GAME_OVER phase. It displays the final results of the game.

### Data Structures

There are no new data structures for this phase. The data is derived from the `GameState` object.
