# Lock Acquisition Flow - Alternative Visualizations

## Option 1: Visual Lock States (Recommended)

Shows the lock lifecycle with clear visual states.

```mermaid
graph TD
    subgraph "Lock Available"
        LA[🔓 Lock Free]
    end

    LA --> R1[Request 1 Arrives]
    R1 --> A1[🔒 Lock Acquired by Request 1]

    subgraph "Lock Held"
        A1 --> CS[Critical Section<br/>Operations in Progress]
        CS --> |Success| RS[Release Lock]
        CS --> |Error| RB[Rollback → Release Lock]
    end

    subgraph "Concurrent Request"
        R2[Request 2 Arrives]
        R2 --> W2[⏳ Request 2 Waits]
    end

    A1 -.-> R2

    RS --> LA2[🔓 Lock Free Again]
    RB --> LA2
    W2 --> |Lock Available| A2[🔒 Lock Acquired by Request 2]
    LA2 --> A2

    style LA fill:#90EE90
    style LA2 fill:#90EE90
    style A1 fill:#FFB6C1
    style A2 fill:#FFB6C1
    style W2 fill:#FFE4B5
    style RB fill:#FF6B6B
```

## Option 2: Timeline View

Shows how locks prevent race conditions over time.

```mermaid
gantt
    title Concurrent Request Timeline
    dateFormat X
    axisFormat %s

    section Request 1
    Acquire Lock          :done, r1lock, 0, 1
    Critical Operations   :active, r1ops, 1, 4
    Release Lock         :done, r1rel, 5, 1

    section Lock Status
    Available            :done, avail1, 0, 0
    Locked by R1         :crit, locked1, 0, 5
    Available Again      :done, avail2, 5, 5

    section Request 2
    Wait for Lock        :crit, r2wait, 1, 4
    Acquire Lock         :done, r2lock, 5, 1
    Operations           :active, r2ops, 6, 3
```

## Option 3: State Machine View

Shows lock states and transitions.

```mermaid
stateDiagram-v2
    [*] --> Available: Initialize

    Available --> Locked: acquire()
    Locked --> Processing: Enter Critical Section

    Processing --> Releasing: Operations Complete
    Processing --> Rollback: Exception Raised

    Rollback --> Releasing: Cleanup Done
    Releasing --> Available: release()

    state Processing {
        Read: Read State
        Modify: Modify Data
        Write: Write Changes
        Log: Log Operations
    }

    state Rollback {
        Undo: Undo Changes
        Restore: Restore State
        LogError: Log Error
    }
```

## Option 4: Simplified Flow

Focus on the core concept of mutual exclusion.

```mermaid
flowchart TB
    Start([Two Requests Arrive])

    Start --> Check{Lock Available?}

    Check -->|Yes| Acquire[Request 1: Acquire Lock]
    Check -->|No| Wait[Request 2: Wait in Queue]

    Acquire --> Execute[Execute Critical Section]

    Execute --> Success{Success?}

    Success -->|Yes| Release1[Release Lock]
    Success -->|No| Rollback[Rollback Changes]

    Rollback --> Release1

    Release1 --> Next[Next Request Gets Lock]
    Wait --> Next

    style Acquire fill:#90EE90
    style Wait fill:#FFE4B5
    style Rollback fill:#FF6B6B
```

## Option 5: Lock Types Overview

Shows all lock types in the system at a glance.

```mermaid
graph TB
    subgraph "AsyncRoomManager"
        ML[manager_lock<br/>🔒 Protects rooms dict]
        RCL[room_creation_lock<br/>🔒 Unique ID generation]
    end

    subgraph "ActionQueue"
        PL[processing_lock<br/>🔒 Sequential processing]
    end

    subgraph "Protected Resources"
        RD[rooms: Dict<br/>💾 Active rooms]
        ID[ID Generator<br/>🔢 Unique IDs]
        AQ[Action Queue<br/>📋 Pending actions]
    end

    ML --> RD
    RCL --> ID
    PL --> AQ

    style ML fill:#FFB6C1
    style RCL fill:#87CEEB
    style PL fill:#90EE90
```

## Recommendation

I recommend **Option 1 (Visual Lock States)** as the primary diagram because:
- Clear visual representation of lock states (🔓 free, 🔒 locked, ⏳ waiting)
- Shows both success and error paths
- Easy to understand the mutual exclusion concept
- Demonstrates how concurrent requests are handled

You could supplement with **Option 5** to show all the different lock types in the system.
