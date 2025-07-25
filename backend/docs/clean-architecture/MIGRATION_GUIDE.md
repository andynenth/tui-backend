# Clean Architecture Migration Guide

## Overview

This guide provides step-by-step instructions for migrating from the legacy WebSocket-based architecture to the clean architecture implementation.

## Migration Phases

### Phase 1: Preparation (Current State)
- ✅ Clean architecture implemented alongside legacy code
- ✅ Feature flags control which implementation is used
- ✅ All tests passing
- ✅ Documentation complete

### Phase 2: Shadow Mode Testing
Enable shadow mode to run both implementations:

```python
# In settings
ENABLE_SHADOW_MODE = True
LOG_ADAPTER_CALLS = True
```

This will:
1. Execute both legacy and clean architecture code
2. Compare results
3. Log any discrepancies
4. Always return legacy results to users

### Phase 3: Gradual Rollout
Start enabling clean architecture for specific features:

#### Step 1: Connection Management (Low Risk)
```bash
export FF_USE_CONNECTION_ADAPTERS=true
```
- Handles: ping, client_ready, sync_state
- Low risk as these are stateless operations

#### Step 2: Room Management (Medium Risk)
```bash
export FF_USE_ROOM_ADAPTERS=true
```
- Handles: create_room, join_room, leave_room
- Test thoroughly with concurrent operations

#### Step 3: Game Operations (High Risk)
```bash
export FF_USE_GAME_ADAPTERS=true
```
- Handles: start_game, declare, play
- Critical path - extensive testing required

### Phase 4: Full Migration
Once all components are validated:
```bash
export FF_USE_CLEAN_ARCHITECTURE=true
```

## Migration Checklist

### Pre-Migration
- [ ] Review all feature flags are set to false
- [ ] Ensure monitoring is in place
- [ ] Have rollback plan ready
- [ ] Notify team of migration schedule

### During Migration
- [ ] Enable shadow mode
- [ ] Monitor logs for discrepancies
- [ ] Run load tests
- [ ] Verify no performance degradation
- [ ] Check memory usage

### Post-Migration
- [ ] Remove legacy code
- [ ] Update documentation
- [ ] Clean up feature flags
- [ ] Celebrate! 🎉

## Code Migration Examples

### Example 1: Migrating a WebSocket Handler

**Before (Legacy):**
```python
@sio.on('create_room')
async def handle_create_room(sid, data):
    player_name = data.get('player_name')
    room = room_manager.create_room(player_name, sid)
    
    await sio.emit('room_created', {
        'room_id': room.room_id,
        'room_code': room.room_code
    }, to=sid)
    
    return {'success': True, 'room_id': room.room_id}
```

**After (Clean Architecture):**
```python
@sio.on('create_room')
async def handle_create_room(sid, data):
    if feature_flags.is_enabled(FeatureFlags.USE_ROOM_ADAPTERS):
        return await adapter.handle_event(
            'create_room',
            data,
            {'player_id': sid}
        )
    else:
        # Legacy implementation
        return await legacy_create_room(sid, data)
```

### Example 2: Migrating Business Logic

**Before (Mixed Concerns):**
```python
class RoomManager:
    def join_room(self, room_code, player_name, player_id):
        room = self.get_room_by_code(room_code)
        if not room:
            raise ValueError("Room not found")
        
        if len(room.players) >= room.max_players:
            raise ValueError("Room is full")
        
        player = Player(player_id, player_name)
        room.players.append(player)
        
        # Broadcast to room
        asyncio.create_task(
            broadcast(room.room_id, 'player_joined', {
                'player': player.to_dict()
            })
        )
        
        return room
```

**After (Separated Concerns):**
```python
# Domain Layer
class Room(Entity):
    def add_player(self, player: Player) -> None:
        if self.is_full:
            raise DomainException("Room is full")
        
        self._players.append(player)
        self._events.append(
            PlayerJoinedRoom(
                room_id=self.room_id.value,
                player_id=player.player_id.value,
                player_name=player.name
            )
        )

# Application Layer
class JoinRoomUseCase:
    async def execute(self, request: JoinRoomRequest) -> JoinRoomResponse:
        async with self._uow:
            room = await self._uow.rooms.get_by_code(request.room_code)
            if not room:
                return JoinRoomResponse(
                    success=False,
                    error="Room not found"
                )
            
            player = Player(
                PlayerId(request.player_id),
                request.player_name
            )
            
            try:
                room.add_player(player)
                await self._uow.rooms.update(room)
                await self._uow.commit()
                
                # Publish domain events
                for event in room.collect_events():
                    await self._publisher.publish(event)
                
                return JoinRoomResponse(
                    success=True,
                    room_id=room.room_id.value
                )
            except DomainException as e:
                return JoinRoomResponse(
                    success=False,
                    error=str(e)
                )
```

## Testing During Migration

### 1. Shadow Mode Validation
```python
# In shadow mode, both implementations run
async def validate_shadow_mode():
    # Create room with legacy
    legacy_response = await legacy_create_room(data)
    
    # Create room with clean arch
    clean_response = await clean_create_room(data)
    
    # Compare results
    assert legacy_response['room_code'] == clean_response['room_code']
    assert legacy_response['success'] == clean_response['success']
```

### 2. Load Testing
```bash
# Run load tests against both implementations
python -m pytest tests/load/test_clean_architecture_load.py
python -m pytest tests/load/test_legacy_load.py

# Compare results
python scripts/compare_load_test_results.py
```

### 3. Integration Testing
```python
# Test that both systems can coexist
async def test_mixed_mode():
    # Create room with legacy
    room_id = await create_room_legacy()
    
    # Join with clean architecture
    await join_room_clean_arch(room_id)
    
    # Verify state is consistent
    assert room_has_player(room_id, player_id)
```

## Rollback Procedures

If issues arise during migration:

### Immediate Rollback
```bash
# Disable all clean architecture flags
export FF_USE_CLEAN_ARCHITECTURE=false
export FF_USE_CONNECTION_ADAPTERS=false
export FF_USE_ROOM_ADAPTERS=false
export FF_USE_GAME_ADAPTERS=false

# Restart services
./restart_services.sh
```

### Partial Rollback
```python
# Disable specific feature
feature_flags.override(FeatureFlags.USE_GAME_ADAPTERS, False)

# Keep other features enabled
# This allows fixing issues without full rollback
```

## Monitoring

### Key Metrics to Watch

1. **Performance Metrics**
   - Response time percentiles (p50, p95, p99)
   - Database query times
   - Memory usage
   - CPU utilization

2. **Business Metrics**
   - Room creation success rate
   - Game completion rate
   - Player connection stability
   - Error rates by type

3. **Technical Metrics**
   - Event publishing lag
   - Transaction rollback rate
   - Feature flag evaluation time

### Alert Thresholds
```yaml
alerts:
  - name: clean_arch_error_rate
    condition: error_rate > 0.01  # 1% error rate
    action: page_oncall
    
  - name: performance_degradation
    condition: p95_response_time > 200ms
    action: notify_team
    
  - name: memory_leak
    condition: memory_growth > 10% per hour
    action: investigate_and_rollback
```

## Common Issues and Solutions

### Issue 1: Import Errors
**Symptom**: `ImportError: cannot import name 'UseCase'`

**Solution**:
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH="${PYTHONPATH}:/path/to/backend"
```

### Issue 2: Transaction Failures
**Symptom**: `RuntimeError: Transaction already in progress`

**Solution**:
```python
# Don't nest unit of work contexts
# Bad
async with uow:
    async with uow:  # Error!
        pass

# Good
async with uow:
    # Do work
    await uow.commit()
```

### Issue 3: Event Publishing Delays
**Symptom**: Events arrive late or out of order

**Solution**:
```python
# Ensure events are published after commit
async with uow:
    # Make changes
    await uow.commit()
    
# Then publish events
for event in domain_object.collect_events():
    await publisher.publish(event)
```

## Support and Resources

- **Documentation**: `/docs/clean-architecture/`
- **Examples**: `/examples/clean-architecture/`
- **Tests**: `/tests/test_infrastructure/`
- **Support Channel**: #clean-architecture-migration

## Timeline

### Week 1-2: Shadow Mode
- Enable shadow mode in staging
- Monitor and fix discrepancies
- Load test both implementations

### Week 3-4: Gradual Rollout
- Enable connection adapters (10% → 50% → 100%)
- Enable room adapters (10% → 50% → 100%)
- Monitor metrics and user feedback

### Week 5-6: Game Operations
- Enable game adapters in staging
- Extensive testing with QA team
- Gradual production rollout

### Week 7-8: Cleanup
- Remove legacy code
- Update all documentation
- Knowledge sharing sessions

## Success Criteria

Migration is considered successful when:
- ✅ All feature flags enabled in production
- ✅ No increase in error rates
- ✅ No performance degradation
- ✅ All tests passing
- ✅ Team trained on new architecture
- ✅ Legacy code removed