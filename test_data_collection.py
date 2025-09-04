import requests
import time
import json

def test_event_exists(room_id, event_type, timeout=10):
    """Poll for event to appear"""
    start = time.time()
    while time.time() - start < timeout:
        resp = requests.get(f"http://localhost:5050/api/debug/events/{room_id}?event_type={event_type}")
        events = resp.json()["events"]
        if events:
            return events[0]
        time.sleep(0.5)
    raise AssertionError(f"Event {event_type} not found within {timeout}s")

def verify_event_fields(event, required_fields):
    """Verify event has all required fields"""
    for field in required_fields:
        if field not in event["payload"]:
            raise AssertionError(f"Missing required field: {field}")
    print(f"✓ Event {event['event_type']} has all required fields")

# Run tests
room_id = "TEST_ROOM"

# Test disconnection event
print("Testing disconnection events...")
disconnect_event = test_event_exists(room_id, "player_disconnected")
verify_event_fields(disconnect_event, ["player_name", "timestamp", "was_bot", "grace_period_seconds", "game_context"])

# Test bot takeover
print("Waiting 6 seconds for bot takeover...")
time.sleep(6)
takeover_event = test_event_exists(room_id, "bot_takeover_activated")
verify_event_fields(takeover_event, ["activation_time", "pre_state", "reason"])

print("All data collection tests passed!")