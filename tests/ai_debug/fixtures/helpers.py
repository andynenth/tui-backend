"""
Helper functions for AI Debug Mode tests
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.engine.piece import Piece
from backend.engine.player import Player
from backend.services.ai_logger import AILogger


def create_test_hand(piece_specs):
    """
    Create a test hand from piece specifications
    
    Args:
        piece_specs: List of tuples (name, color) or strings like "GENERAL_RED"
        
    Returns:
        List of Piece objects
    """
    hand = []
    for spec in piece_specs:
        if isinstance(spec, str):
            # Direct string format like "GENERAL_RED"
            hand.append(Piece(spec))
        elif isinstance(spec, tuple) and len(spec) == 2:
            # Use (name, color) tuple to create "NAME_COLOR" string
            name, color = spec
            kind = f"{name}_{color}"
            hand.append(Piece(kind))
    return hand


def create_test_player(name, hand_specs=None, declared=0, captured_piles=0):
    """
    Create a test player with specified attributes
    
    Args:
        name: Player name
        hand_specs: List of piece specifications for hand
        declared: Declaration value
        captured_piles: Number of piles captured
        
    Returns:
        Player object
    """
    player = Player(name, is_bot=True)
    
    if hand_specs:
        player.hand = create_test_hand(hand_specs)
        
    player.declared = declared
    player.captured_piles = captured_piles
    
    # Add bot-specific attributes
    player._bot_name = name
    player._bot_zero_streak = 0
    
    return player


def run_declaration_test(hand_specs, position=0, previous_declarations=None, 
                        must_declare_nonzero=False, expected_min=None, expected_max=None):
    """
    Run a declaration test with specified parameters
    
    Args:
        hand_specs: List of piece specifications
        position: Position in declaration order (0-3)
        previous_declarations: List of previous player declarations
        must_declare_nonzero: Whether zero declaration is forbidden
        expected_min: Minimum expected declaration value
        expected_max: Maximum expected declaration value
        
    Returns:
        Dict with test results
    """
    from backend.engine import ai
    
    hand = create_test_hand(hand_specs)
    previous_declarations = previous_declarations or []
    is_first_player = (position == 0)
    
    # Run AI declaration
    ai_logger = AILogger('summary', None)
    declaration = ai.choose_declare(
        hand=hand,
        is_first_player=is_first_player,
        position_in_order=position,
        previous_declarations=previous_declarations,
        must_declare_nonzero=must_declare_nonzero,
        verbose=False,
        ai_logger=ai_logger
    )
    
    # Check results
    result = {
        'declaration': declaration,
        'passed': True,
        'message': ''
    }
    
    if expected_min is not None and declaration < expected_min:
        result['passed'] = False
        result['message'] = f"Declaration {declaration} is below minimum {expected_min}"
        
    if expected_max is not None and declaration > expected_max:
        result['passed'] = False
        result['message'] = f"Declaration {declaration} is above maximum {expected_max}"
        
    if must_declare_nonzero and declaration == 0:
        result['passed'] = False
        result['message'] = "Declared 0 when must declare non-zero"
        
    return result


def run_turn_play_test(hand_specs, required_count=None, my_declared=0, my_captured=0,
                      expected_play_type=None, expected_piece_count=None):
    """
    Run a turn play test with specified parameters
    
    Args:
        hand_specs: List of piece specifications
        required_count: Required number of pieces to play
        my_declared: Player's declaration
        my_captured: Player's captured piles
        expected_play_type: Expected play type (e.g., "SINGLE", "PAIR")
        expected_piece_count: Expected number of pieces played
        
    Returns:
        Dict with test results
    """
    from backend.engine import ai
    
    hand = create_test_hand(hand_specs)
    
    # Run AI turn play
    selected = ai.choose_best_play(
        hand=hand,
        required_count=required_count,
        verbose=False
    )
    
    # Get play type
    from backend.engine.rules import get_play_type
    play_type = get_play_type(selected) if selected else None
    
    # Check results
    result = {
        'selected_play': [f"{p.name}_{p.color}" for p in selected],
        'play_type': play_type,
        'piece_count': len(selected),
        'passed': True,
        'message': ''
    }
    
    if expected_play_type and play_type != expected_play_type:
        result['passed'] = False
        result['message'] = f"Expected {expected_play_type} but got {play_type}"
        
    if expected_piece_count and len(selected) != expected_piece_count:
        result['passed'] = False
        result['message'] = f"Expected {expected_piece_count} pieces but got {len(selected)}"
        
    return result