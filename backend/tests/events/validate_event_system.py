#!/usr/bin/env python3
"""
Validation script for the event system.

This script validates that the event system is correctly integrated
and produces the expected outputs.
"""

import asyncio
import sys
import os
from typing import Dict, Any, List
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from domain.events.base import DomainEvent, EventMetadata
from domain.events.all_events import (
    RoomCreated, PlayerJoinedRoom, GameStarted,
    PiecesPlayed, PhaseChanged, CustomGameEvent
)
from infrastructure.events.in_memory_event_bus import (
    get_event_bus, reset_event_bus
)
from infrastructure.events.event_broadcast_mapper import (
    event_broadcast_mapper
)
from infrastructure.events.integrated_broadcast_handler import (
    get_broadcast_handler, reset_broadcast_handler
)

from api.adapters.adapter_event_config import adapter_event_config
from engine.state_machine.event_config import state_event_config


class EventSystemValidator:
    """Validates the event system functionality."""
    
    def __init__(self):
        self.results = []
        self.broadcast_messages = []
        self.published_events = []
    
    async def validate_all(self):
        """Run all validation checks."""
        print("Event System Validation")
        print("=" * 60)
        print()
        
        # Run validations
        await self.validate_event_bus()
        await self.validate_event_mappings()
        await self.validate_adapter_events()
        await self.validate_state_machine_events()
        await self.validate_broadcast_integration()
        
        # Print summary
        self.print_summary()
    
    async def validate_event_bus(self):
        """Validate basic event bus functionality."""
        print("1. Validating Event Bus...")
        
        reset_event_bus()
        bus = get_event_bus()
        
        # Track events
        received_events = []
        
        async def handler(event: DomainEvent):
            received_events.append(event)
        
        # Subscribe and publish
        bus.subscribe(RoomCreated, handler)
        
        metadata = EventMetadata(user_id="validator")
        event = RoomCreated(
            room_id="test_room",
            host_name="Test Host",
            metadata=metadata
        )
        
        await bus.publish(event)
        
        # Validate
        success = len(received_events) == 1 and received_events[0] == event
        self.results.append({
            "test": "Event Bus Basic Functionality",
            "success": success,
            "details": f"Published 1 event, received {len(received_events)}"
        })
        
        print(f"   ✓ Event publishing and subscription working" if success else "   ✗ Event bus failed")
    
    async def validate_event_mappings(self):
        """Validate event-to-broadcast mappings."""
        print("\n2. Validating Event Mappings...")
        
        # Test a few key mappings
        test_cases = [
            {
                "event": RoomCreated(
                    room_id="room123",
                    host_name="Alice",
                    metadata=EventMetadata()
                ),
                "expected_event": "room_created",
                "expected_target": "response"
            },
            {
                "event": PlayerJoinedRoom(
                    room_id="room123",
                    player_name="Bob",
                    slot=2,
                    metadata=EventMetadata()
                ),
                "expected_event": "room_update",
                "expected_target": "room"
            },
            {
                "event": PhaseChanged(
                    room_id="room123",
                    old_phase="PREPARATION",
                    new_phase="DECLARATION",
                    metadata=EventMetadata()
                ),
                "expected_event": "phase_change",
                "expected_target": "room"
            }
        ]
        
        all_passed = True
        for test in test_cases:
            result = event_broadcast_mapper.map_event(test["event"], {})
            
            if result:
                passed = (
                    result["event_name"] == test["expected_event"] and
                    result["target_type"] == test["expected_target"]
                )
                status = "✓" if passed else "✗"
                print(f"   {status} {type(test['event']).__name__} → {test['expected_event']}")
                all_passed = all_passed and passed
            else:
                print(f"   ✗ {type(test['event']).__name__} → No mapping found")
                all_passed = False
        
        self.results.append({
            "test": "Event-to-Broadcast Mappings",
            "success": all_passed,
            "details": f"Tested {len(test_cases)} mappings"
        })
    
    async def validate_adapter_events(self):
        """Validate adapter event publishing."""
        print("\n3. Validating Adapter Events...")
        
        # Enable event adapters
        original_enabled = adapter_event_config.events_enabled
        adapter_event_config.events_enabled = True
        adapter_event_config.adapter_modes["create_room"] = "event"
        
        try:
            # Reset and track events
            reset_event_bus()
            published = []
            
            async def track_event(event: DomainEvent):
                published.append(event)
            
            bus = get_event_bus()
            bus.subscribe(DomainEvent, track_event)
            
            # Create adapter and test
            from api.adapters.room_adapters_event import CreateRoomAdapterEvent
            adapter = CreateRoomAdapterEvent()
            
            # Mock websocket
            class MockWS:
                player_id = "test_player"
            
            message = {
                "action": "create_room",
                "data": {"player_name": "Test Player"}
            }
            
            response = await adapter.handle(MockWS(), message)
            
            # Validate
            success = (
                len(published) == 1 and
                isinstance(published[0], RoomCreated) and
                response["event"] == "room_created"
            )
            
            self.results.append({
                "test": "Adapter Event Publishing",
                "success": success,
                "details": f"Published {len(published)} events, got response"
            })
            
            print(f"   ✓ Adapters publish events correctly" if success else "   ✗ Adapter events failed")
            
        finally:
            adapter_event_config.events_enabled = original_enabled
    
    async def validate_state_machine_events(self):
        """Validate state machine event integration."""
        print("\n4. Validating State Machine Events...")
        
        # Enable state events
        from engine.state_machine.event_integration import get_state_event_publisher
        publisher = get_state_event_publisher()
        publisher.enable()
        
        try:
            # Track events
            reset_event_bus()
            published = []
            
            async def track_event(event: DomainEvent):
                published.append(event)
            
            bus = get_event_bus()
            bus.subscribe(DomainEvent, track_event)
            
            # Mock state machine
            class MockStateMachine:
                room_id = "test_room"
                _sequence_number = 1
            
            # Simulate phase change
            from engine.state_machine.core import GamePhase
            await publisher.on_phase_data_update(
                MockStateMachine(),
                GamePhase.TURN,
                {"current_player": "Alice"},
                {},
                "Test phase change"
            )
            
            # Validate
            phase_events = [e for e in published if isinstance(e, PhaseChanged)]
            success = len(phase_events) > 0
            
            self.results.append({
                "test": "State Machine Event Publishing",
                "success": success,
                "details": f"Published {len(published)} events on state change"
            })
            
            print(f"   ✓ State machine publishes events" if success else "   ✗ State events failed")
            
        finally:
            publisher.disable()
    
    async def validate_broadcast_integration(self):
        """Validate event-to-broadcast integration."""
        print("\n5. Validating Broadcast Integration...")
        
        # Reset and initialize handler
        reset_broadcast_handler()
        reset_event_bus()
        
        # Track broadcasts
        broadcasts = []
        
        async def mock_broadcast(room_id, event_name, data):
            broadcasts.append({
                "room_id": room_id,
                "event": event_name,
                "data": data
            })
        
        # Initialize broadcast handler
        handler = get_broadcast_handler()
        handler.initialize()
        
        # Publish a game event
        with patch('backend.infrastructure.events.integrated_broadcast_handler.broadcast', mock_broadcast):
            bus = get_event_bus()
            
            metadata = EventMetadata()
            event = GameStarted(
                room_id="room123",
                round_number=1,
                starter_player="Alice",
                metadata=metadata
            )
            
            await bus.publish(event)
            
            # Give handler time to process
            await asyncio.sleep(0.1)
        
        # Validate
        success = len(broadcasts) > 0 and any(b["event"] == "game_started" for b in broadcasts)
        
        self.results.append({
            "test": "Event-to-Broadcast Integration",
            "success": success,
            "details": f"Generated {len(broadcasts)} broadcasts from events"
        })
        
        print(f"   ✓ Events trigger broadcasts" if success else "   ✗ Broadcast integration failed")
    
    def print_summary(self):
        """Print validation summary."""
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in self.results if r["success"])
        total = len(self.results)
        
        for result in self.results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"{status} - {result['test']}")
            print(f"        {result['details']}")
        
        print(f"\nTotal: {passed}/{total} passed")
        
        if passed == total:
            print("\n🎉 All validations passed! Event system is working correctly.")
            return 0
        else:
            print(f"\n⚠️  {total - passed} validations failed. Please check the event system.")
            return 1


async def main():
    """Run the validation."""
    validator = EventSystemValidator()
    return await validator.validate_all()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)