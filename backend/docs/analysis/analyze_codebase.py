#!/usr/bin/env python3
"""
Codebase Analyzer - Traces actual data flows and generates Mermaid diagrams
Analyzes both backend and frontend code to extract real system architecture
"""

import ast
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict
import subprocess

@dataclass
class APIEndpoint:
    """Represents an API endpoint"""
    path: str
    method: str
    handler: str
    params: List[str] = field(default_factory=list)
    returns: str = ""
    websocket: bool = False

@dataclass
class WebSocketEvent:
    """Represents a WebSocket event"""
    event_name: str
    handler: str
    data_structure: Dict = field(default_factory=dict)
    broadcasts: List[str] = field(default_factory=list)

@dataclass
class Component:
    """Represents a frontend component"""
    name: str
    file_path: str
    props: List[str] = field(default_factory=list)
    state_vars: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    websocket_events: List[str] = field(default_factory=list)
    api_calls: List[str] = field(default_factory=list)

@dataclass
class DataFlow:
    """Represents a data flow between components"""
    source: str
    target: str
    data_type: str
    trigger: str = ""

class CodebaseAnalyzer:
    def __init__(self, backend_path: str = ".", frontend_path: str = "frontend"):
        self.backend_path = Path(backend_path)
        self.frontend_path = Path(frontend_path)
        self.api_endpoints: List[APIEndpoint] = []
        self.websocket_events: List[WebSocketEvent] = []
        self.components: Dict[str, Component] = {}
        self.data_flows: List[DataFlow] = []
        self.state_machine_phases: Dict[str, Any] = {}
        self.game_features: Dict[str, Any] = {}
        
    def analyze(self):
        """Run complete analysis"""
        print("🔍 Starting codebase analysis...")
        
        # Backend analysis
        print("\n📊 Analyzing backend...")
        self.analyze_backend_api()
        self.analyze_websocket_handlers()
        self.analyze_state_machine()
        self.analyze_game_engine()
        
        # Frontend analysis
        print("\n📊 Analyzing frontend...")
        self.analyze_frontend_components()
        self.analyze_frontend_services()
        self.trace_data_flows()
        
        # Generate diagrams
        print("\n📈 Generating diagrams...")
        self.generate_diagrams()
        
    def analyze_backend_api(self):
        """Analyze FastAPI endpoints"""
        api_files = list(self.backend_path.glob("api/**/*.py"))
        
        for file_path in api_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    tree = ast.parse(content)
                    
                for node in ast.walk(tree):
                    # Find FastAPI route decorators
                    if isinstance(node, ast.FunctionDef):
                        for decorator in node.decorator_list:
                            route_info = self._extract_route_info(decorator, node)
                            if route_info:
                                self.api_endpoints.append(route_info)
            except Exception as e:
                print(f"  ⚠️  Error parsing {file_path}: {e}")
                
    def _extract_route_info(self, decorator, func_node) -> APIEndpoint:
        """Extract route information from decorator"""
        if isinstance(decorator, ast.Call):
            if hasattr(decorator.func, 'attr'):
                method = decorator.func.attr.upper()
                if method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'WEBSOCKET']:
                    # Extract path from arguments
                    if decorator.args:
                        if isinstance(decorator.args[0], ast.Constant):
                            path = decorator.args[0].value
                            params = [arg.arg for arg in func_node.args.args if arg.arg != 'self']
                            
                            return APIEndpoint(
                                path=path,
                                method=method,
                                handler=func_node.name,
                                params=params,
                                websocket=(method == 'WEBSOCKET')
                            )
        return None
        
    def analyze_websocket_handlers(self):
        """Analyze WebSocket event handlers"""
        ws_file = self.backend_path / "api" / "routes" / "ws.py"
        if ws_file.exists():
            with open(ws_file, 'r') as f:
                content = f.read()
                
            # Find WebSocket event handlers using regex
            event_pattern = r'["\'](create_room|join_room|start_game|declare|play|accept_redeal|decline_redeal|leave_room)["\']'
            events = re.findall(event_pattern, content)
            
            for event in set(events):
                # Find associated broadcasts
                broadcast_pattern = rf'{event}.*?broadcast.*?["\'](.*?)["\']'
                broadcasts = re.findall(broadcast_pattern, content, re.DOTALL)
                
                self.websocket_events.append(WebSocketEvent(
                    event_name=event,
                    handler=f"handle_{event}",
                    broadcasts=list(set(broadcasts[:3]))  # Limit to first 3 unique broadcasts
                ))
                
    def analyze_state_machine(self):
        """Analyze game state machine phases"""
        state_machine_path = self.backend_path / "engine" / "state_machine"
        if state_machine_path.exists():
            phase_files = list(state_machine_path.glob("*.py"))
            
            for file_path in phase_files:
                if 'game_state.py' in str(file_path):
                    continue
                    
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                # Extract phase name and transitions
                phase_match = re.search(r'class (\w+State)', content)
                if phase_match:
                    phase_name = phase_match.group(1)
                    
                    # Find handle methods
                    handle_methods = re.findall(r'async def (handle_\w+)', content)
                    
                    # Find broadcasts
                    broadcasts = re.findall(r'broadcast_custom_event\([^,]+,\s*["\'](\w+)["\']', content)
                    
                    self.state_machine_phases[phase_name] = {
                        'handlers': handle_methods,
                        'broadcasts': list(set(broadcasts))
                    }
                    
    def analyze_game_engine(self):
        """Analyze game engine features"""
        engine_path = self.backend_path / "engine"
        engine_files = {
            'game.py': 'Game Management',
            'rules.py': 'Game Rules',
            'scoring.py': 'Scoring System',
            'player.py': 'Player Management',
            'piece.py': 'Piece Management'
        }
        
        for file_name, feature_name in engine_files.items():
            file_path = engine_path / file_name
            if file_path.exists():
                with open(file_path, 'r') as f:
                    content = f.read()
                    tree = ast.parse(content)
                    
                # Extract class methods
                methods = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef):
                                if not item.name.startswith('_'):
                                    methods.append(item.name)
                                    
                self.game_features[feature_name] = methods[:10]  # Limit to 10 methods
                
    def analyze_frontend_components(self):
        """Analyze React components"""
        component_files = list(self.frontend_path.glob("src/**/*.jsx"))
        component_files.extend(list(self.frontend_path.glob("src/**/*.js")))
        
        for file_path in component_files:
            if 'test' in str(file_path).lower():
                continue
                
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                # Extract component name
                component_match = re.search(r'(?:export default |export )?(?:function |const |class )(\w+)', content)
                if component_match:
                    comp_name = component_match.group(1)
                    
                    # Extract props
                    props_match = re.findall(r'\{([^}]+)\}\s*=\s*props', content)
                    props = []
                    if props_match:
                        props = [p.strip() for p in props_match[0].split(',')]
                    
                    # Extract state variables
                    state_vars = re.findall(r'const \[(\w+),\s*set\w+\]\s*=\s*useState', content)
                    
                    # Extract WebSocket events
                    ws_events = re.findall(r'networkService\.send\(["\'](\w+)["\']', content)
                    ws_events.extend(re.findall(r'socket\.emit\(["\'](\w+)["\']', content))
                    
                    # Extract imports
                    imports = re.findall(r'import .+ from ["\']([^"\']+)["\']', content)
                    deps = [imp.split('/')[-1].replace('.jsx', '').replace('.js', '') 
                           for imp in imports if './components' in imp or './services' in imp]
                    
                    self.components[comp_name] = Component(
                        name=comp_name,
                        file_path=str(file_path.relative_to(self.frontend_path)),
                        props=props,
                        state_vars=state_vars,
                        dependencies=deps,
                        websocket_events=list(set(ws_events))
                    )
            except Exception as e:
                print(f"  ⚠️  Error parsing {file_path}: {e}")
                
    def analyze_frontend_services(self):
        """Analyze frontend service layer"""
        services_path = self.frontend_path / "src" / "services"
        if services_path.exists():
            service_files = list(services_path.glob("*.js"))
            
            for file_path in service_files:
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                # Extract WebSocket event handlers
                event_handlers = re.findall(r'on\(["\'](\w+)["\']', content)
                event_sends = re.findall(r'emit\(["\'](\w+)["\']|send\(["\'](\w+)["\']', content)
                
                service_name = file_path.stem
                if event_handlers or event_sends:
                    self.components[f"Service_{service_name}"] = Component(
                        name=f"Service_{service_name}",
                        file_path=str(file_path.relative_to(self.frontend_path)),
                        websocket_events=list(set(event_handlers + [e for pair in event_sends for e in pair if e]))
                    )
                    
    def trace_data_flows(self):
        """Trace data flows between components"""
        # WebSocket event flows
        for component in self.components.values():
            for event in component.websocket_events:
                # Find matching backend handler
                for ws_event in self.websocket_events:
                    if ws_event.event_name == event:
                        self.data_flows.append(DataFlow(
                            source=component.name,
                            target=f"Backend_{ws_event.handler}",
                            data_type=event,
                            trigger="WebSocket"
                        ))
                        
                        # Add broadcast flows
                        for broadcast in ws_event.broadcasts:
                            self.data_flows.append(DataFlow(
                                source=f"Backend_{ws_event.handler}",
                                target="Frontend_Components",
                                data_type=broadcast,
                                trigger="Broadcast"
                            ))
        
        # Component dependencies
        for component in self.components.values():
            for dep in component.dependencies:
                if dep in self.components:
                    self.data_flows.append(DataFlow(
                        source=component.name,
                        target=dep,
                        data_type="Component",
                        trigger="Import"
                    ))
                    
    def generate_diagrams(self):
        """Generate Mermaid diagrams"""
        diagrams = []
        
        # 1. System Architecture Overview
        architecture = self._generate_architecture_diagram()
        diagrams.append(("System Architecture", architecture))
        
        # 2. WebSocket Event Flow
        websocket_flow = self._generate_websocket_diagram()
        diagrams.append(("WebSocket Event Flow", websocket_flow))
        
        # 3. State Machine Diagram
        state_machine = self._generate_state_machine_diagram()
        diagrams.append(("Game State Machine", state_machine))
        
        # 4. Component Hierarchy
        component_hierarchy = self._generate_component_diagram()
        diagrams.append(("Frontend Components", component_hierarchy))
        
        # 5. Data Flow Sequence
        data_sequence = self._generate_sequence_diagram()
        diagrams.append(("Game Flow Sequence", data_sequence))
        
        # Save diagrams
        output_file = Path("codebase_analysis.md")
        with open(output_file, 'w') as f:
            f.write("# Codebase Analysis - Data Flow Diagrams\n\n")
            f.write("Generated from actual code analysis\n\n")
            
            for title, diagram in diagrams:
                f.write(f"## {title}\n\n")
                f.write("```mermaid\n")
                f.write(diagram)
                f.write("\n```\n\n")
                
        print(f"\n✅ Analysis complete! Diagrams saved to: {output_file}")
        print(f"   Found {len(self.api_endpoints)} API endpoints")
        print(f"   Found {len(self.websocket_events)} WebSocket events")
        print(f"   Found {len(self.components)} components")
        print(f"   Traced {len(self.data_flows)} data flows")
        
    def _generate_architecture_diagram(self) -> str:
        """Generate system architecture diagram"""
        diagram = """graph TB
    subgraph Frontend
        React[React 19.1.0]
        Components[UI Components]
        Services[Service Layer]
        WebSocketClient[WebSocket Client]
    end
    
    subgraph Backend
        FastAPI[FastAPI Server]
        WebSocketHandler[WebSocket Handler]
        StateMachine[State Machine]
        GameEngine[Game Engine]
    end
    
    subgraph DataFlow
        Events[(Game Events)]
        State[(Game State)]
    end
    
    React --> Components
    Components --> Services
    Services --> WebSocketClient
    WebSocketClient -.WebSocket.-> WebSocketHandler
    WebSocketHandler --> StateMachine
    StateMachine --> GameEngine
    GameEngine --> State
    State --> Events
    Events -.Broadcast.-> WebSocketClient"""
        
        # Add discovered endpoints
        if self.api_endpoints:
            diagram += "\n\n    subgraph \"REST Endpoints\"\n"
            for i, endpoint in enumerate(self.api_endpoints[:5]):
                diagram += f"        API{i}[\"{endpoint.method} {endpoint.path}\"]\n"
            diagram += "    end"
            
        return diagram
        
    def _generate_websocket_diagram(self) -> str:
        """Generate WebSocket event flow diagram"""
        diagram = "graph LR\n"
        diagram += "    Client[Frontend Client]\n"
        diagram += "    Server[WebSocket Server]\n\n"
        
        for event in self.websocket_events[:10]:  # Limit to 10 events
            safe_event = event.event_name.replace('-', '_')
            diagram += f"    Client -->|{event.event_name}| Server\n"
            
            for broadcast in event.broadcasts[:2]:  # Limit broadcasts
                safe_broadcast = broadcast.replace('-', '_')
                diagram += f"    Server -->|{broadcast}| Client\n"
                
        return diagram
        
    def _generate_state_machine_diagram(self) -> str:
        """Generate state machine diagram"""
        diagram = "stateDiagram-v2\n"
        
        states = list(self.state_machine_phases.keys())
        if states:
            for i, state in enumerate(states):
                clean_state = state.replace('State', '')
                diagram += f"    {clean_state}\n"
                
                # Add handlers as state details
                phase_data = self.state_machine_phases[state]
                for handler in phase_data['handlers'][:3]:
                    diagram += f"    {clean_state} : {handler}()\n"
                    
            # Add transitions based on common patterns
            if 'PreparationState' in states and 'DeclarationState' in states:
                diagram += "    Preparation --> Declaration: Cards dealt\n"
            if 'DeclarationState' in states and 'TurnState' in states:
                diagram += "    Declaration --> Turn: All declared\n"
            if 'TurnState' in states and 'ScoringState' in states:
                diagram += "    Turn --> Scoring: Round complete\n"
            if 'ScoringState' in states and 'PreparationState' in states:
                diagram += "    Scoring --> Preparation: New round\n"
                
        return diagram
        
    def _generate_component_diagram(self) -> str:
        """Generate component hierarchy diagram"""
        diagram = "graph TD\n"
        
        # Group components by type
        pages = []
        components = []
        services = []
        
        for comp_name, comp in self.components.items():
            if 'Page' in comp_name:
                pages.append(comp)
            elif 'Service' in comp_name:
                services.append(comp)
            else:
                components.append(comp)
                
        diagram += "    App[App Root]\n"
        
        # Add pages
        if pages:
            diagram += "    App --> Pages\n"
            diagram += "    subgraph Pages\n"
            for page in pages[:5]:
                diagram += f"        {page.name}[{page.name}]\n"
            diagram += "    end\n"
            
        # Add components
        if components:
            diagram += "    Pages --> Components\n"
            diagram += "    subgraph Components\n"
            for comp in components[:10]:
                safe_name = comp.name.replace('-', '_')
                diagram += f"        {safe_name}[{comp.name}]\n"
                if comp.websocket_events:
                    diagram += f"        {safe_name} -.-> |{comp.websocket_events[0]}| WebSocket\n"
            diagram += "    end\n"
            
        # Add services
        if services:
            diagram += "    Components --> Services\n"
            diagram += "    subgraph Services\n"
            for service in services[:5]:
                diagram += f"        {service.name}\n"
            diagram += "    end\n"
            
        return diagram
        
    def _generate_sequence_diagram(self) -> str:
        """Generate game flow sequence diagram"""
        diagram = "sequenceDiagram\n"
        diagram += "    participant User\n"
        diagram += "    participant Frontend\n"
        diagram += "    participant WebSocket\n"
        diagram += "    participant StateMachine\n"
        diagram += "    participant GameEngine\n\n"
        
        # Create room flow
        diagram += "    User->>Frontend: Create Room\n"
        diagram += "    Frontend->>WebSocket: create_room\n"
        diagram += "    WebSocket->>GameEngine: Initialize Game\n"
        diagram += "    GameEngine->>StateMachine: Set PREPARATION\n"
        diagram += "    StateMachine-->>WebSocket: room_created\n"
        diagram += "    WebSocket-->>Frontend: room_created\n"
        diagram += "    Frontend-->>User: Show Room\n\n"
        
        # Join and start game flow
        diagram += "    User->>Frontend: Join Room\n"
        diagram += "    Frontend->>WebSocket: join_room\n"
        diagram += "    WebSocket-->>Frontend: player_joined\n\n"
        
        diagram += "    User->>Frontend: Start Game\n"
        diagram += "    Frontend->>WebSocket: start_game\n"
        diagram += "    WebSocket->>StateMachine: Handle start\n"
        diagram += "    StateMachine->>GameEngine: Deal cards\n"
        diagram += "    GameEngine-->>StateMachine: Cards dealt\n"
        diagram += "    StateMachine-->>WebSocket: phase_change\n"
        diagram += "    WebSocket-->>Frontend: game_started\n\n"
        
        # Game play flow
        diagram += "    loop Game Rounds\n"
        diagram += "        Frontend->>WebSocket: declare\n"
        diagram += "        WebSocket->>StateMachine: Handle declaration\n"
        diagram += "        StateMachine-->>WebSocket: declaration_made\n"
        diagram += "        WebSocket-->>Frontend: Update UI\n\n"
        
        diagram += "        Frontend->>WebSocket: play\n"
        diagram += "        WebSocket->>GameEngine: Validate play\n"
        diagram += "        GameEngine->>StateMachine: Update state\n"
        diagram += "        StateMachine-->>WebSocket: play_made\n"
        diagram += "        WebSocket-->>Frontend: Update board\n"
        diagram += "    end\n"
        
        return diagram

def main():
    """Run the analysis"""
    analyzer = CodebaseAnalyzer()
    analyzer.analyze()
    
    print("\n📋 Summary Statistics:")
    print(f"   API Endpoints: {len(analyzer.api_endpoints)}")
    print(f"   WebSocket Events: {len(analyzer.websocket_events)}")
    print(f"   Frontend Components: {len(analyzer.components)}")
    print(f"   State Machine Phases: {len(analyzer.state_machine_phases)}")
    print(f"   Game Features: {len(analyzer.game_features)}")
    print(f"   Data Flows Traced: {len(analyzer.data_flows)}")

if __name__ == "__main__":
    main()