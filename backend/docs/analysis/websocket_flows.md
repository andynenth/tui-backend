# WebSocket Message Flow Analysis

## Summary

- **Backend Handlers**: 0
- **Frontend Components**: 18
- **Message Flows**: 0

## Backend WebSocket Handlers

## Flow Diagrams

### WebSocket Message Flow

```mermaid
graph TB
    subgraph Frontend
    end

    subgraph Backend
        WSHandler[WebSocket Handler]
    end


```

### Event Handler Map

```mermaid
graph LR
    subgraph "Frontend Sends"
        FE_lobby[lobby]
    end

    subgraph "Backend Handles"
    end

    subgraph "Backend Broadcasts"
    end


```

### Broadcast Flow

```mermaid
flowchart TB
    subgraph "Broadcast Events"
    end

```

### Complete Game Interaction

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant WebSocket
    participant Backend
    participant StateMachine
    participant Broadcast


```

### State Change Flow

```mermaid
graph TD
    subgraph "Actions Triggering State Changes"
    end

```

