# Frontend Documentation

This document provides a detailed overview of the frontend system for the Liap Tui project.

## Table of Contents

*   [Main Application Component](#main-application-component)
*   [Game Service](#game-service)
*   [Network Service](#network-service)
*   [Game State Hook](#game-state-hook)

## Main Application Component

The main entry point for the frontend application is `frontend/src/App.jsx`. This file is responsible for:

*   Setting up the main application component.
*   Initializing the React router.
*   Wrapping the application in an `ErrorBoundary` and `AppProvider`.
*   Initializing the frontend services.

### Key Components in `App.jsx`

*   **`App`**: The root component of the application.
*   **`AppWithServices`**: A component that ensures the frontend services are initialized before rendering the rest of the application.
*   **`AppRouter`**: Defines the application's routes, including protected routes that require a player name and/or room ID.
*   **`GameRoute`**: A wrapper component that provides the `GameContext` to the game page.

## Game Service

The `GameService` class, located in `frontend/src/services/GameService.ts`, is the single source of truth for the game's state on the frontend. It is a singleton class that:

*   Manages the game state in an immutable way.
*   Listens for events from the `NetworkService` and updates the state accordingly.
*   Provides an observable interface for React components to subscribe to state changes.
*   Dispatches player actions to the backend.

### Key Functions in `GameService.ts`

*   **`getState()`**: Returns the current game state.
*   **`joinRoom(...)`**: Connects the player to a game room.
*   **`leaveRoom()`**: Disconnects the player from the current room.
*   **`addListener(...)`**: Allows components to subscribe to state changes.
*   **`sendAction(...)`**: Sends a player action to the backend through the `NetworkService`.

## Network Service

The `NetworkService` class, located in `frontend/src/services/NetworkService.ts`, is responsible for managing the WebSocket connection to the backend. It is a singleton class that provides:

*   A robust WebSocket connection manager.
*   Automatic reconnection with exponential backoff.
*   A message queue for offline message sending.
*   A heartbeat system to ensure the connection is alive.

### Key Functions in `NetworkService.ts`

*   **`connectToRoom(...)`**: Establishes a WebSocket connection to a specific game room.
*   **`disconnectFromRoom(...)`**: Closes the WebSocket connection.
*   **`send(...)`**: Sends a message to the backend.
*   **`getConnectionStatus(...)`**: Returns the current status of the WebSocket connection.

## Game State Hook

The `useGameState` hook, defined in `frontend/src/hooks/useGameState.ts`, is the primary way for React components to access the game state. It provides:

*   A simple interface for components to get the latest game state.
*   Optimized re-rendering by only updating components when the state they care about changes.
*   Type safety through TypeScript interfaces.

### Key Functions in `useGameState.ts`

*   **`useGameState()`**: The main hook that returns the entire game state.
*   **`useGameStateSlice(...)`**: A more advanced hook that allows components to select a specific slice of the state, further optimizing re-renders.
*   **`useConnectionState()`**: A specialized hook that returns only the connection-related state.
*   **`usePlayerState()`**: A specialized hook that returns only the state relevant to the current player.