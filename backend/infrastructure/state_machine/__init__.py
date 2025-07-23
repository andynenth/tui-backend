# infrastructure/state_machine/__init__.py
"""
State machine infrastructure for game flow management.
"""

from .state_adapter import StateMachineAdapter, StateMachineRepository, StateTransitionResult

__all__ = [
    'StateMachineAdapter',
    'StateMachineRepository',
    'StateTransitionResult',
]