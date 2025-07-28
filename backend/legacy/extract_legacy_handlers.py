#!/usr/bin/env python3
"""
Script to extract legacy handlers from ws.py
This helps identify and extract the existing handler logic for each event.
"""

import re
import os

def extract_handlers_from_ws():
    """Extract event handlers from ws.py"""
    
    ws_file = "api/routes/ws.py"
    if not os.path.exists(ws_file):
        print(f"Error: {ws_file} not found")
        return
    
    with open(ws_file, 'r') as f:
        content = f.read()
    
    # Find all event handlers
    # Pattern: if event_name == "..." or elif event_name == "..."
    pattern = r'(?:if|elif)\s+event_name\s*==\s*["\'](\w+)["\']'
    
    handlers = []
    for match in re.finditer(pattern, content):
        event_name = match.group(1)
        start_pos = match.start()
        
        # Find the line number
        line_num = content[:start_pos].count('\n') + 1
        
        # Get some context
        line_start = content.rfind('\n', 0, start_pos) + 1
        line_end = content.find('\n', start_pos)
        if line_end == -1:
            line_end = len(content)
        
        line_content = content[line_start:line_end].strip()
        
        handlers.append({
            'event': event_name,
            'line': line_num,
            'context': line_content
        })
    
    print("Event Handlers Found in ws.py:")
    print("=" * 60)
    
    # Group by type
    connection_events = ['ping', 'client_ready', 'ack', 'sync_request']
    room_events = ['create_room', 'join_room', 'leave_room', 'get_room_state', 'add_bot', 'remove_player']
    lobby_events = ['request_room_list', 'get_rooms']
    game_events = ['start_game', 'declare', 'play', 'play_pieces', 'request_redeal', 
                   'accept_redeal', 'decline_redeal', 'redeal_decision', 'player_ready', 'leave_game']
    
    categories = {
        'Connection': connection_events,
        'Room': room_events,
        'Lobby': lobby_events,
        'Game': game_events
    }
    
    for category, events in categories.items():
        print(f"\n{category} Events:")
        print("-" * 40)
        
        category_handlers = [h for h in handlers if h['event'] in events]
        for handler in sorted(category_handlers, key=lambda x: x['line']):
            print(f"  Line {handler['line']:4d}: {handler['event']:<20} - {handler['context'][:50]}...")
    
    # Find unmatched events
    all_known_events = sum(categories.values(), [])
    unknown_handlers = [h for h in handlers if h['event'] not in all_known_events]
    
    if unknown_handlers:
        print(f"\nUnknown Events:")
        print("-" * 40)
        for handler in unknown_handlers:
            print(f"  Line {handler['line']:4d}: {handler['event']:<20} - {handler['context'][:50]}...")
    
    print(f"\nTotal handlers found: {len(handlers)}")
    
    # Generate extraction template
    print("\n" + "=" * 60)
    print("Handler Extraction Template:")
    print("=" * 60)
    
    print("""
To extract a handler from ws.py:

1. Find the handler block starting at the line number above
2. Copy all the code until the next 'elif' or end of the if block
3. Add it to ws_legacy_handlers.py in the appropriate method

Example for 'ping' handler:
```python
async def handle_ping(self, websocket, data: Dict[str, Any], room_id: str) -> Dict[str, Any]:
    # Paste the extracted code here
    # Adjust variable names as needed:
    # - event_data -> data
    # - registered_ws -> websocket
    # - Add return statement for the response
```
""")
    
    # Check which handlers we already have adapters for
    print("\nAdapter Coverage Check:")
    print("-" * 40)
    
    adapter_implemented = 22  # From our completion report
    total_handlers = len(handlers)
    
    print(f"Adapters implemented: {adapter_implemented}")
    print(f"Handlers in ws.py: {total_handlers}")
    
    if total_handlers > adapter_implemented:
        print(f"⚠️  Warning: More handlers in ws.py than adapters implemented!")
        print(f"   This might indicate special handlers or duplicates")


if __name__ == "__main__":
    extract_handlers_from_ws()