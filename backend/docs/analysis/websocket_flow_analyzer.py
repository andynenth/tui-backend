#!/usr/bin/env python3
"""
WebSocket Flow Analyzer - Traces actual WebSocket message flows
Analyzes ws.py to extract exact message handling and broadcasting patterns
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

@dataclass
class WSMessage:
    """WebSocket message definition"""
    action: str
    handler_code: str
    broadcasts: List[Tuple[str, str]]  # (event, condition)
    state_changes: List[str]
    validations: List[str]
    
@dataclass
class FrontendHandler:
    """Frontend event handler"""
    component: str
    event: str
    sends: List[str]
    receives: List[str]

class WebSocketFlowAnalyzer:
    def __init__(self):
        self.backend_path = Path(".")
        self.frontend_path = Path("../frontend")
        
        # Analysis results
        self.ws_messages: Dict[str, WSMessage] = {}
        self.frontend_handlers: List[FrontendHandler] = []
        self.message_flows: List[Tuple[str, str, str]] = []  # (source, event, target)
        
    def analyze(self):
        """Run complete WebSocket flow analysis"""
        print("🔍 Analyzing WebSocket message flows...")
        
        # Analyze backend WebSocket handler
        self.analyze_ws_handler()
        
        # Analyze frontend WebSocket usage
        self.analyze_frontend_ws()
        
        # Trace message flows
        self.trace_message_flows()
        
        # Generate flow diagrams
        self.generate_flow_diagrams()
        
    def analyze_ws_handler(self):
        """Deep analysis of ws.py"""
        ws_file = self.backend_path / "api" / "routes" / "ws.py"
        if not ws_file.exists():
            print(f"  ⚠️  ws.py not found at {ws_file}")
            return
            
        with open(ws_file, 'r') as f:
            content = f.read()
            
        # Split into message handlers
        # Look for action/event handling patterns
        action_blocks = re.split(r'if\s+(?:action|data\.get\(["\']action["\']\)|message\[["\']action["\']\])\s*==', content)
        
        for block in action_blocks[1:]:  # Skip first block (before any if)
            # Extract action name
            action_match = re.match(r'\s*["\'](\w+)["\']', block)
            if not action_match:
                continue
                
            action = action_match.group(1)
            
            # Extract broadcasts from this block
            broadcasts = []
            
            # Pattern 1: await broadcast(room_id, "event", data)
            broadcast_calls = re.findall(
                r'await\s+broadcast\([^,]+,\s*["\'](\w+)["\'],\s*([^)]+)\)',
                block
            )
            for event, data in broadcast_calls:
                broadcasts.append((event, "always"))
                
            # Pattern 2: broadcast_custom_event
            custom_broadcasts = re.findall(
                r'broadcast_custom_event\([^,]+,\s*["\'](\w+)["\']',
                block
            )
            for event in custom_broadcasts:
                broadcasts.append((event, "custom"))
                
            # Pattern 3: Conditional broadcasts
            if_broadcasts = re.findall(
                r'if\s+([^:]+):\s*\n\s*await\s+broadcast\([^,]+,\s*["\'](\w+)["\']',
                block
            )
            for condition, event in if_broadcasts:
                broadcasts.append((event, f"if {condition.strip()}"))
                
            # Extract state changes
            state_changes = []
            
            # update_phase_data calls
            phase_updates = re.findall(r'update_phase_data\(([^)]+)\)', block)
            state_changes.extend(phase_updates[:3])
            
            # Direct state modifications
            state_mods = re.findall(r'(room\.\w+\s*=\s*[^;]+)', block)
            state_changes.extend(state_mods[:3])
            
            # Extract validations
            validations = []
            validation_patterns = [
                r'if\s+not\s+([^:]+):',
                r'raise\s+\w+Error\(["\']([^"\']+)["\']',
                r'return\s+.*["\']error["\'].*["\']([^"\']+)["\']'
            ]
            for pattern in validation_patterns:
                validations.extend(re.findall(pattern, block)[:2])
                
            self.ws_messages[action] = WSMessage(
                action=action,
                handler_code=block[:500],  # Store first 500 chars
                broadcasts=broadcasts,
                state_changes=state_changes,
                validations=validations
            )
            
        print(f"  Found {len(self.ws_messages)} WebSocket message handlers")
        
    def analyze_frontend_ws(self):
        """Analyze frontend WebSocket usage"""
        # Find NetworkService
        network_files = []
        
        # Check various possible locations
        possible_paths = [
            self.frontend_path / "src" / "services" / "NetworkService.js",
            self.frontend_path / "src" / "services" / "networkService.js",
            self.frontend_path / "network" / "NetworkService.js",
            self.frontend_path / "src" / "network" / "NetworkService.js"
        ]
        
        for path in possible_paths:
            if path.exists():
                network_files.append(path)
                
        # Also scan all component files for WebSocket usage
        if self.frontend_path.exists():
            component_files = list((self.frontend_path / "src").glob("**/*.jsx"))
            component_files.extend(list((self.frontend_path / "src").glob("**/*.js")))
            
            for file_path in component_files:
                if 'node_modules' in str(file_path) or 'test' in str(file_path).lower():
                    continue
                    
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        
                    # Find WebSocket sends
                    sends = []
                    send_patterns = [
                        r'networkService\.send\(["\'](\w+)["\']',
                        r'ws\.send\(.*?["\']action["\']\s*:\s*["\'](\w+)["\']',
                        r'socket\.emit\(["\'](\w+)["\']'
                    ]
                    for pattern in send_patterns:
                        sends.extend(re.findall(pattern, content))
                        
                    # Find WebSocket receives
                    receives = []
                    receive_patterns = [
                        r'on\(["\'](\w+)["\']',
                        r'addEventListener\(["\'](\w+)["\']',
                        r'case\s+["\'](\w+)["\']\s*:'
                    ]
                    for pattern in receive_patterns:
                        receives.extend(re.findall(pattern, content))
                        
                    if sends or receives:
                        component_name = file_path.stem
                        self.frontend_handlers.append(FrontendHandler(
                            component=component_name,
                            event="websocket",
                            sends=list(set(sends)),
                            receives=list(set(receives))
                        ))
                        
                except Exception as e:
                    pass
                    
        print(f"  Found {len(self.frontend_handlers)} frontend WebSocket handlers")
        
    def trace_message_flows(self):
        """Trace complete message flows"""
        # Frontend -> Backend flows
        for handler in self.frontend_handlers:
            for send_event in handler.sends:
                if send_event in self.ws_messages:
                    self.message_flows.append((
                        f"FE:{handler.component}",
                        send_event,
                        "Backend"
                    ))
                    
                    # Backend -> Frontend broadcasts
                    ws_msg = self.ws_messages[send_event]
                    for broadcast_event, condition in ws_msg.broadcasts:
                        self.message_flows.append((
                            "Backend",
                            broadcast_event,
                            f"FE:All"
                        ))
                        
        print(f"  Traced {len(self.message_flows)} message flows")
        
    def generate_flow_diagrams(self):
        """Generate comprehensive flow diagrams"""
        output = []
        
        # 1. WebSocket Message Flow Overview
        output.append(("WebSocket Message Flow", self._gen_message_flow()))
        
        # 2. Event Handler Map
        output.append(("Event Handler Map", self._gen_handler_map()))
        
        # 3. Broadcast Flow
        output.append(("Broadcast Flow", self._gen_broadcast_flow()))
        
        # 4. Complete Interaction Sequence
        output.append(("Complete Game Interaction", self._gen_interaction_sequence()))
        
        # 5. State Change Flow
        output.append(("State Change Flow", self._gen_state_flow()))
        
        # Save diagrams
        with open("websocket_flows.md", 'w') as f:
            f.write("# WebSocket Message Flow Analysis\n\n")
            f.write("## Summary\n\n")
            f.write(f"- **Backend Handlers**: {len(self.ws_messages)}\n")
            f.write(f"- **Frontend Components**: {len(self.frontend_handlers)}\n")
            f.write(f"- **Message Flows**: {len(self.message_flows)}\n\n")
            
            # Add handler details
            f.write("## Backend WebSocket Handlers\n\n")
            for action, msg in self.ws_messages.items():
                f.write(f"### `{action}` Handler\n\n")
                f.write(f"**Broadcasts:**\n")
                for event, condition in msg.broadcasts:
                    f.write(f"- `{event}` ({condition})\n")
                f.write(f"\n**State Changes:** {len(msg.state_changes)}\n")
                f.write(f"**Validations:** {len(msg.validations)}\n\n")
                
            # Add diagrams
            f.write("## Flow Diagrams\n\n")
            for title, diagram in output:
                f.write(f"### {title}\n\n")
                f.write("```mermaid\n")
                f.write(diagram)
                f.write("\n```\n\n")
                
        print(f"\n✅ WebSocket flow analysis complete! Results saved to: websocket_flows.md")
        
    def _gen_message_flow(self) -> str:
        """Generate message flow diagram"""
        diagram = "graph TB\n"
        diagram += "    subgraph Frontend\n"
        
        # Add frontend components that send messages
        senders = set()
        for handler in self.frontend_handlers[:10]:
            if handler.sends:
                safe_name = handler.component.replace('-', '_')
                diagram += f"        {safe_name}[{handler.component}]\n"
                senders.add(safe_name)
                
        diagram += "    end\n\n"
        diagram += "    subgraph Backend\n"
        diagram += "        WSHandler[WebSocket Handler]\n"
        
        # Add backend handlers
        for action in list(self.ws_messages.keys())[:10]:
            safe_action = action.replace('-', '_')
            diagram += f"        {safe_action}[{action} Handler]\n"
            
        diagram += "    end\n\n"
        
        # Add message flows
        for handler in self.frontend_handlers[:10]:
            if handler.sends:
                safe_comp = handler.component.replace('-', '_')
                for event in handler.sends[:3]:
                    if event in self.ws_messages:
                        safe_event = event.replace('-', '_')
                        diagram += f"    {safe_comp} -->|{event}| {safe_event}\n"
                        
                        # Add broadcasts
                        msg = self.ws_messages[event]
                        for broadcast, _ in msg.broadcasts[:2]:
                            diagram += f"    {safe_event} -.->|{broadcast}| Frontend\n"
                            
        return diagram
        
    def _gen_handler_map(self) -> str:
        """Generate handler mapping"""
        diagram = "graph LR\n"
        
        # Group handlers by type
        diagram += "    subgraph \"Frontend Sends\"\n"
        all_sends = set()
        for handler in self.frontend_handlers:
            all_sends.update(handler.sends)
        for event in list(all_sends)[:10]:
            diagram += f"        FE_{event}[{event}]\n"
        diagram += "    end\n\n"
        
        diagram += "    subgraph \"Backend Handles\"\n"
        for action in list(self.ws_messages.keys())[:10]:
            diagram += f"        BE_{action}[{action}]\n"
        diagram += "    end\n\n"
        
        diagram += "    subgraph \"Backend Broadcasts\"\n"
        all_broadcasts = set()
        for msg in self.ws_messages.values():
            for event, _ in msg.broadcasts:
                all_broadcasts.add(event)
        for event in list(all_broadcasts)[:10]:
            diagram += f"        BC_{event}[{event}]\n"
        diagram += "    end\n\n"
        
        # Connect matching events
        for send in all_sends:
            if send in self.ws_messages:
                diagram += f"    FE_{send} --> BE_{send}\n"
                msg = self.ws_messages[send]
                for broadcast, _ in msg.broadcasts[:2]:
                    safe_bc = broadcast.replace('-', '_')
                    if broadcast in all_broadcasts:
                        diagram += f"    BE_{send} --> BC_{broadcast}\n"
                        
        return diagram
        
    def _gen_broadcast_flow(self) -> str:
        """Generate broadcast flow diagram"""
        diagram = "flowchart TB\n"
        
        # Create broadcast map
        broadcast_map = defaultdict(list)
        for action, msg in self.ws_messages.items():
            for event, condition in msg.broadcasts:
                broadcast_map[event].append((action, condition))
                
        diagram += "    subgraph \"Broadcast Events\"\n"
        for event, sources in list(broadcast_map.items())[:10]:
            safe_event = event.replace('-', '_')
            diagram += f"        {safe_event}[{event}]\n"
            
            for source, condition in sources[:3]:
                safe_source = source.replace('-', '_')
                if condition == "always":
                    diagram += f"        {safe_source}_handler[{source}] --> {safe_event}\n"
                else:
                    diagram += f"        {safe_source}_handler[{source}] -.-> |{condition[:20]}| {safe_event}\n"
                    
        diagram += "    end\n"
        
        return diagram
        
    def _gen_interaction_sequence(self) -> str:
        """Generate complete interaction sequence"""
        diagram = "sequenceDiagram\n"
        diagram += "    participant User\n"
        diagram += "    participant Frontend\n"
        diagram += "    participant WebSocket\n"
        diagram += "    participant Backend\n"
        diagram += "    participant StateMachine\n"
        diagram += "    participant Broadcast\n\n"
        
        # Generate sequences for each major action
        sequences = [
            ("create_room", [
                "User->>Frontend: Click Create Room",
                "Frontend->>WebSocket: send('create_room')",
                "WebSocket->>Backend: Handle create_room",
                "Backend->>StateMachine: Initialize game",
                "StateMachine->>Broadcast: room_created",
                "Broadcast->>Frontend: Receive room_created",
                "Frontend->>User: Show room code"
            ]),
            ("join_room", [
                "User->>Frontend: Enter room code",
                "Frontend->>WebSocket: send('join_room')",
                "WebSocket->>Backend: Handle join_room",
                "Backend->>Backend: Validate room",
                "Backend->>StateMachine: Add player",
                "StateMachine->>Broadcast: player_joined",
                "Broadcast->>Frontend: Update players",
                "Frontend->>User: Show game room"
            ]),
            ("start_game", [
                "User->>Frontend: Click Start",
                "Frontend->>WebSocket: send('start_game')",
                "WebSocket->>Backend: Handle start_game",
                "Backend->>StateMachine: Begin game",
                "StateMachine->>StateMachine: Deal cards",
                "StateMachine->>Broadcast: game_started",
                "Broadcast->>Frontend: Show game board",
                "Frontend->>User: Display hand"
            ])
        ]
        
        for action, steps in sequences:
            if action in self.ws_messages:
                diagram += f"    Note over User,Broadcast: {action} Flow\n"
                for step in steps:
                    diagram += f"    {step}\n"
                diagram += "\n"
                
        return diagram
        
    def _gen_state_flow(self) -> str:
        """Generate state change flow"""
        diagram = "graph TD\n"
        
        diagram += "    subgraph \"Actions Triggering State Changes\"\n"
        
        for action, msg in list(self.ws_messages.items())[:10]:
            if msg.state_changes:
                safe_action = action.replace('-', '_')
                diagram += f"        {safe_action}[{action}]\n"
                
                for i, change in enumerate(msg.state_changes[:3]):
                    change_summary = change[:30].replace('\n', ' ')
                    diagram += f"        {safe_action} --> SC{safe_action}{i}[{change_summary}...]\n"
                    
        diagram += "    end\n"
        
        return diagram

def main():
    analyzer = WebSocketFlowAnalyzer()
    analyzer.analyze()
    
    print("\n📊 WebSocket Flow Summary:")
    print(f"   Backend message handlers: {len(analyzer.ws_messages)}")
    print(f"   Frontend components with WS: {len(analyzer.frontend_handlers)}")
    print(f"   Total message flows: {len(analyzer.message_flows)}")
    
    if analyzer.ws_messages:
        print("\n   Backend handlers found:")
        for action in list(analyzer.ws_messages.keys())[:10]:
            msg = analyzer.ws_messages[action]
            print(f"     - {action}: {len(msg.broadcasts)} broadcasts")

if __name__ == "__main__":
    main()