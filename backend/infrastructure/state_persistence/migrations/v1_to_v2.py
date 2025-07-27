"""
Migration from v1 to v2 state schema.

Example migration that adds player statistics tracking.
"""

from typing import Dict, Any
import logging

from ..versioning import StateMigration
from ..abstractions import StateVersion


logger = logging.getLogger(__name__)


class V1ToV2Migration(StateMigration):
    """
    Migrates state from v1 to v2.
    
    Changes:
    - Adds player_stats field to track game statistics
    - Restructures state_data for better organization
    """
    
    @property
    def from_version(self) -> StateVersion:
        """Source version."""
        return StateVersion(1, 0, 0)
    
    @property
    def to_version(self) -> StateVersion:
        """Target version."""
        return StateVersion(2, 0, 0)
    
    async def migrate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate state to v2."""
        logger.info("Migrating state from v1 to v2")
        
        # Copy state
        new_state = state.copy()
        
        # Ensure state_data exists
        if 'state_data' not in new_state:
            new_state['state_data'] = {}
        
        # Add player statistics if not present
        if 'player_stats' not in new_state['state_data']:
            new_state['state_data']['player_stats'] = {}
            
            # Initialize stats for each player
            if 'players' in new_state['state_data']:
                for player_id in new_state['state_data']['players']:
                    new_state['state_data']['player_stats'][player_id] = {
                        'games_played': 0,
                        'games_won': 0,
                        'total_score': 0,
                        'highest_score': 0,
                        'average_score': 0.0
                    }
        
        # Add version info
        new_state['_version'] = {
            'version': '2.0.0',
            'migrated_from': '1.0.0',
            'migration_date': None  # Will be set by versioning system
        }
        
        return new_state
    
    async def rollback(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Rollback migration."""
        logger.info("Rolling back migration from v2 to v1")
        
        # Copy state
        old_state = state.copy()
        
        # Remove v2 additions
        if 'state_data' in old_state and 'player_stats' in old_state['state_data']:
            del old_state['state_data']['player_stats']
        
        # Update version info
        if '_version' in old_state:
            old_state['_version'] = {
                'version': '1.0.0',
                'rolled_back_from': '2.0.0'
            }
        
        return old_state