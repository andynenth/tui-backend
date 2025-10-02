# State Machine Event Flow - Automatic Broadcasting System

This diagram illustrates how the Enterprise Architecture ensures automatic synchronization and eliminates manual broadcasting bugs.

```mermaid
sequenceDiagram
    participant User
    participant StateClass as State Class<br/>(e.g., TurnState)
    participant UpdatePhaseData as update_phase_data()
    participant Validation as Validation Layer
    participant StateStore as Phase Data Store
    participant Serializer as JSON Serializer
    participant Broadcast as Broadcast System
    participant Clients as All Connected Clients
    participant AuditTrail as Audit Trail

    User->>StateClass: Performs Action<br/>(e.g., play pieces)

    StateClass->>UpdatePhaseData: await self.update_phase_data({<br/>  'current_player': next_player,<br/>  'turn_number': game.turn_number<br/>}, "Player X played Y pieces")

    Note over UpdatePhaseData: Enterprise Architecture<br/>Single Source of Truth

    UpdatePhaseData->>Validation: Validate updates
    Validation-->>UpdatePhaseData: ✓ Valid

    UpdatePhaseData->>StateStore: Apply updates to phase_data
    StateStore-->>UpdatePhaseData: State updated

    UpdatePhaseData->>UpdatePhaseData: Generate metadata:<br/>- sequence number<br/>- timestamp<br/>- reason

    UpdatePhaseData->>Serializer: Convert to JSON-safe format
    Serializer-->>UpdatePhaseData: Serialized data

    UpdatePhaseData->>Broadcast: Automatic broadcast<br/>"phase_change" event

    Note over Broadcast: No manual broadcast()<br/>calls allowed!

    Broadcast->>Clients: WebSocket event with:<br/>- phase data<br/>- sequence #<br/>- timestamp<br/>- reason

    UpdatePhaseData->>AuditTrail: Store change event
    AuditTrail-->>UpdatePhaseData: Event logged

    UpdatePhaseData-->>StateClass: Success
    StateClass-->>User: Action completed

    Note over User,AuditTrail: Benefits:<br/>🔒 Sync bugs impossible<br/>🔍 Complete debugging<br/>⚡ Optimized performance<br/>🏗️ Single source of truth
```

## Key Points

1. **Single Source of Truth**: All state changes MUST go through `update_phase_data()`
2. **Automatic Broadcasting**: No manual `broadcast()` calls - everything is automatic
3. **Complete Metadata**: Every broadcast includes sequence numbers, timestamps, and reasons
4. **JSON-Safe Serialization**: All data automatically converted for WebSocket transmission
5. **Audit Trail**: Every change is tracked for debugging and analysis

## Code Example

```python
# ✅ CORRECT - Enterprise Pattern
await self.update_phase_data({
    'current_player': next_player,
    'turn_number': game.turn_number,
    'piece_count': len(pieces)
}, "Player moved - automatic broadcasting")

# ❌ WRONG - Manual Pattern (FORBIDDEN)
self.phase_data['current_player'] = next_player  # Bypasses enterprise system
await broadcast(room_id, "state_change", data)   # No automatic features
```
