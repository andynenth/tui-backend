# backend/api/controllers/GameController.py

from .BaseController import BaseController
from .PreparationController import PreparationController
from backend.socket_manager import broadcast
from backend.shared_instances import shared_room_manager
import asyncio
import logging

# Store active controllers globally
active_game_controllers = {}

class GameController(BaseController):
    """
    Minimal game controller - just handles preparation phase for now
    """
    
    def __init__(self, room_id: str):
        super().__init__(room_id)
        self.preparation_controller = None
        self.game_data = {}
        
    async def _validate_prerequisites(self):
        """Check room and game exist"""
        room = shared_room_manager.get_room(self.room_id)
        if not room or not room.game:
            raise ValueError(f"No game found for room {self.room_id}")
            
    async def _initialize_state(self):
        """Create preparation controller"""
        self.preparation_controller = PreparationController(self.room_id)
        
    async def _setup_event_handlers(self):
        """No handlers needed for main controller"""
        pass
        
    async def start_game(self, initial_data):
        """Start the game"""
        self.game_data = initial_data
        self.logger.info(f"🎮 Starting game controller for room {self.room_id}")
        
        # Initialize self
        success = await self.start()
        if not success:
            self.logger.error("Failed to start GameController")
            return False
            
        # Start preparation phase
        self.logger.info("📋 Starting preparation phase...")
        
        # Set callback for when preparation completes
        self.preparation_controller.on_complete = self.handle_preparation_complete
        
        # Start preparation
        success = await self.preparation_controller.start()
        if not success:
            self.logger.error("Failed to start preparation phase")
            return False
            
        return True
        
    async def handle_preparation_complete(self, next_phase: str, data: dict):
        """Handle preparation phase completion"""
        self.logger.info(f"✅ Preparation complete! Next phase would be: {next_phase}")
        
        # For now, just log it
        # Later we'll add other phases here
        await broadcast(self.room_id, {
            'type': 'game_message',
            'data': {
                'message': f'Preparation complete! {data.get("starter")} will start.',
                'phase': 'preparation_complete'
            }
        })

# Helper function to get controller
def get_game_controller(room_id: str) -> GameController:
    """Get the game controller for a room"""
    return active_game_controllers.get(room_id)