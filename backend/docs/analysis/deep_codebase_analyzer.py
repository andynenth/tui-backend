#!/usr/bin/env python3
"""
Deep Codebase Analyzer - Enhanced version with actual code tracing
Performs deep analysis of both backend and frontend to extract real data flows
"""

import ast
import json
import re
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict

@dataclass
class APIRoute:
    path: str
    method: str
    handler: str
    file: str
    params: List[str] = field(default_factory=list)
    returns: List[str] = field(default_factory=list)
    calls: List[str] = field(default_factory=list)

@dataclass
class WebSocketHandler:
    event: str
    handler: str
    file: str
    receives: Dict = field(default_factory=dict)
    broadcasts: List[str] = field(default_factory=list)
    state_changes: List[str] = field(default_factory=list)

@dataclass
class ReactComponent:
    name: str
    file: str
    type: str  # 'page', 'component', 'phase', 'service'
    props: List[str] = field(default_factory=list)
    state: List[str] = field(default_factory=list)
    hooks: List[str] = field(default_factory=list)
    events: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    api_calls: List[str] = field(default_factory=list)

@dataclass
class GamePhase:
    name: str
    handlers: List[str]
    transitions: List[str]
    broadcasts: List[str]
    state_updates: List[str]

@dataclass
class DataFlow:
    source: str
    target: str
    data: str
    type: str  # 'websocket', 'api', 'component', 'state', 'broadcast'
    details: str = ""

class DeepCodebaseAnalyzer:
    def __init__(self):
        self.backend_path = Path(".")
        self.frontend_path = Path("../frontend")
        
        # Analysis results
        self.api_routes: List[APIRoute] = []
        self.websocket_handlers: Dict[str, WebSocketHandler] = {}
        self.react_components: Dict[str, ReactComponent] = {}
        self.game_phases: Dict[str, GamePhase] = {}
        self.data_flows: List[DataFlow] = []
        self.game_features: Dict[str, List[str]] = {}
        
        # WebSocket event mappings
        self.ws_event_mapping = {}
        self.broadcast_listeners = defaultdict(list)
        
    def analyze(self):
        """Run complete deep analysis"""
        print("🔬 Starting deep codebase analysis...")
        
        # Backend analysis
        print("\n📊 Analyzing backend architecture...")
        self.analyze_api_routes()
        self.analyze_websocket_system()
        self.analyze_state_machine_deep()
        self.analyze_game_engine_deep()
        
        # Frontend analysis  
        print("\n📊 Analyzing frontend architecture...")
        self.analyze_react_components()
        self.analyze_frontend_network()
        self.analyze_frontend_state_management()
        
        # Trace data flows
        print("\n🔄 Tracing data flows...")
        self.trace_websocket_flows()
        self.trace_component_flows()
        self.trace_state_flows()
        
        # Generate comprehensive diagrams
        print("\n📈 Generating comprehensive diagrams...")
        self.generate_comprehensive_diagrams()
        
    def analyze_api_routes(self):
        """Deep analysis of API routes"""
        # Check main.py for routes
        main_file = self.backend_path / "main.py"
        if main_file.exists():
            with open(main_file, 'r') as f:
                content = f.read()
                
            # Find route includes
            includes = re.findall(r'app\.include_router\(([^)]+)\)', content)
            
            # Find direct routes
            routes = re.findall(r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']', content)
            for method, path in routes:
                self.api_routes.append(APIRoute(
                    path=path,
                    method=method.upper(),
                    handler="main",
                    file="main.py"
                ))
        
        # Analyze route files
        routes_path = self.backend_path / "api" / "routes"
        if routes_path.exists():
            for route_file in routes_path.glob("*.py"):
                self._analyze_route_file(route_file)
                
    def _analyze_route_file(self, file_path: Path):
        """Analyze a single route file"""
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Find router definition
        router_match = re.search(r'router\s*=\s*APIRouter\(prefix=["\']([^"\']*)["\']', content)
        prefix = router_match.group(1) if router_match else ""
        
        # Find all route decorators
        route_pattern = r'@router\.(get|post|put|delete|patch|websocket)\(["\']([^"\']+)["\']'
        routes = re.findall(route_pattern, content)
        
        for method, path in routes:
            full_path = prefix + path if prefix else path
            
            # Find the function after this decorator
            func_pattern = rf'@router\.{method}\(["\'][^"\']*["\'].*?\n+(?:.*?\n)*?(?:async )?def (\w+)'
            func_matches = re.findall(func_pattern, content, re.MULTILINE | re.DOTALL)
            
            handler = func_matches[0] if func_matches else "unknown"
            
            self.api_routes.append(APIRoute(
                path=full_path,
                method=method.upper(),
                handler=handler,
                file=str(file_path.relative_to(self.backend_path))
            ))
            
    def analyze_websocket_system(self):
        """Deep analysis of WebSocket system"""
        ws_file = self.backend_path / "api" / "routes" / "ws.py"
        if not ws_file.exists():
            return
            
        with open(ws_file, 'r') as f:
            content = f.read()
            
        # Find all event handlers
        event_handlers = re.findall(
            r'["\']action["\']\s*==\s*["\'](\w+)["\']|["\']event["\']\s*==\s*["\'](\w+)["\']',
            content
        )
        
        for event_tuple in event_handlers:
            event = event_tuple[0] or event_tuple[1]
            if not event:
                continue
                
            # Find broadcasts related to this event
            event_section = re.search(
                rf'["\']action["\']\s*==\s*["\']{event}["\'].*?(?=action["\']\\s*==|event["\']\\s*==|$)',
                content,
                re.DOTALL
            )
            
            if event_section:
                section = event_section.group(0)
                
                # Find broadcasts in this section
                broadcasts = re.findall(r'broadcast[^(]*\([^,]+,\s*["\'](\w+)["\']', section)
                
                # Find state updates
                state_updates = re.findall(r'update_phase_data\(([^)]+)\)', section)
                
                self.websocket_handlers[event] = WebSocketHandler(
                    event=event,
                    handler=f"handle_{event}",
                    file="api/routes/ws.py",
                    broadcasts=list(set(broadcasts)),
                    state_changes=state_updates[:3] if state_updates else []
                )
                
    def analyze_state_machine_deep(self):
        """Deep analysis of state machine"""
        state_path = self.backend_path / "engine" / "state_machine"
        if not state_path.exists():
            return
            
        # Analyze each state file
        for state_file in state_path.glob("*_state.py"):
            with open(state_file, 'r') as f:
                content = f.read()
                
            # Extract state class name
            class_match = re.search(r'class (\w+State)', content)
            if not class_match:
                continue
                
            state_name = class_match.group(1)
            
            # Find all handler methods
            handlers = re.findall(r'async def (handle_\w+)', content)
            
            # Find transitions (next phase changes)
            transitions = []
            transition_patterns = [
                r'self\.game\.phase\s*=\s*GamePhase\.(\w+)',
                r'transition_to\(["\'](\w+)["\']',
                r'next_phase\s*=\s*["\'](\w+)["\']'
            ]
            for pattern in transition_patterns:
                transitions.extend(re.findall(pattern, content))
            
            # Find broadcasts
            broadcasts = re.findall(r'broadcast_custom_event\([^,]+,\s*["\'](\w+)["\']', content)
            
            # Find state updates
            state_updates = re.findall(r'update_phase_data\(\{([^}]+)\}', content)
            
            self.game_phases[state_name] = GamePhase(
                name=state_name,
                handlers=handlers,
                transitions=list(set(transitions)),
                broadcasts=list(set(broadcasts)),
                state_updates=state_updates[:5] if state_updates else []
            )
            
    def analyze_game_engine_deep(self):
        """Deep analysis of game engine"""
        engine_path = self.backend_path / "engine"
        
        # Key engine files to analyze
        engine_files = {
            'game.py': [],
            'rules.py': [],
            'scoring.py': [],
            'player.py': [],
            'piece.py': []
        }
        
        for file_name in engine_files.keys():
            file_path = engine_path / file_name
            if not file_path.exists():
                continue
                
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Extract all public methods
            methods = re.findall(r'def ([a-z_]+[a-z0-9_]*)\(', content)
            
            # Extract class names
            classes = re.findall(r'class (\w+)', content)
            
            feature_name = file_name.replace('.py', '').title()
            self.game_features[feature_name] = {
                'classes': classes,
                'methods': [m for m in methods if not m.startswith('_')][:10]
            }
            
    def analyze_react_components(self):
        """Deep analysis of React components"""
        if not self.frontend_path.exists():
            print(f"  ⚠️  Frontend path not found: {self.frontend_path}")
            return
            
        # Scan all JavaScript/JSX files
        src_path = self.frontend_path / "src"
        if not src_path.exists():
            return
            
        # Categorize by directory
        categories = {
            'pages': 'page',
            'components': 'component',
            'phases': 'phase',
            'services': 'service',
            'hooks': 'hook'
        }
        
        for category, comp_type in categories.items():
            category_path = src_path / category
            if category_path.exists():
                for file_path in category_path.glob("**/*.jsx"):
                    self._analyze_react_file(file_path, comp_type)
                for file_path in category_path.glob("**/*.js"):
                    self._analyze_react_file(file_path, comp_type)
                    
    def _analyze_react_file(self, file_path: Path, comp_type: str):
        """Analyze a single React file"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Extract component name
            comp_patterns = [
                r'export default function (\w+)',
                r'export default (\w+)',
                r'function (\w+)\s*\(',
                r'const (\w+)\s*=.*?=>',
                r'class (\w+) extends'
            ]
            
            comp_name = None
            for pattern in comp_patterns:
                match = re.search(pattern, content)
                if match:
                    comp_name = match.group(1)
                    break
                    
            if not comp_name:
                return
                
            # Extract props
            props = []
            props_patterns = [
                r'\{([^}]+)\}\s*=\s*props',
                r'props\.(\w+)',
                r'function \w+\s*\(.*?\{([^}]+)\}'
            ]
            for pattern in props_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if ',' in match:
                        props.extend([p.strip() for p in match.split(',')])
                    else:
                        props.append(match)
                        
            # Extract state
            state_vars = re.findall(r'const \[(\w+),\s*set\w+\]\s*=\s*useState', content)
            
            # Extract hooks
            hooks = re.findall(r'use(\w+)\(', content)
            
            # Extract WebSocket events
            events = []
            event_patterns = [
                r'networkService\.send\(["\'](\w+)["\']',
                r'socket\.emit\(["\'](\w+)["\']',
                r'on\(["\'](\w+)["\']',
                r'addEventListener\(["\'](\w+)["\']'
            ]
            for pattern in event_patterns:
                events.extend(re.findall(pattern, content))
                
            # Extract imports
            imports = re.findall(r'import .+ from ["\']([^"\']+)["\']', content)
            
            # Store component
            self.react_components[comp_name] = ReactComponent(
                name=comp_name,
                file=str(file_path.relative_to(self.frontend_path)),
                type=comp_type,
                props=list(set(props))[:10],
                state=state_vars[:10],
                hooks=list(set(hooks))[:10],
                events=list(set(events))[:10],
                imports=[imp.split('/')[-1].replace('.jsx','').replace('.js','') 
                        for imp in imports if not imp.startswith('react')][:10]
            )
            
            # Track event listeners
            for event in events:
                self.broadcast_listeners[event].append(comp_name)
                
        except Exception as e:
            print(f"  ⚠️  Error analyzing {file_path}: {e}")
            
    def analyze_frontend_network(self):
        """Analyze frontend network layer"""
        network_path = self.frontend_path / "src" / "services"
        if not network_path.exists():
            network_path = self.frontend_path / "network"
            
        if network_path.exists():
            for file_path in network_path.glob("*.js"):
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                # Find WebSocket connection
                ws_patterns = [
                    r'new WebSocket\(["\']([^"\']+)["\']',
                    r'io\(["\']([^"\']+)["\']'
                ]
                
                for pattern in ws_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        print(f"  Found WebSocket connections: {matches}")
                        
                # Find event emitters
                emitters = re.findall(r'(?:emit|send)\(["\'](\w+)["\']', content)
                
                # Find event listeners  
                listeners = re.findall(r'(?:on|addEventListener)\(["\'](\w+)["\']', content)
                
                service_name = file_path.stem
                if emitters or listeners:
                    self.react_components[f"NetworkService_{service_name}"] = ReactComponent(
                        name=f"NetworkService_{service_name}",
                        file=str(file_path.relative_to(self.frontend_path)),
                        type='service',
                        events=list(set(emitters + listeners))[:20]
                    )
                    
    def analyze_frontend_state_management(self):
        """Analyze frontend state management (Redux, Context, etc.)"""
        # Check for Redux store
        store_patterns = [
            self.frontend_path / "src" / "store",
            self.frontend_path / "src" / "redux",
            self.frontend_path / "src" / "state"
        ]
        
        for store_path in store_patterns:
            if store_path.exists():
                for file_path in store_path.glob("**/*.js"):
                    with open(file_path, 'r') as f:
                        content = f.read()
                        
                    # Find actions
                    actions = re.findall(r'(?:const|export)\s+(\w+ACTION\w*)', content)
                    
                    # Find reducers
                    reducers = re.findall(r'function (\w+Reducer)', content)
                    
                    if actions or reducers:
                        print(f"  Found state management: {file_path.name}")
                        print(f"    Actions: {actions[:5]}")
                        print(f"    Reducers: {reducers[:5]}")
                        
    def trace_websocket_flows(self):
        """Trace WebSocket event flows between frontend and backend"""
        for event_name, handler in self.websocket_handlers.items():
            # Find frontend components that send this event
            for comp_name, comp in self.react_components.items():
                if event_name in comp.events:
                    self.data_flows.append(DataFlow(
                        source=comp_name,
                        target=f"Backend_{handler.handler}",
                        data=event_name,
                        type="websocket",
                        details="Frontend -> Backend"
                    ))
                    
            # Trace broadcasts back to frontend
            for broadcast in handler.broadcasts:
                # Find components listening to this broadcast
                if broadcast in self.broadcast_listeners:
                    for listener in self.broadcast_listeners[broadcast]:
                        self.data_flows.append(DataFlow(
                            source=f"Backend_{handler.handler}",
                            target=listener,
                            data=broadcast,
                            type="broadcast",
                            details="Backend -> Frontend"
                        ))
                        
    def trace_component_flows(self):
        """Trace data flows between components"""
        for comp_name, comp in self.react_components.items():
            # Trace imports (component dependencies)
            for imported in comp.imports:
                if imported in self.react_components:
                    self.data_flows.append(DataFlow(
                        source=comp_name,
                        target=imported,
                        data="props/state",
                        type="component",
                        details="Component dependency"
                    ))
                    
    def trace_state_flows(self):
        """Trace state machine flows"""
        for phase_name, phase in self.game_phases.items():
            # Trace phase transitions
            for transition in phase.transitions:
                target_phase = f"{transition}State"
                if target_phase in self.game_phases:
                    self.data_flows.append(DataFlow(
                        source=phase_name,
                        target=target_phase,
                        data="phase_transition",
                        type="state",
                        details="State machine transition"
                    ))
                    
            # Trace broadcasts from phases
            for broadcast in phase.broadcasts:
                self.data_flows.append(DataFlow(
                    source=phase_name,
                    target="Frontend",
                    data=broadcast,
                    type="broadcast",
                    details="Phase broadcast"
                ))
                
    def generate_comprehensive_diagrams(self):
        """Generate comprehensive Mermaid diagrams"""
        output = []
        
        # 1. Complete System Architecture
        output.append(("Complete System Architecture", self._gen_complete_architecture()))
        
        # 2. WebSocket Communication Map
        output.append(("WebSocket Communication Map", self._gen_websocket_map()))
        
        # 3. Frontend Component Hierarchy
        output.append(("Frontend Component Hierarchy", self._gen_component_hierarchy()))
        
        # 4. Backend State Machine
        output.append(("Backend State Machine", self._gen_state_machine()))
        
        # 5. Data Flow Diagram
        output.append(("Complete Data Flow", self._gen_data_flow()))
        
        # 6. API Endpoints Map
        output.append(("API Endpoints", self._gen_api_map()))
        
        # 7. Game Feature Map
        output.append(("Game Features", self._gen_feature_map()))
        
        # 8. Sequence Diagram
        output.append(("Game Play Sequence", self._gen_sequence_diagram()))
        
        # Save all diagrams
        with open("deep_analysis.md", 'w') as f:
            f.write("# Deep Codebase Analysis - Complete Data Flows\n\n")
            f.write(f"## Analysis Summary\n\n")
            f.write(f"- **API Routes**: {len(self.api_routes)}\n")
            f.write(f"- **WebSocket Events**: {len(self.websocket_handlers)}\n")
            f.write(f"- **React Components**: {len(self.react_components)}\n")
            f.write(f"- **Game Phases**: {len(self.game_phases)}\n")
            f.write(f"- **Data Flows**: {len(self.data_flows)}\n")
            f.write(f"- **Game Features**: {len(self.game_features)}\n\n")
            
            for title, diagram in output:
                f.write(f"## {title}\n\n")
                f.write("```mermaid\n")
                f.write(diagram)
                f.write("\n```\n\n")
                
        print(f"\n✅ Deep analysis complete! Results saved to: deep_analysis.md")
        
    def _gen_complete_architecture(self) -> str:
        """Generate complete architecture diagram"""
        diagram = """graph TB
    subgraph "Frontend Layer"
        Browser[Browser Client]
        React[React 19.1.0]
        Router[React Router]
        Pages[Page Components]
        Components[UI Components]
        Services[Service Layer]
        Network[Network Service]
    end
    
    subgraph "Communication Layer"
        WebSocket[WebSocket Connection]
        REST[REST API]
    end
    
    subgraph "Backend Layer"
        FastAPI[FastAPI Server]
        WSHandler[WebSocket Handler]
        APIRoutes[API Routes]
        Middleware[Middleware]
    end
    
    subgraph "Business Logic"
        StateMachine[State Machine]
        GameEngine[Game Engine]
        Rules[Game Rules]
        Scoring[Scoring System]
    end
    
    subgraph "Data Layer"
        GameState[(Game State)]
        Rooms[(Room Manager)]
        Players[(Player Data)]
    end
    
    Browser --> React
    React --> Router
    Router --> Pages
    Pages --> Components
    Components --> Services
    Services --> Network
    Network -.WebSocket.-> WebSocket
    Network -.HTTP.-> REST
    
    WebSocket --> WSHandler
    REST --> APIRoutes
    WSHandler --> StateMachine
    APIRoutes --> Middleware
    
    StateMachine --> GameEngine
    GameEngine --> Rules
    GameEngine --> Scoring
    
    StateMachine --> GameState
    WSHandler --> Rooms
    GameEngine --> Players"""
        
        return diagram
        
    def _gen_websocket_map(self) -> str:
        """Generate WebSocket communication map"""
        diagram = "graph LR\n"
        diagram += "    subgraph Frontend\n"
        diagram += "        FE[Frontend Client]\n"
        diagram += "    end\n\n"
        diagram += "    subgraph Backend\n"
        diagram += "        BE[Backend Server]\n"
        diagram += "    end\n\n"
        
        # Add all WebSocket events
        for event, handler in list(self.websocket_handlers.items())[:15]:
            diagram += f"    FE -->|{event}| BE\n"
            
            for broadcast in handler.broadcasts[:2]:
                diagram += f"    BE -->|{broadcast}| FE\n"
                
        return diagram
        
    def _gen_component_hierarchy(self) -> str:
        """Generate component hierarchy"""
        diagram = "graph TD\n"
        
        # Group components by type
        pages = [c for c in self.react_components.values() if c.type == 'page']
        components = [c for c in self.react_components.values() if c.type == 'component']
        phases = [c for c in self.react_components.values() if c.type == 'phase']
        services = [c for c in self.react_components.values() if c.type == 'service']
        
        diagram += "    App[App Root]\n\n"
        
        if pages:
            diagram += "    App --> Pages\n"
            diagram += "    subgraph Pages\n"
            for page in pages[:8]:
                safe_name = page.name.replace('-', '_')
                diagram += f"        {safe_name}[{page.name}]\n"
            diagram += "    end\n\n"
            
        if components:
            diagram += "    Pages --> UIComponents\n"
            diagram += "    subgraph UIComponents\n"
            for comp in components[:10]:
                safe_name = comp.name.replace('-', '_')
                diagram += f"        {safe_name}[{comp.name}]\n"
            diagram += "    end\n\n"
            
        if phases:
            diagram += "    UIComponents --> GamePhases\n"
            diagram += "    subgraph GamePhases\n"
            for phase in phases[:6]:
                safe_name = phase.name.replace('-', '_')
                diagram += f"        {safe_name}[{phase.name}]\n"
            diagram += "    end\n\n"
            
        if services:
            diagram += "    GamePhases --> Services\n"
            diagram += "    subgraph Services\n"
            for service in services[:5]:
                safe_name = service.name.replace('-', '_')
                diagram += f"        {safe_name}[{service.name}]\n"
            diagram += "    end\n"
            
        return diagram
        
    def _gen_state_machine(self) -> str:
        """Generate state machine diagram"""
        diagram = "stateDiagram-v2\n"
        diagram += "    [*] --> Waiting: Room Created\n\n"
        
        # Add all game phases
        for phase_name, phase in self.game_phases.items():
            clean_name = phase_name.replace('State', '')
            diagram += f"    state {clean_name} {{\n"
            
            # Add handlers as state details
            for handler in phase.handlers[:3]:
                diagram += f"        {clean_name} : {handler}()\n"
            diagram += "    }\n\n"
            
        # Add transitions
        if 'PreparationState' in self.game_phases:
            diagram += "    Waiting --> Preparation: Game Started\n"
            diagram += "    Preparation --> Declaration: Cards Dealt\n"
            
        if 'DeclarationState' in self.game_phases:
            diagram += "    Declaration --> Turn: All Declared\n"
            
        if 'TurnState' in self.game_phases:
            diagram += "    Turn --> Scoring: Round Complete\n"
            
        if 'ScoringState' in self.game_phases:
            diagram += "    Scoring --> Preparation: Next Round\n"
            diagram += "    Scoring --> [*]: Game Over\n"
            
        return diagram
        
    def _gen_data_flow(self) -> str:
        """Generate data flow diagram"""
        diagram = "graph TB\n"
        
        # Group flows by type
        ws_flows = [f for f in self.data_flows if f.type == 'websocket'][:10]
        broadcast_flows = [f for f in self.data_flows if f.type == 'broadcast'][:10]
        component_flows = [f for f in self.data_flows if f.type == 'component'][:10]
        
        # Add nodes
        nodes = set()
        for flow in ws_flows + broadcast_flows + component_flows:
            nodes.add(flow.source)
            nodes.add(flow.target)
            
        for node in list(nodes)[:20]:
            safe_node = node.replace('-', '_').replace(' ', '_')
            diagram += f"    {safe_node}[{node}]\n"
            
        diagram += "\n"
        
        # Add flows
        for flow in ws_flows:
            safe_source = flow.source.replace('-', '_').replace(' ', '_')
            safe_target = flow.target.replace('-', '_').replace(' ', '_')
            diagram += f"    {safe_source} -->|{flow.data}| {safe_target}\n"
            
        for flow in broadcast_flows:
            safe_source = flow.source.replace('-', '_').replace(' ', '_')
            safe_target = flow.target.replace('-', '_').replace(' ', '_')
            diagram += f"    {safe_source} -.->|{flow.data}| {safe_target}\n"
            
        return diagram
        
    def _gen_api_map(self) -> str:
        """Generate API endpoints map"""
        diagram = "graph LR\n"
        diagram += "    Client[Client]\n"
        diagram += "    Server[Server]\n\n"
        
        # Group by method
        methods = defaultdict(list)
        for route in self.api_routes:
            methods[route.method].append(route)
            
        for method, routes in methods.items():
            diagram += f"    subgraph {method}\n"
            for i, route in enumerate(routes[:5]):
                diagram += f"        {method}{i}[\"{route.path}\"]\n"
            diagram += "    end\n"
            diagram += f"    Client -->|{method}| {method}\n"
            diagram += f"    {method} --> Server\n\n"
            
        return diagram
        
    def _gen_feature_map(self) -> str:
        """Generate game feature map"""
        diagram = "graph TD\n"
        diagram += "    GameEngine[Game Engine]\n\n"
        
        for feature, data in self.game_features.items():
            safe_feature = feature.replace(' ', '_')
            diagram += f"    GameEngine --> {safe_feature}[{feature}]\n"
            
            if isinstance(data, dict):
                # Add classes
                for cls in data.get('classes', [])[:3]:
                    diagram += f"    {safe_feature} --> {cls}[{cls}]\n"
                    
                # Add key methods
                for method in data.get('methods', [])[:3]:
                    safe_method = method.replace('_', '')
                    diagram += f"    {safe_feature} --> {safe_method}[{method}]\n"
                    
        return diagram
        
    def _gen_sequence_diagram(self) -> str:
        """Generate detailed sequence diagram"""
        diagram = """sequenceDiagram
    participant User
    participant Browser
    participant React
    participant NetworkService
    participant WebSocket
    participant FastAPI
    participant StateMachine
    participant GameEngine
    participant Database
    
    Note over User,Database: Room Creation Flow
    User->>Browser: Click Create Room
    Browser->>React: Handle Click
    React->>NetworkService: createRoom()
    NetworkService->>WebSocket: send('create_room')
    WebSocket->>FastAPI: WebSocket Message
    FastAPI->>GameEngine: create_game()
    GameEngine->>Database: Store Game State
    Database-->>GameEngine: Game ID
    GameEngine-->>FastAPI: Game Created
    FastAPI-->>WebSocket: broadcast('room_created')
    WebSocket-->>NetworkService: Receive Event
    NetworkService-->>React: Update State
    React-->>Browser: Render Room
    Browser-->>User: Show Room Code
    
    Note over User,Database: Game Play Flow
    User->>Browser: Make Move
    Browser->>React: Handle Input
    React->>NetworkService: play(pieces)
    NetworkService->>WebSocket: send('play', data)
    WebSocket->>FastAPI: WebSocket Message
    FastAPI->>StateMachine: handle_play()
    StateMachine->>GameEngine: validate_play()
    GameEngine->>GameEngine: Apply Rules
    GameEngine-->>StateMachine: Play Valid
    StateMachine->>Database: Update State
    StateMachine-->>FastAPI: broadcast_changes()
    FastAPI-->>WebSocket: broadcast('play_made')
    WebSocket-->>NetworkService: Receive Update
    NetworkService-->>React: Update Game State
    React-->>Browser: Render Changes
    Browser-->>User: Show Updated Board"""
        
        return diagram

def main():
    analyzer = DeepCodebaseAnalyzer()
    analyzer.analyze()
    
    print("\n📊 Final Analysis Summary:")
    print(f"   API Routes: {len(analyzer.api_routes)}")
    print(f"   WebSocket Handlers: {len(analyzer.websocket_handlers)}")
    print(f"   React Components: {len(analyzer.react_components)}")
    print(f"   Game Phases: {len(analyzer.game_phases)}")
    print(f"   Data Flows: {len(analyzer.data_flows)}")
    print(f"   Game Features: {len(analyzer.game_features)}")
    
    # Print sample data flows
    if analyzer.data_flows:
        print("\n   Sample Data Flows:")
        for flow in analyzer.data_flows[:5]:
            print(f"     {flow.source} → {flow.target} [{flow.type}: {flow.data}]")

if __name__ == "__main__":
    main()